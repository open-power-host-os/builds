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
from lib import exception
from lib.utils import is_package_installed
from tools import build_iso
from tools import build_package
from tools import create_release_notes
from tools import setup_environment
from tools import update_versions_readme
from tools import upgrade_versions

INSUFFICIENT_PRIVILEGE_ERROR = 3
TOO_MUCH_PRIVILEGE_ERROR = 4
MISSING_PACKAGES_ERROR = 5
REQUIRED_PACKAGES_FILE_PATH = "rpm_requirements.txt"
LOG = logging.getLogger(__name__)
SUBCOMMANDS = {
    'build-package': build_package,
    'release-notes': create_release_notes,
    'upgrade-versions': upgrade_versions,
    'update-versions-readme': update_versions_readme,
    'set-env': setup_environment,
    'build-iso': build_iso,
}


if __name__ == '__main__':
    CONF = config.setup_default_config()
    subcommand = CONF.get('default').get('subcommand')

    # validate if all required packages are installed
    with open(REQUIRED_PACKAGES_FILE_PATH) as f:
        required_packages = f.read().splitlines()
    missing_packages = [p for p in required_packages
        if not is_package_installed(p)]
    if missing_packages:
        print("Following packages should be installed before running this "
              "script: %s" % ", ".join(missing_packages))
        sys.exit(MISSING_PACKAGES_ERROR)

    if os.getuid() is 0 and subcommand != 'set-env':
        print("Please, do not run this command as root, run "
              "host_os.py set-env --user <YOUR_USER_LOGIN> command in order to "
              "properly setup user and directory for build scripts")
        sys.exit(TOO_MUCH_PRIVILEGE_ERROR)

    if os.getuid() is not 0 and subcommand == 'set-env':
        print("The set-env command should be run with root privileges")
        sys.exit(INSUFFICIENT_PRIVILEGE_ERROR)

    return_code = 0
    try:
        SUBCOMMANDS[subcommand].run(CONF)
    except exception.BaseException as exc:
        LOG.exception("Command %s failed." % subcommand)
        return_code = exc.error_code
    sys.exit(return_code)
