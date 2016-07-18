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
import os
import logging
import sys

from lib import config
from lib import exception
from lib import log_helper
from lib import manager

import pygit2

LOG = logging.getLogger(__name__)


def setup_versions_repository(versions_git_url, dest, version):
    # Load if it is an existing git repo
    if os.path.exists(dest):
        try:
            versions_repo = pygit2.Repository(dest)
            LOG.info("Found versions repository!")

        except KeyError:
            raise exception.RepositoryError(
                message="Failed to setup Versions repository")
    else:
        LOG.info("Cloning into %s..." % dest)
        versions_repo = pygit2.clone_repository(versions_git_url,
                                                dest)

    LOG.info("Trying to check versions Tag: %s", version)
    try:
        versions_repo.checkout(version)
    except ValueError:
        pass
    finally:
        for remote in versions_repo.remotes:
            remote.fetch()
            LOG.info("Fetched changes for %s" % remote.name)
        # NOTE(maurosr): Get references and rearrange local master's HEAD
        # we are always **assuming a fastforward**
        remote = versions_repo.lookup_reference('refs/remotes/origin/master')
        master = versions_repo.lookup_reference('refs/heads/master')
        master.set_target(remote.target)
        versions_repo.head.set_target(master.target)
        LOG.info("Repository updated")
        try:
            # try again and then fail if can't find the reference
            versions_repo.checkout(version)
        except ValueError:
            raise exception.RepositoryError(message="Could not find reference "
                                            "%s on versions repo" % version)


def main(args):
    try:
        conf = config.get_config().CONF
    except OSError:
        print("Failed to parse settings")
        return 2

    log_helper.LogHelper(logfile=conf.get('default').get('log_file'),
                         verbose=conf.get('default').get('verbose'))
    try:
        version = conf.get('default').get('build_version')
        version = 'refs/heads/master' if version == 'latest' else (
            'refs/tags/' + version)
        setup_versions_repository(config.VERSIONS_REPOSITORY,
                                  config.COMPONENTS_DIRECTORY, version)

        # rediscovery software if it was not set
        conf['default']['packages'] = conf['default']['packages'] if (
            conf.get('default').get('packages')) else (
                config.discover_software())

    except exception.RepositoryError as e:
        return e.errno
    build_manager = manager.BuildManager()
    return build_manager()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
