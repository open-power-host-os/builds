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

import json
import logging
import os
import yaml

from lib import config
from lib import exception
from lib import repository
from lib.constants import BUILD_INFO_FILE_NAME
from lib.constants import PACKAGES_INFO_FILE_NAME
from lib.constants import REPOSITORIES_DIR

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


def write_version_info(file_path, release_date, build_info, packages_info):
    """
    Write release information to a file.
    It contains packages names, branches and commit IDs.

    Args:
        file_path (str): path to the output release file
        release_date (str): date of the release
        build_info (dict): information about the build
        packages_info (dict): information about the packages
    """

    release_tag = "%s-%s" % (build_info['version'], release_date)

    desired_keys = ['sources', 'version', 'release']
    packages = [dict({k: v for k,v in pkg_info.items() if k in desired_keys},
                     name=pkg_name)
                for pkg_name, pkg_info in packages_info.items()]

    release_file_info = {
        "title": RELEASE_FILE_TITLE,
        "layout": RELEASE_FILE_LAYOUT,
        "release_tag": release_tag,
        "packages": packages,
        "builds_commit": build_info['builds_repo_commit_id'],
        "versions_commit": build_info['versions_repo_commit_id'],
    }

    LOG.info("Writing release {release_tag} information to file: {file_path}"
             .format(**locals()))
    with open(file_path, "w") as version_info_file:
        release_file_content = RELEASE_FILE_CONTENT_TEMPLATE.format(
            header_yaml=yaml.safe_dump(release_file_info, default_flow_style=False))
        version_info_file.write(release_file_content)


def run(CONF):

    release_notes_repo_url = CONF.get('release_notes_repo_url')
    release_notes_repo_branch = CONF.get('release_notes_repo_branch')
    commit_updates = CONF.get('commit_updates')
    push_updates = CONF.get('push_updates')
    push_repo_url = CONF.get('push_repo_url')
    push_repo_branch = CONF.get('push_repo_branch')
    updater_name = CONF.get('updater_name')
    updater_email = CONF.get('updater_email')
    info_files_dir = CONF.get('info_files_dir')

    required_parameters = []
    if commit_updates:
        required_parameters += ["updater_name", "updater_email"]
    if push_updates:
        required_parameters += ["push_repo_url", "push_repo_branch" ]
    for parameter in required_parameters:
        if not CONF.get(parameter):
            raise exception.RequiredParameterMissing(parameter=parameter)

    LOG.info("Creating release notes based on files at: {}".format(
        info_files_dir))

    repositories_dir_path = os.path.join(
        CONF.get('work_dir'), REPOSITORIES_DIR)
    website_repo = repository.get_git_repository(
        release_notes_repo_url, repositories_dir_path)
    website_repo.checkout(release_notes_repo_branch)

    WEBSITE_POSTS_DIR = "_posts"

    build_info_file = os.path.join(info_files_dir, BUILD_INFO_FILE_NAME)
    build_info = json.load(open(build_info_file))

    packages_info_file = os.path.join(info_files_dir, PACKAGES_INFO_FILE_NAME)
    packages_info = json.load(open(packages_info_file))

    # timestamp format is YYYY-MM-DDThh:mm:ss.xxx
    release_date = build_info['timestamp'].split('T')[0]
    release_file_name = RELEASE_FILE_NAME_TEMPLATE.format(date=release_date)
    release_file_path = os.path.join(
        website_repo.working_tree_dir, WEBSITE_POSTS_DIR, release_file_name)
    write_version_info(release_file_path, release_date, build_info, packages_info)

    if commit_updates:
        commit_message = "Host OS release of {date}".format(date=release_date)
        website_repo.commit_changes(commit_message, updater_name, updater_email)
        if push_updates:
            website_repo.push_head_commits(push_repo_url, push_repo_branch)

    LOG.info("Release notes built succesfully")
