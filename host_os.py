#!/usr/bin/python2
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
import grp
import logging
import os
import sys

from lib import config
from lib import exception
from lib.utils import create_directory
from lib.utils import is_package_installed
from tools import build_iso
from tools import build_packages
from tools import build_release_notes
from tools import update_versions
from tools import update_versions_in_readme

INSUFFICIENT_PRIVILEGE_ERROR = 3
TOO_MUCH_PRIVILEGE_ERROR = 4
MISSING_PACKAGES_ERROR = 5
REQUIRED_PACKAGES_FILE_PATH = "rpm_requirements.txt"
LOG = logging.getLogger(__name__)
SUBCOMMANDS = {
    'build-packages': build_packages,
    'build-release-notes': build_release_notes,
    'update-versions': update_versions,
    'update-versions-readme': update_versions_in_readme,
    'build-iso': build_iso,
}
MOCK_REQUIRED_SUBCOMANDS = [
    'build-package',
    'build-iso',
]


if __name__ == '__main__':
    CONF = config.setup_default_config()
    subcommand = CONF.get('common').get('subcommand')

    # validate if all required packages are installed
    with open(REQUIRED_PACKAGES_FILE_PATH) as f:
        required_packages = f.read().splitlines()
    missing_packages = [p for p in required_packages
        if not is_package_installed(p)]
    if missing_packages:
        print("Following packages should be installed before running this "
              "script: %s" % ", ".join(missing_packages))
        sys.exit(MISSING_PACKAGES_ERROR)

    if os.getuid() is 0:
        print("Please, do not run this command as root.")
        sys.exit(TOO_MUCH_PRIVILEGE_ERROR)

    if subcommand in MOCK_REQUIRED_SUBCOMANDS:
        mock_users = grp.getgrnam('mock').gr_mem
        user = os.environ['USER']
        if user not in mock_users:
            print("User must be in mock group, please run "
                  "'sudo usermod -a -G mock $(whoami)'")
            sys.exit(INSUFFICIENT_PRIVILEGE_ERROR)

    create_directory(CONF.get('common').get('work_dir'))

    return_code = 0
    try:
        SUBCOMMANDS[subcommand].run(CONF)
    except exception.BaseException as exc:
        LOG.exception("Command %s failed." % subcommand)
        return_code = exc.error_code
    sys.exit(return_code)
