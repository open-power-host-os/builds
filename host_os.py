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
import logging
import os
import sys

from lib import config
from tools import build_package
from tools import create_release_notes

LOG = logging.getLogger(__name__)
SUBCOMMANDS = {
    'build-package': build_package,
    'release-notes': create_release_notes,
}


if __name__ == '__main__':
    CONF = config.setup_default_config()
    subcommand = CONF.get('default').get('subcommand')

    if os.getuid() is 0:
        print("Please, do not run this script as root, run "
              "setup_environment.py script in order to properly setup user and"
              " directory for build scripts")
        sys.exit(3)

    sys.exit(SUBCOMMANDS[subcommand].run(CONF))
