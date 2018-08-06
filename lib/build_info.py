# Copyright (C) IBM Corp. 2017.
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

import config
import json
import logging
import os
import pprint

from lib import repository
from lib.constants import BUILD_INFO_FILE_NAME
from lib.constants import PACKAGES_INFO_FILE_NAME

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)


class PackageInfo(object):
    def __init__(self, pkg):
        self.pkg = pkg

    def __getattr__(self, attr):
        if hasattr(self.pkg, attr):
            return getattr(self.pkg, attr)
        raise AttributeError("%r object has no attribute %r" %
                             (self.pkg.__class__, attr))

    @property
    def sources(self):
        sources = []
        for source in self.pkg.sources:
        # Dereference dict with repository type as key
            source = source.values()[0]
            sources.append({
                "src": source.get("src", ""),
                "branch": source.get("branch", ""),
                "commit_id": source.get("commit_id", ""),
            })
        return sources

    @property
    def rpms(self):
        return [os.path.basename(path)
                for path in self.pkg.cached_build_results]


def query_pkgs_info(packages, target_attrs, include_unbuilt=False):
    """
    Query information about packages

    Args:
        packages([Package]): packages from which to extract information
        target_attrs([str]): attributes to return for each package
        include_unbuilt(bool): whether to include in the query results
                               packages that were not built

    Returns:
        dict: packages information
    """

    packages_info = {pkg.name: {attr: getattr(PackageInfo(pkg), attr)
                                for attr in target_attrs}
                     for pkg in packages if pkg.built or include_unbuilt}

    LOG.debug("Query:\n%s\nResult:\n%s", sorted(target_attrs),
              pprint.pformat(packages_info, width=1))
    return packages_info




def write_build_info(build_manager, versions_repo):
    """
    Write build information to a file

    Args:
        build_manager(BuildManager): build manager instance
        versions_repo (GitRepository): versions repository instance
    """

    info_files = {}
    info_files[PACKAGES_INFO_FILE_NAME] = json.dumps(
        query_pkgs_info(build_manager.packages_manager.packages,
                        ['version', 'rpms', 'sources', 'release']),
        sort_keys=True, indent=4)

    info_files[BUILD_INFO_FILE_NAME] = json.dumps({
        "builds_repo_commit_id": str(repository.GitRepository(".").head.commit.hexsha),
        "versions_repo_commit_id": str(versions_repo.head.commit.hexsha),
        "timestamp": build_manager.timestamp,
    }, sort_keys=True, indent=4)

    for file_name, content in info_files.items():
        file_path = os.path.join(
            CONF.get('result_dir'), 'packages', 'latest', file_name)

        LOG.info("Writing information file: %s", file_path)

        with open(file_path, "w") as info_file:
            info_file.write(content)
