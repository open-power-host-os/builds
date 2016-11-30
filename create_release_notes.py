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
import shutil
import sys
import urlparse

import git

from lib import config
from lib import distro_utils
from lib import exception
from lib import log_helper
from lib import packages_manager
from lib import repository
from lib import rpm_package
from lib import utils

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)

RELEASE_FILE_NAME_TEMPLATE = "{date}-release.markdown"
RELEASE_FILE_CONTENT_TEMPLATE = """\
---
title: OpenPOWER Host OS release
layout: release
packages:
{packages_info}
---
"""


class PackageReleaseInfo(object):

    def __init__(self, package):
        self.package = package

    def __str__(self):
        string = " -\n"
        PACKAGE_ATTRIBUTES = ["name", "clone_url", "version", "release",
                              "branch", "commit_id"]
        for attribute in PACKAGE_ATTRIBUTES:
            string += "   {name}: {value}\n".format(
                name=attribute, value=self.package.__getattribute__(attribute))
        return string


def write_version_info(release, file_path, packages):
    """
    Write release information to a file.
    It contains packages names, branches and commit IDs.
    """
    LOG.info("Writing release {release} information to file: {file_path}".format(
        **locals()))
    format_dict = {"release": release}

    packages_info = ""
    packages.sort()
    for package in packages:
        packages_info += str(PackageReleaseInfo(package))
    format_dict["packages_info"] = packages_info

    with open(file_path, "w") as version_info_file:
        version_info_file.write(RELEASE_FILE_CONTENT_TEMPLATE.format(
            **format_dict))

def publish_release_notes(
        release_date, release_file_source_path, website_pull_repo_url,
        website_pull_repo_branch, website_push_repo_url,
        website_push_repo_branch, committer_name, committer_email):
    """
    Publish release notes page to the Host OS website, using the
    system's configured git committer and SSH credentials.
    """
    LOG.info("Publishing release notes file {file_path} with date {date}"
             .format(file_path=release_file_source_path, date=release_date))

    WEBSITE_REPO_PUSH_REMOTE = "push-remote"
    WEBSITE_POSTS_DIR = "_posts"

    # Name is last path part without the file extension (".git")
    website_repo_path = urlparse.urlsplit(website_pull_repo_url).path
    website_repo_name = os.path.basename(website_repo_path).rsplit(".", 1)[0]
    website_repo = repository.get_git_repository(
        website_repo_name, website_pull_repo_url, os.getcwd())
    website_repo.checkout(website_pull_repo_branch)

    LOG.info("Copying file to repository directory")
    website_posts_dir_abs_path = os.path.join(
        website_repo.working_tree_dir, WEBSITE_POSTS_DIR)
    release_file_path_in_repo = os.path.join(
        website_posts_dir_abs_path, os.path.basename(release_file_source_path))
    if not os.path.isdir(website_posts_dir_abs_path):
        os.mkdir(website_posts_dir_abs_path, 0755)
    shutil.copy(release_file_source_path, release_file_path_in_repo)

    LOG.info("Adding file to repository index")
    website_repo.index.add([release_file_path_in_repo])

    LOG.info("Committing changes to local repository")
    commit_message = "Host OS release of {date}".format(date=release_date)
    actor = git.Actor(committer_name, committer_email)
    website_repo.index.commit(commit_message, author=actor, committer=actor)

    LOG.info("Pushing changes to remote repository")
    remote = website_repo.create_remote(
        WEBSITE_REPO_PUSH_REMOTE, website_push_repo_url)
    refspec = "HEAD:refs/heads/{}".format(website_push_repo_branch)
    push_info = remote.push(refspec=refspec)[0]
    LOG.debug("Push result: {}".format(push_info.summary))
    if git.PushInfo.ERROR & push_info.flags:
        raise repository.PushError(push_info)


def main(args):
    CONF = config.setup_default_config()
    utils.setup_versions_repository(CONF)

    packages_names = (CONF.get('default').get('packages')
                      or config.discover_packages())
    distro = distro_utils.get_distro(
        CONF.get('default').get('distro_name'),
        CONF.get('default').get('distro_version'),
        CONF.get('default').get('arch_and_endianness'))
    release_notes_repo_url = CONF.get('default').get('release_notes_repo_url')
    release_notes_repo_branch = CONF.get('default').get(
        'release_notes_repo_branch')
    push_repo_url = CONF.get('default').get('push_repo_url')
    push_repo_branch = CONF.get('default').get('push_repo_branch')
    committer_name = CONF.get('default').get('committer_name')
    committer_email = CONF.get('default').get('committer_email')

    REQUIRED_PARAMETERS = ["push_repo_url", "push_repo_branch",
                           "committer_name", "committer_email"]
    for parameter in REQUIRED_PARAMETERS:
        if CONF.get('default').get(parameter) is None:
            LOG.error("Parameter '%s' is required", parameter)
            return 1

    LOG.info("Creating release notes with packages: {}".format(
        ", ".join(packages_names)))
    package_manager = packages_manager.PackagesManager(packages_names)
    package_manager.prepare_packages(packages_class=rpm_package.RPM_Package,
                                     download_source_code=False, distro=distro)

    release_date = datetime.today().date().isoformat()
    release_file_name = RELEASE_FILE_NAME_TEMPLATE.format(date=release_date)
    write_version_info(release_date, release_file_name, package_manager.packages)
    publish_release_notes(
        release_date, release_file_name, release_notes_repo_url,
        release_notes_repo_branch, push_repo_url, push_repo_branch,
        committer_name, committer_email)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
