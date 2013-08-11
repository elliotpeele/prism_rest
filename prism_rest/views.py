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

import logging

from prism_core.views import lift
from prism_core.views import BaseView
from prism_core.views import view_defaults

log = logging.getLogger('prism.rest.views')

@lift()
@view_defaults(renderer='prism_renderer', route_name='base_api')
class APIView(BaseView):
    """
    Super class for all API related views.
    """


@lift()
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
