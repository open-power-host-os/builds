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
import re

from lib import distro_utils
from lib import exception
from lib import packages_manager
from lib import rpm_package
from lib.utils import replace_str_in_file
from lib.packages_manager import discover_packages
from lib.versions_repository import setup_versions_repository
from lib.metapackage import update_metapackage

LOG = logging.getLogger(__name__)
PACKAGES = [
    'SLOF',
    'kernel',
    'libservicelog',
    'libvirt',
    'libvpd',
    'qemu',
    'servicelog',
]

# prerelease strings supported as last element in the version regex
PRERELEASE_TERMS = ['rc']


def _get_git_commit_log(repo, commit_id):
    """
    Get log of short SHA1 and short message for commit_id
    """
    SHORT_HEX_SHA_LENGTH = 7
    log = []
    commit = repo.commit(commit_id)
    commit_message = commit.message.split('\n')[0]
    commit_message = commit_message.replace("'", "")
    commit_message = commit_message.replace("\"", "")
    log.append("Updating to %s %s" % (
        commit.hexsha[0:SHORT_HEX_SHA_LENGTH], commit_message))

    return log

class Version(object):
    def __init__(self, pkg):
        self.pkg = pkg
        self._repo_prerelease = "%{nil}"
        self._repo_version = None

        LOG.info("%s: Current version: %s" % (self.pkg, self.pkg.version))

    def update(self, user_name, user_email):
        """
        Update the package's information, including version, release and git
        repository source.

        Args:
            user_name (str): name used when updating RPM specification files
                change logs
            user_email (str): email used when updating RPM specification files
                change logs

        Returns:
            bool: Whether the package has been updated
        """
        previous_commit_id = self.pkg.sources[0]["git"]["commit_id"]
        previous_version = self.pkg.version

        self.pkg.sources[0]["git"]["commit_id"] = None
        self.pkg.download_files(recurse=False)
        newest_commit_id = self.pkg.sources[0]["git"]["repo"].head.commit.hexsha
        self.pkg.sources[0]["git"]["commit_id"] = newest_commit_id

        if newest_commit_id == previous_commit_id:
            LOG.debug("%s: no changes.", self.pkg)
            return False

        self._read_version_from_repo(
            self.pkg.sources[0]["git"]["repo"].working_tree_dir)

        change_log_header = None
        result = rpm_package.compare_versions(
            previous_version, self._repo_version)
        if result < 0:
            self.pkg.spec_file.update_version(self._repo_version)
            change_log_header = "Version update"
        elif result > 0:
            raise exception.PackageError(
                "Current version (%s) is greater than repo version (%s)" %
                (previous_version, self._repo_version))

        self.pkg.spec_file.update_prerelease_tag(self._repo_prerelease)
        self._bump_release(previous_commit_id, change_log_header, user_name, user_email)

        return True

    def _bump_release(self, previous_commit_id, change_log_header=None,
                      user_name=None, user_email=None):
        """
        Bump package's spec file release number and mention it in the
        change log.

        Args:
            previous_commit_id (str): previous package's commit ID
            change_log_header (str): first line of the change log
            user_name (str): name used when updating RPM specification files
                change logs
            user_email (str): email used when updating RPM specification files
                change logs
        """
        LOG.info("%s: Bumping release" % self.pkg)
        change_log_lines = []
        if change_log_header is not None:
            change_log_lines.append(change_log_header)

        if previous_commit_id:
            new_source = self.pkg.sources[0]["git"]
            new_commit_id = new_source["commit_id"]
            LOG.info("Updating package %s from %s to %s" % (
                self.pkg.name, previous_commit_id, new_commit_id))
            change_log_lines += _get_git_commit_log(
                new_source["repo"], new_commit_id)
            replace_str_in_file(
                self.pkg.package_file, previous_commit_id, new_commit_id)
            self.pkg.spec_file.update_commit_id(previous_commit_id, new_commit_id)

        if change_log_lines:
            assert user_name is not None
            assert user_email is not None
            self.pkg.spec_file.bump_release(change_log_lines, user_name, user_email)

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


def run(CONF):
    versions_repo = setup_versions_repository(CONF)
    packages_to_update = CONF.get('packages') or PACKAGES
    distro = distro_utils.get_distro(
        CONF.get('distro_name'),
        CONF.get('distro_version'),
        CONF.get('architecture'))
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

    # get packages names
    packages_to_update_names = []
    for package in packages_to_update:
        packages_to_update_names.append(package.split("#")[0])

    LOG.info("Checking for updates in packages versions: %s",
             ", ".join(packages_to_update_names))
    pm = packages_manager.PackagesManager(packages_to_update_names)
    pm.prepare_packages(packages_class=rpm_package.RPM_Package,
                        download_source_code=False, distro=distro)

    updates_available = False
    for pkg in pm.packages:
        pkg.lock()
        pkg_version = Version(pkg)
        updates_available = (pkg_version.update(updater_name, updater_email)
                             or updates_available)
        pkg.unlock()

    if updates_available:
        packages_names = discover_packages()
        METAPACKAGE_NAME = "open-power-host-os"
        packages_names.remove(METAPACKAGE_NAME)
        update_metapackage(
            versions_repo, distro, METAPACKAGE_NAME, packages_names,
            updater_name, updater_email)

        if commit_updates:
            commit_message = (CONF.get('commit_message')
                              or "Update packages versions")
            versions_repo.commit_changes(
                commit_message, updater_name, updater_email)

            if push_updates:
                LOG.info("Pushing packages versions updates")
                versions_repo.push_head_commits(push_repo_url, push_repo_branch)
        elif push_updates:
            LOG.warning("Not pushing branch because no commit was created")
    else:
        LOG.info("No updates in packages versions, skipping metapackage "
                 "update and commit creation")
        if push_updates:
            LOG.info("No updates, pushing branch with unaltered head")
            versions_repo.push_head_commits(push_repo_url, push_repo_branch)
        raise exception.NoPackagesUpdated()

    LOG.info("Packages updated succesfully")
