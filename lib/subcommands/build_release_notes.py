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

from datetime import datetime
import logging
import os
import yaml

from lib import build_info
from lib import config
from lib import distro_utils
from lib import exception
from lib import packages_manager
from lib import repository
from lib import rpm_package
from lib.constants import REPOSITORIES_DIR
from lib.versions_repository import setup_versions_repository
from lib.versions_repository import read_version_and_milestone

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)

RELEASE_FILE_NAME_TEMPLATE = "{date}-release.markdown"
RELEASE_FILE_CONTENT_TEMPLATE = """\
---
{header_yaml}
---
"""
RELEASE_FILE_TITLE = "OpenPOWER Host OS release"
RELEASE_FILE_LAYOUT = "release"


def write_version_info(release_tag, file_path, versions_repo, packages):
    """
    Write release information to a file.
    It contains packages names, branches and commit IDs.
    """
    LOG.info("Creating release {release_tag} information".format(**locals()))

    release_file_info = {
        "title": RELEASE_FILE_TITLE,
        "layout": RELEASE_FILE_LAYOUT,
        "release_tag": release_tag,
        "builds_commit": str(repository.GitRepository(".").head.commit.hexsha),
        "versions_commit": str(versions_repo.head.commit.hexsha),
    }

    packages_info = build_info.query_pkgs_info(
        packages, ["name", "version", "release", "sources"], True)

    release_file_info["packages"] = [packages_info[k]
                                     for k in sorted(packages_info.keys())]

    LOG.info("Writing release {release_tag} information to file: {file_path}"
             .format(**locals()))
    with open(file_path, "w") as version_info_file:
        release_file_content = RELEASE_FILE_CONTENT_TEMPLATE.format(
            header_yaml=yaml.dump(release_file_info, default_flow_style=False))
        version_info_file.write(release_file_content)


def run(CONF):
    versions_repo = setup_versions_repository(CONF)

    version_milestone = read_version_and_milestone(versions_repo)

    packages_names = packages_manager.discover_packages()
    distro = distro_utils.get_distro(
        CONF.get('distro_name'),
        CONF.get('distro_version'),
        CONF.get('architecture'))
    release_notes_repo_url = CONF.get('release_notes_repo_url')
    release_notes_repo_branch = CONF.get('release_notes_repo_branch')
    commit_updates = CONF.get('commit_updates')
    push_updates = CONF.get('push_updates')
    push_repo_url = CONF.get('push_repo_url')
    push_repo_branch = CONF.get('push_repo_branch')
    updater_name = CONF.get('updater_name')
    updater_email = CONF.get('updater_email')

    REQUIRED_PARAMETERS = ["updater_name", "updater_email"]
    if push_updates:
        REQUIRED_PARAMETERS += ["push_repo_url", "push_repo_branch" ]
    for parameter in REQUIRED_PARAMETERS:
        if not CONF.get(parameter):
            raise exception.RequiredParameterMissing(parameter=parameter)

    LOG.info("Creating release notes with packages: {}".format(
        ", ".join(packages_names)))
    package_manager = packages_manager.PackagesManager(packages_names)
    package_manager.prepare_packages(packages_class=rpm_package.RPM_Package,
                                     download_source_code=False, distro=distro)

    repositories_dir_path = os.path.join(
        CONF.get('work_dir'), REPOSITORIES_DIR)
    website_repo = repository.get_git_repository(
        release_notes_repo_url, repositories_dir_path)
    website_repo.checkout(release_notes_repo_branch)

    WEBSITE_POSTS_DIR = "_posts"
    release_date = datetime.today().date().isoformat()
    release_tag = "{version}-{date}".format(
        version=version_milestone, date=release_date)
    release_file_name = RELEASE_FILE_NAME_TEMPLATE.format(date=release_date)
    release_file_path = os.path.join(
        website_repo.working_tree_dir, WEBSITE_POSTS_DIR, release_file_name)
    write_version_info(release_tag, release_file_path, versions_repo,
                       package_manager.packages)

    if commit_updates:
        commit_message = "Host OS release of {date}".format(date=release_date)
        website_repo.commit_changes(commit_message, updater_name, updater_email)
        if push_updates:
            website_repo.push_head_commits(push_repo_url, push_repo_branch)
