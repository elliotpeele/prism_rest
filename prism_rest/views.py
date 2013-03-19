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
Core module for storing common view super class.
"""

from pyramid.view import view_config
from pyramid.view import view_defaults as pyramid_view_defaults
from pyramid.httpexceptions import HTTPNotImplemented

from prism_core.util import AttrDict

class view_defaults(pyramid_view_defaults):
    def __call__(self, wrapped):
        defaults = {}
        for cls in reversed(wrapped.mro()):
            if hasattr(cls, '__view_defaults__'):
                defaults.update(cls.__view_defaults__)
        defaults.update(self.__dict__)
        wrapped.__view_defaults__ = defaults
        return wrapped


@view_defaults(route_name='base', permission='view')
class BaseView(object):
    """
    Base class for other other view classes to inherit from.
    """

    def __init__(self, request):
        self.request = request

        # move the match dict into a local attr dict
        self.match = AttrDict()
        if hasattr(self.request, 'matchdict'):
            self.match.update(self.request.matchdict)

        self.args = AttrDict()
        if self.request.query_string:
            self.args.update(dict(x.split('=', 2)
                for x in self.request.query_string.split('&')))

    def _call_method(self, method):
        if hasattr(self, method):
            func = getattr(self, method)
            return func()
        else:
            raise HTTPNotImplemented

    @view_config(request_method='POST')
    def post(self):
        return self._call_method('_post')

    @view_config(request_method='PUT')
    def put(self):
        return self._call_method('_put')

    @view_config(request_method='GET')
    def get(self):
        return self._call_method('_get')

    @view_config(request_method='DELETE')
    def delete(self):
        return self._call_method('_delete')


@view_defaults(route_name='base_view_auth', permission='authenticated')
class BaseAuthView(BaseView):
    """
    Super class for all authenticated views.
    """

    def __init__(self, request):
        BaseView.__init__(self, request)
        if self.request.user:
            user = self.request.user.users[0]
            self.user = self.c.users.getById(user.id)
        else:
            self.user = None


@view_defaults(renderer='prism_renderer', route_name='base_api')
class APIView(BaseView):
    """
    Super class for all API related views.
    """


@view_defaults(route_name='base_api_auth', permission='authenticated')
class APIAuthView(APIView):
    """
    Super class for all API views that should require authentication.
    """

    def __init__(self, request):
        BaseView.__init__(self, request)
        if self.request.user:
            user = self.request.user.users[0]
            self.user = self.c.users.getById(user.id)
        else:
            self.user = None
