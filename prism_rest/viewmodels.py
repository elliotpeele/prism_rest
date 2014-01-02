#
# Copyright (c) Elliot Peele <elliot@bentlogic.net>
#
# This program is distributed under the terms of the MIT License as found
# in a file called LICENSE. If it is not present, the license
# is always available at http://www.opensource.org/licenses/mit-license.php.
#
# This program is distributed in the hope that it will be useful, but
# without any warrenty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the MIT License for full details.
#

import re
import json
import types
import logging
import collections

from pyramid.compat import text_
from pyramid.httpexceptions import HTTPNotFound

from prism_core.util import AttrDict
from prism_rest.views import BaseView

from prism_rest.errors import ViewModelNotFoundError

log = logging.getLogger('prism.rest.viewmodels')

class _base(object):
    """
    Base class for requires and provides view model decorators.
    """

    _view_model_types = {}

    def __init__(self, *args):
        self._models = []
        if len(args) > 1 and isinstance(args[0], collections.Iterable):
            self._models = args
        else:
            if len(args) == 1:
                model_version = None
                model_name = args[0]
            else:
                model_version = args[0]
                model_name = args[1]
            self._models = [(model_version, model_name), ]

    def _resolve_model(self):
        return dict([ (x, self._view_model_types[x]) for x in self._models ])

    def __call__(self, func):
        modelClses = self._resolve_model()
        for modelCls in modelClses.itervalues():
            assert issubclass(modelCls, AbstractViewModel), ('%s decorator '
                'requires view models are subclasses of BaseViewModel'
                % self.__class__.__name__)

        def wrapper(inst, *args, **kwargs):
            assert isinstance(inst, BaseView), ('%s decorator only supported '
                'for instances of BaseView.' % self.__class__.__name__)

            data = None
            if getattr(inst.request, 'body', None):
                data = json.loads(
                    text_(inst.request.body, inst.request.charset),
                    object_hook=JSONDecoder(inst.request))

            model = None
            if not data or isinstance(data, dict):
                # If nothing matches, pick the first one?
                modelCls = sorted(modelClses.items())[0][1]
                model = modelCls(inst.request)
                if data:
                    model.deserialize(data)

            return self._wrap(model or data, func, inst, *args, **kwargs)

        return wrapper

    @classmethod
    def register_model(cls, mcls):
        log.info('registering view model: %s' % mcls.model_name)
        assert issubclass(mcls, AbstractViewModel), ('All view models must '
            'decend from BaseViewModel.')
        cls._view_model_types[(mcls.version, mcls.model_name)] = mcls
        return mcls

    @classmethod
    def get_model(cls, version, dbinst):
        models = {}
        for (v, n), m in cls._view_model_types.iteritems():
            name = m.dbmodelCls and m.dbmodelCls.__name__ or None
            models.setdefault(name, dict()).setdefault(v, m)

        name = dbinst.__class__.__name__
        if name not in models:
            raise ViewModelNotFoundError, ('No view model matching %s '
                'found' % name)

        return models.get(dbinst.__class__.__name__).get(version)

    @classmethod
    def get_model_by_name(cls, model_name, model_version):
        model = cls._view_model_types.get((model_version, model_name))
        if not model:
            raise ViewModelNotFoundError, ('No view model matching %s '
                'found' % model_name)
        return model

    def _wrap(self, model, func, inst, *args, **kwargs):
        raise NotImplementedError


get_model = _base.get_model
get_model_by_name = _base.get_model_by_name
register_model = _base.register_model


class view_requires(_base):
    """
    Decorator for specifying the input view model to use. This will parse a
    request into the specified model.

    NOTE: self passed to the wrapper is assumed to be a subclass of
          core.views.BaseView.
          model_name must be a subclass of BaseViewModel.
    """
    def _wrap(self, model, func, inst, *args, **kwargs):
        inst.request.input_model = model
        return func(inst, *args, **kwargs)


class view_provides(_base):
    """
    Decorator for specifying the output view model to use. This will parse the
    db model returned by the view into the specified view model.

    NOTE: self passed to the wrapper is assumed to be a subclass of
          core.views.BaseView.
          model_name must be a subclass of BaseViewModel.
    """
    def _wrap(self, model, func, inst, *args, **kwargs):
        res = func(inst, *args, **kwargs)
        return model.serialize(res)


class JSONDecoder(object):
    """
    Custom JSON decoder.
    """

    _decoders = {}

    def __init__(self, request):
        self.request = request

    def __call__(self, pairs):
        md = pairs.get('metadata')
        if md:
            model_name = md.get('type')
            model_version = md.get('version')

            modelCls = get_model_by_name(model_name, model_version)
            model = modelCls(self.request)
            return model.deserialize(pairs)

        data = AttrDict()
        for k, v in pairs.iteritems():
            decoder = self.get_decoder(v)
            if decoder:
                v = decoder.decode(v)
            data[k] = v

        return data

    @classmethod
    def get_decoder(cls, o):
        for regex, decoder in cls._decoders.iteritems():
            if isinstance(o, int):
                o = str(o)
            if not isinstance(o, types.StringTypes):
                continue
            if regex.match(o):
                return decoder

    @classmethod
    def register_decoder(cls, regexStr, decoder):
        cls._decoders[re.compile(regexStr)] = decoder


def register_decoder(matchStr):
    def deco(cls):
        JSONDecoder.register_decoder(matchStr, cls())
        return cls
    return deco


class AbstractViewModel(object):
    """
    Abstract class to define the interface that all view model implemenations
    should implement.
    """

    version = None
    model_name = None
    model_type = None
    dbmodelCls = None
    static_model = False

    id_fields = {}

    def __init__(self, request):
        self.request = request

    def _get_var_dict(self, dbmodel, args):
        if not isinstance(args, (list, tuple, set)):
            args = [ args, ]

        kw = {}
        for arg in args:
            if not arg:
                continue

            if hasattr(dbmodel, arg):
                kw[arg] = getattr(dbmodel, arg)

            if arg in self.request.matchdict:
                kw[arg] = self.request.matchdict.get(arg)

        return kw

    def _compute_id_fields(self, data):
        output = {}

        for field, dest in self.id_fields.iteritems():
            if len(dest) == 2:
                route_name, var_name = dest
            else:
                route_name = dest[0]
                var_name = None

            kw = self._get_var_dict(data, var_name)
            if field == 'id' and self.request.params:
                kw['_query'] = self.request.params

            output[field] = self.request.route_url(route_name, **kw)

        return output

    @staticmethod
    def _isSerialized(data):
        return isinstance(data, dict) and 'metadata' in data

    def serialize(self, data):
        raise NotImplementedError

    def deserialize(self, data):
        raise NotImplementedError


class BaseViewModel(AbstractViewModel):
    """
    Base model for all view models.

    fields - The list of attributes that should be copied from the
             database model or expected to be in the input model.
    id_fields - Fields that should be turned into urls.
    """

    fields = ()

    def serialize(self, data):
        if not self.static_model and not data:
            raise HTTPNotFound

        if self._isSerialized(data):
            return data

        output = AttrDict()
        for field in self.fields:
            if hasattr(data, field):
                output[field] = getattr(data, field)

        # Add metadata that should be in pretty much every model.
        if not self.static_model:
            output['metadata'] = AttrDict({
                'type': self.model_type or self.model_name,
                'version': self.version,
                'creation_date': getattr(data, 'creation_date', None),
                'modification_date': getattr(data, 'modification_date', None),
            })

        # Generate URLs for ID fields.
        output.update(self._compute_id_fields(data))

        return output

    def deserialize(self, data):
        for field in self.fields:
            if field in data:
                setattr(self, field, data.get(field))
            else:
                setattr(self, field, None)
        if 'metadata' in data:
            self.metadata = data['metadata']
        return self


class BaseCollectionViewModel(AbstractViewModel):
    """
    Base model class for all collection models.

    id_fields - Fields that should be turned into urls.
    """

    def serialize(self, data):
        if self._isSerialized(data):
            return data

        data, kw = data
        assert isinstance(data, collections.Iterable)

        output = {
            'metadata': {
                'type': self.model_type or self.model_name,
                'version': self.version,
                'count': len(data),
                'limit': len(data),
                'per_page': len(data),
                'num_pages': 1,
                'next_page': None,
                'previous_page': None,
                'start_index': len(data) and 0 or None,
                'end_index': len(data) and len(data) - 1 or None,
            },
            'data': data,
        }

        # Generate URLs for ID fields.
        output.update(self._compute_id_fields(AttrDict(kw)))

        return output

    def deserialize(self, data):
        self.metadata = data.get('metadata')
        self.data = data.get('data', [])
        return self
