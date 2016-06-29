# Copyright (C) IBM Corp. 2016.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

from lib import config
from lib import log_helper
from lib import manager


def main(args):
    try:
        conf = config.get_config().CONF
    except OSError:
        print("Failed to parse settings")
        return 2

    log_helper.LogHelper(logfile=conf.get('default').get('log_file'),
                         verbose=conf.get('default').get('verbose'))
    build_manager = manager.BuildManager()
    return build_manager()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
