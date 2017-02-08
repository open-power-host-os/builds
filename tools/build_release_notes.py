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

import git

from lib import config
from lib import distro_utils
from lib import exception
from lib import packages_manager
from lib import repository
from lib import rpm_package
from lib.versions_repository import setup_versions_repository
from lib.versions_repository import read_version_and_milestone

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)

RELEASE_FILE_NAME_TEMPLATE = "{date}-release.markdown"
RELEASE_FILE_CONTENT_TEMPLATE = """\
---
title: OpenPOWER Host OS release
release_tag: {release_tag}
layout: release
builds_commit: {builds_commit}
versions_commit: {versions_commit}
packages:
{packages_info}
---
"""


class PackageReleaseInfo(object):

    def __init__(self, package):
        self.package = package

    def __str__(self):
        string = " -\n"

        if self.package.sources and "git" in self.package.sources[0]:
            main_git_source = self.package.sources[0]["git"]
        else:
            main_git_source = None

        PACKAGE_ATTRIBUTES = [
            ("name", self.package.name),
            ("clone_url", main_git_source["src"] if main_git_source else ""),
            ("version", self.package.version),
            ("release", self.package.release),
            ("branch", main_git_source["branch"] if main_git_source else ""),
            ("commit_id",
             main_git_source["commit_id"] if main_git_source else ""),
        ]
        for name, value in PACKAGE_ATTRIBUTES:
            string += "   {name}: {value}\n".format(name=name, value=value)
        return string


def write_version_info(release_tag, file_path, versions_repo, packages):
    """
    Write release information to a file.
    It contains packages names, branches and commit IDs.
    """
    LOG.info("Creating release {release_tag} information".format(**locals()))

    format_dict = {"release_tag": release_tag}
    format_dict["builds_commit"] = (
        repository.GitRepository(".").head.commit.hexsha)
    format_dict["versions_commit"] = versions_repo.head.commit.hexsha

    packages_info = ""
    packages.sort()
    for package in packages:
        packages_info += str(PackageReleaseInfo(package))
    format_dict["packages_info"] = packages_info

    LOG.info("Writing release {release_tag} information to file: {file_path}".format(
        **locals()))
    with open(file_path, "w") as version_info_file:
        version_info_file.write(RELEASE_FILE_CONTENT_TEMPLATE.format(
            **format_dict))


def commit_release_notes(
        website_repo, release_date, updater_name, updater_email):
    """
    Commit release notes page to the Host OS website repository.

    Args:
        website_repo (GitRepository): Host OS website git repository
        release_date (str): release date
        updater_name (str): updater name
        updater_email (str): updater email
    """
    LOG.info("Adding files to repository index")
    website_repo.index.add(["*"])

    LOG.info("Committing changes to local repository")
    commit_message = "Host OS release of {date}".format(date=release_date)
    actor = git.Actor(updater_name, updater_email)
    website_repo.index.commit(commit_message, author=actor, committer=actor)


def push_website_head_commit(
        website_repo, website_push_repo_url, website_push_repo_branch):
    """
    Push Host OS website changes in local Git repository to the remote
    Git repository, using the system's configured SSH credentials.

    Args:
        website_repo (GitRepository): Host OS website git repository
        versions_repo_push_url (str): remote git repository URL
        versions_repo_push_branch (str): remote git repository branch

    Raises:
        repository.PushError: if push fails
    """
    WEBSITE_REPO_PUSH_REMOTE = "push-remote"

    LOG.info("Pushing changes to remote repository")
    remote = website_repo.create_remote(
        WEBSITE_REPO_PUSH_REMOTE, website_push_repo_url)
    refspec = "HEAD:refs/heads/{}".format(website_push_repo_branch)
    push_info = remote.push(refspec=refspec)[0]
    LOG.debug("Push result: {}".format(push_info.summary))
    if git.PushInfo.ERROR & push_info.flags:
        raise repository.PushError(push_info)


def run(CONF):
    versions_repo = setup_versions_repository(CONF)

    version_milestone = read_version_and_milestone(versions_repo)
    
    packages_names = (CONF.get('common').get('packages')
                      or packages_manager.discover_packages())
    distro = distro_utils.get_distro(
        CONF.get('common').get('distro_name'),
        CONF.get('common').get('distro_version'),
        CONF.get('common').get('arch_and_endianness'))
    release_notes_repo_url = CONF.get('release_notes').get('release_notes_repo_url')
    release_notes_repo_branch = CONF.get('release_notes').get('release_notes_repo_branch')
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

    LOG.info("Creating release notes with packages: {}".format(
        ", ".join(packages_names)))
    package_manager = packages_manager.PackagesManager(packages_names)
    package_manager.prepare_packages(packages_class=rpm_package.RPM_Package,
                                     download_source_code=False, distro=distro)

    website_repo = repository.get_git_repository(
        release_notes_repo_url, os.getcwd())
    website_repo.checkout(release_notes_repo_branch)

    WEBSITE_POSTS_DIR = "_posts"
    release_date = datetime.today().date().isoformat()
    release_tag = "{version}-{date}".format(
        version=version_milestone, date=release_date)
    release_file_name = RELEASE_FILE_NAME_TEMPLATE.format(date=release_date)
    release_file_path = os.path.join(
        website_repo.name, WEBSITE_POSTS_DIR, release_file_name)
    write_version_info(release_tag, release_file_path, versions_repo,
                       package_manager.packages)

    if commit_updates:
        commit_release_notes(
            website_repo, release_date, updater_name, updater_email)
        if push_updates:
            push_website_head_commit(
                website_repo, push_repo_url, push_repo_branch)
