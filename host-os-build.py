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
from lib import distro_utils
from lib import exception
from lib import log_helper
from lib import manager
from lib import repository
from lib import utils

import pygit2

LOG = logging.getLogger(__name__)


def main(args):
    CONF = utils.setup_default_config()
    utils.setup_versions_repository(CONF)
    packages_to_build = (CONF.get('default').get('packages')
                         or config.discover_software())
    distro = distro_utils.get_distro(
        CONF.get('default').get('distro_name'),
        CONF.get('default').get('distro_version'),
        CONF.get('default').get('arch_and_endianness'))

    LOG.info("Building packages: %s", ", ".join(packages_to_build))
    build_manager = manager.BuildManager(packages_to_build, distro)
    try:
        build_manager()
    except exception.BaseException as exc:
        LOG.exception("Failed to build packages")
        return exc.errno
    else:
        return 0

if __name__ == '__main__':
    if os.getuid() is 0:
        print("Please, do not run this script as root, run "
              "setup_environment.py script in order to properly setup user and"
              " directory for build scripts")
        sys.exit(3)
    sys.exit(main(sys.argv[1:]))
