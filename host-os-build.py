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
from lib import log_helper
from lib import manager
from lib import repository

import pygit2

LOG = logging.getLogger(__name__)


def main(args):
    try:
        conf = config.get_config().CONF
    except OSError:
        print("Failed to parse settings")
        return 2

    log_helper.LogHelper(logfile=conf.get('default').get('log_file'),
                         verbose=conf.get('default').get('verbose'),
                         rotate_size=conf.get('default').get('log_size'))
    try:
        # setup versions directory
        path, dirname = os.path.split(
            conf.get('default').get('build_versions_repo_dir'))
        repository.Repo(
            dirname, conf.get('default').get('build_versions_repository_url'),
            path, conf.get('default').get('build_version'))

        conf['default']['packages'] = conf['default']['packages'] if (
            conf.get('default').get('packages')) else (
                config.discover_software())

    except exception.RepositoryError as e:
        LOG.exception("Script failed")
        return e.errno
    build_manager = manager.BuildManager()
    return build_manager()

if __name__ == '__main__':
    if os.getuid() is 0:
        print("Please, do not run this script as root, run "
              "setup_environment.py script in order to properly setup user and"
              " directory for build scripts")
        sys.exit(3)
    sys.exit(main(sys.argv[1:]))
