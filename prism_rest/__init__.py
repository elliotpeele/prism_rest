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

from .renderer import APISerializer

from .views import APIView
from .views import APIAuthView

from .viewmodels import view_requires
from .viewmodels import view_provides
from .viewmodels import register_model

from .viewmodels import BaseViewModel
from .viewmodels import BaseCollectionViewModel

def includeme(config):
    config.add_renderer('prism_renderer', APISerializer)

    # FIXME: Figure out how to avoid the errors while loading these instead
    #        of having to define routes for them.
    config.add_route('base', '/base')
    config.add_route('base_view_auth', '/base/auth')
    config.add_route('base_api', '/base/api')
    config.add_route('base_api_auth', '/base/api_auth')

    config.include('prism_core')

    config.scan()
    return config
