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

import logging

from lib import distro_utils
from lib import exception
from lib.packages_manager import discover_packages
from lib.metapackage import update_metapackage
from lib.versions_repository import setup_versions_repository


LOG = logging.getLogger(__name__)


def run(CONF):
    versions_repo = setup_versions_repository(CONF)
    package_names = discover_packages()

    architecture = CONF.get('common').get('architecture')
    distro = distro_utils.get_distro(CONF.get('common').get('distro_name'),
                                     CONF.get('common').get('distro_version'),
                                     architecture)

    commit_updates = CONF.get('common').get('commit_updates')
    push_updates = CONF.get('common').get('push_updates')
    push_repo_url = CONF.get('common').get('push_repo_url')
    push_repo_branch = CONF.get('common').get('push_repo_branch')
    updater_name = CONF.get('common').get('updater_name')
    updater_email = CONF.get('common').get('updater_email')

    REQUIRED_PARAMETERS = ["updater_name", "updater_email"]
    if push_updates:
        REQUIRED_PARAMETERS += ["push_repo_url", "push_repo_branch"]
    for parameter in REQUIRED_PARAMETERS:
        if CONF.get('common').get(parameter) is None:
            raise exception.RequiredParameterMissing(parameter=parameter)

    METAPACKAGE_NAME = "open-power-host-os"
    package_names.remove(METAPACKAGE_NAME)
    update_metapackage(
        versions_repo, distro, METAPACKAGE_NAME, package_names,
        updater_name, updater_email)

    if commit_updates:
        commit_message = "Update {} dependencies".format(METAPACKAGE_NAME)
        versions_repo.commit_changes(
            commit_message, updater_name, updater_email)
        if push_updates:
            LOG.info("Pushing updated {} files".format(METAPACKAGE_NAME))
            versions_repo.push_head_commits(push_repo_url, push_repo_branch)
