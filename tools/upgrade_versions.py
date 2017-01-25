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
import copy
import logging
import os
import re

import git

from lib import distro_utils
from lib import exception
from lib import packages_manager
from lib import repository
from lib import rpm_package
from lib.versions_repository import setup_versions_repository


LOG = logging.getLogger(__name__)
PACKAGES = [
    'SLOF',
    'ginger',
    'ginger-base',
    'kernel',
    'kimchi',
    'libservicelog',
    'libvirt',
    'libvpd',
    'lsvpd',
    'ppc64-diag',
    'qemu',
    'servicelog',
    'sos',
    'wok',
]

# prerelease strings supported as last element in the version regex
PRERELEASE_TERMS = ['rc']


def _sed_yaml_descriptor(yamlfile, old_commit, new_commit):
    lines = []
    with file(yamlfile, "r") as f:
        lines = f.readlines()
    with file(yamlfile, "w") as f:
        for line in lines:
            line = line.replace(old_commit, new_commit)
            f.write(line)


def _get_git_log(repo, since_id):
    """
    Get log of commit SHA1 and short messages since the ID provided
    (non-inclusive).
    """
    log = []
    for commit in repo.iter_commits():
        if commit.hexsha.startswith(since_id):
            break
        commit_message = commit.message.split('\n')[0]
        commit_message = commit_message.replace("'", "")
        commit_message = commit_message.replace("\"", "")
        log.append("%s %s" % (commit.hexsha, commit_message))

    return log


class Version(object):
    def __init__(self, pkg):
        self.pkg = pkg
        self._repo_prerelease = "%{nil}"
        self._repo_version = None

        LOG.info("%s: Current version: %s" % (self.pkg, self.pkg.version))

    def update(self, user_name, user_email):
        pkg = copy.deepcopy(self.pkg)
        pkg.sources[0]["git"]["commit_id"] = None
        pkg.download_files(recurse=False)
        newest_commit_id = pkg.sources[0]["git"]["repo"].head.commit.hexsha

        if newest_commit_id == self.pkg.sources[0]["git"]["commit_id"]:
            LOG.debug("%s: no changes.", self.pkg)
            return

        pkg.sources[0]["git"]["commit_id"] = newest_commit_id

        self._read_version_from_repo(
            pkg.sources[0]["git"]["repo"].working_tree_dir)

        change_log_header = None
        result = rpm_package.compare_versions(
            self.pkg.version, self._repo_version)
        if result < 0:
            pkg.spec_file.update_version(self._repo_version)
            change_log_header = "Version update"
        elif result > 0:
            raise exception.PackageError(
                "Current version (%s) is greater than repo version (%s)" %
                (self.pkg.version, self._repo_version))

        pkg.spec_file.update_prerelease_tag(self._repo_prerelease)
        self._bump_release(pkg, change_log_header, user_name, user_email)

    def _bump_release(self, pkg, change_log_header=None, user_name=None,
                      user_email=None):
        LOG.info("%s: Bumping release" % self.pkg)
        change_log_lines = []
        if change_log_header is not None:
            change_log_lines.append(change_log_header)

        old_commit_id = self.pkg.sources[0]["git"]["commit_id"]
        if old_commit_id:
            new_source = pkg.sources[0]["git"]
            new_commit_id = new_source["commit_id"]
            LOG.info("Updating package %s from %s to %s" % (
                self.pkg.name, old_commit_id, new_commit_id))
            change_log_lines += _get_git_log(
                new_source["repo"], old_commit_id)
            _sed_yaml_descriptor(
                self.pkg.package_file, old_commit_id, new_commit_id)

        if change_log_lines:
            assert user_name is not None
            assert user_email is not None
            pkg.spec_file.bump_release(change_log_lines, user_name, user_email)

    def _read_version_from_repo(self, repo_path):

        version_file_and_regexes = [
            self.pkg.version_file_regex,
            ('VERSION', r'(.*)'),
            ('%s.spec' % self.pkg, r'Version:\s*(.*)'),
        ]

        for _file, regex in version_file_and_regexes:
            try:
                version_file = os.path.join(repo_path, _file)
                LOG.debug("%s: Reading version from %s using '%s'" %
                          (self.pkg, version_file, regex))

                with open(version_file, 'r') as f:
                    match = re.search(regex, f.read())
                match_groups = list(match.groups())

                last_group = match_groups[-1]
                for term in PRERELEASE_TERMS:
                    if term in last_group:
                        # The spec file's Release field cannot contain dashes.
                        self._repo_prerelease = last_group.replace('-', '.')
                        match_groups.pop()
                        break

                self._repo_version = '.'.join(s.strip()
                                              for s in match_groups if s)
                LOG.info("%s: Repository version: %s" % (self.pkg,
                                                         self._repo_version))
                break
            except:
                pass
        else:
            msg = "%s: Could not find version in the source repo." % self.pkg
            if not self.pkg.version_file_regex:
                msg += (" Try specifying version file and regex in the .yaml "
                        "file.")

            LOG.error(msg)
            raise exception.PackageError(msg)


def push_new_versions(versions_repo, release_date, versions_repo_push_url,
                      versions_repo_push_branch, committer_name,
                      committer_email):
    """
    Push updated versions to the remote Git repository, using the
    system's configured git committer and SSH credentials.
    """
    LOG.info("Pushing packages versions updates on release dated {date}"
             .format(date=release_date))

    LOG.info("Creating remote for URL {}".format(versions_repo_push_url))
    VERSIONS_REPO_REMOTE = "push-remote"
    versions_repo.create_remote(VERSIONS_REPO_REMOTE, versions_repo_push_url)

    LOG.info("Adding files to repository index")
    versions_repo.index.add(["*"])

    LOG.info("Committing changes to local repository")
    commit_message = "Weekly build {date}".format(date=release_date)
    actor = git.Actor(committer_name, committer_email)
    versions_repo.index.commit(commit_message, author=actor, committer=actor)

    LOG.info("Pushing changes to remote repository")
    remote = versions_repo.remote(VERSIONS_REPO_REMOTE)
    refspec = "HEAD:refs/heads/{}".format(versions_repo_push_branch)
    push_info = remote.push(refspec=refspec)[0]
    LOG.debug("Push result: {}".format(push_info.summary))
    if git.PushInfo.ERROR & push_info.flags:
        raise repository.PushError(push_info)


def run(CONF):
    versions_repo = setup_versions_repository(CONF)
    packages_to_update = CONF.get('default').get('packages') or PACKAGES
    distro = distro_utils.get_distro(
        CONF.get('default').get('distro_name'),
        CONF.get('default').get('distro_version'),
        CONF.get('default').get('arch_and_endianness'))
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

    LOG.info("Checking for updates in packages versions: %s",
             ", ".join(packages_to_update))
    pm = packages_manager.PackagesManager(packages_to_update)
    pm.prepare_packages(packages_class=rpm_package.RPM_Package,
                        download_source_code=False, distro=distro)

    for pkg in pm.packages:
        pkg_version = Version(pkg)
        pkg_version.update(committer_name, committer_email)

    release_date = datetime.today().date().isoformat()
    push_new_versions(versions_repo, release_date, push_repo_url,
                      push_repo_branch, committer_name, committer_email)
