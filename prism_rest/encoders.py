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

import datetime

from .renderer import register_encoder
from .viewmodels import register_decoder

class AbstractEncoder(object):
    """
    Base class for all other encoders to inherit from.
    """

    def encode(self, value):
        raise NotImplementedError

    def decode(self, value):
        raise NotImplementedError

@register_decoder(
    r'^(Sun|Mon|Tue|Wed|Thu|Fri|Sat)\ '
      '(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\ '
      '(0[1-9]|[12][0-9]|3[01])\ '
      '([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])\ '
      '(\d\d\d\d)$')
@register_encoder(datetime.datetime)
class DateTimeEncoder(AbstractEncoder):
    """
    Handle encoding datetime objects.
    """

    def encode(self, value):
        # FIXME: Using ctime for now, should probably find something better that
        #        supports timezones.
        return value.ctime()

    def decode(self, value):
        return datetime.datetime.strptime(value, '%a %b %d %H:%M:%S %Y')


@register_decoder(r'^(\d\d\d\d)\/(0[1-9]|1[012])\/(0[1-9]|[12][0-9]|3[01])$')
@register_encoder(datetime.date)
class DateEncoder(AbstractEncoder):
    """
    Handle encoding date objects.
    """

    def encode(self, value):
        return '%s/%s/%s' % (value.year, value.month, value.day)

    def decode(self, value):
        return datetime.datetime.strptime(value, '%Y/%m/%d')
