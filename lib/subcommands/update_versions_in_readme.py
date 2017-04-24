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

from lib import distro_utils
from lib import exception
from lib.packages_manager import discover_packages
from lib.readme import update_versions_in_readme
from lib.versions_repository import setup_versions_repository

LOG = logging.getLogger(__name__)


def run(CONF):
    versions_repo = setup_versions_repository(CONF)
    packages = discover_packages()

    architecture = CONF.get('common').get('architecture')
    distro = distro_utils.get_distro(CONF.get('common').get('distro_name'),
                                     CONF.get('common').get('distro_version'),
                                     architecture)

    commit_updates = CONF.get('common').get('commit_updates')
    push_updates = CONF.get('common').get('push_updates')
    push_repo_url = CONF.get('update_versions_readme').get('push_repo_url')
    push_repo_branch = CONF.get('update_versions_readme').get('push_repo_branch')
    updater_name = CONF.get('common').get('updater_name')
    updater_email = CONF.get('common').get('updater_email')

    REQUIRED_PARAMETERS = [("common", "updater_name"), ("common", "updater_email")]
    if push_updates:
        REQUIRED_PARAMETERS += [("update_versions_readme", "push_repo_url"),
                                ("update_versions_readme", "push_repo_branch")]
    for section, parameter in REQUIRED_PARAMETERS:
        if CONF.get(section).get(parameter) is None:
            raise exception.RequiredParameterMissing(parameter=parameter)

    update_versions_in_readme(versions_repo, distro, packages)

    if commit_updates:
        commit_message = "Update README versions table"
        versions_repo.commit_changes(
            commit_message, updater_name, updater_email)
        if push_updates:
            LOG.info("Pushing updated versions README")
            versions_repo.push_head_commits(push_repo_url, push_repo_branch)
