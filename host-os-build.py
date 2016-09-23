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

import pygit2

LOG = logging.getLogger(__name__)


def get_reference(repository, short_reference_string):
    """
    Get repository reference (branch, tag) based on a short reference
    suffix string.
    """
    prefixes = ["refs/tags", "refs/heads"]
    for remote in repository.remotes:
        prefixes.append(os.path.join("refs/remotes", remote.name))
    for prefix in prefixes:
        reference_string = os.path.join(prefix, short_reference_string)
        LOG.debug("Trying to get reference: %s", reference_string)
        try:
            return repository.lookup_reference(reference_string)
        except KeyError as exception:
            pass
    else:
       raise exception.RepositoryError(
           message="Reference not found in repository")

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

    version_reference = get_reference(versions_repo, version)
    LOG.info("Trying to check out versions' reference: %s",
             version_reference.name)
    try:
        for remote in versions_repo.remotes:
            remote.fetch()
            LOG.info("Fetched changes for %s" % remote.name)

        versions_repo.checkout(
            version_reference, strategy=pygit2.GIT_CHECKOUT_FORCE)
        versions_repo.reset(versions_repo.head.target, pygit2.GIT_RESET_HARD)
    except ValueError:
        LOG.error("Failed to check out %s", version_reference.name)
        raise exception.RepositoryError(
            message="Could not find reference %s on versions repo"
            % version_reference)


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
    if os.getuid() is 0:
        print("Please, do not run this script as root, run "
              "setup_environment.py script in order to properly setup user and"
              " directory for build scripts")
        sys.exit(3)
    sys.exit(main(sys.argv[1:]))
