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

"""
Implementation of a custom renderer that handles more complex objects when
rendering to JSON. Purhaps in the future this could be extended to support
other serialization formats based on request headers.
"""

import json
import logging

from prism_rest import viewmodels
from prism_rest.errors import ViewModelNotFoundError

log = logging.getLogger('prism.rest.renderer')

class APISerializer(object):
    def __init__(self, info):
        """
        Constructor: info will be an object having the
        following attributes: name (the renderer name), package
        (the package that was 'current' at the time the
        renderer was registered), type (the renderer type
        name), registry (the current application registry) and
        settings (the deployment settings dictionary).
        """

        # Since this is purely a serializer, we should never receive an info
        # object of any use.

    def __call__(self, value, system):
        """
        Call the renderer implementation with the value and the system value
        passed in as arguments and return the result (a string or unicode
        object). The value is the return value of a view. The system value is
        a dictionary containing available system values (e.g. view, context,
        and request).
        """

        # Set content type. (NOTE: This code is from pyramid/renderers.py)
        request = system.get('request')
        if request is not None:
            response = request.response
            if response.content_type == response.default_content_type:
                response.content_type = 'application/json'
        ## End copy

        model_version = None
        model_metadata = value.get('metadata')
        if model_metadata:
            model_version = model_metadata.get('version')

        return json.dumps(value, cls=JSONEncoder, indent=2,
            model_version=model_version, request=request)


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for handling more complex objects.
    """

    _encoders = {}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.model_version = kwargs.pop('model_version', None)
        json.JSONEncoder.__init__(self, *args, **kwargs)

    def default(self, o):
        """
        Handle encoding of complex objects.
        """

        encoder = self.get_encoder(o)
        if encoder:
            return encoder.encode(o)

        try:
            modelCls = viewmodels.get_model(self.model_version, o)
            model = modelCls(self.request)
            return model.serialize(o)
        except ViewModelNotFoundError:
            pass

        return json.JSONEncoder.default(self, o)

    @classmethod
    def get_encoder(cls, o):
        for t, encoder in cls._encoders.iteritems():
            if isinstance(o, t):
                return encoder
        return None

    @classmethod
    def register_encoder(cls, tcls, encoder):
        cls._encoders[tcls] = encoder


def register_encoder(type_cls):
    def deco(cls):
        JSONEncoder.register_encoder(type_cls, cls())
        return cls
    return deco
