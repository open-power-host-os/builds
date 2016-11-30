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
import sys

import git

from lib import config
from lib import distro_utils
from lib import exception
from lib import log_helper
from lib import packages_manager
from lib import repository
from lib import utils
from lib.rpm_package import RPM_Package

LOG = logging.getLogger(__name__)
PACKAGES = [
    'SLOF',
    'ginger',
    'gingerbase',
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
    log = []
    for commit in repo.iter_commits():
        commit_message = commit.message.split('\n')[0]
        commit_message = commit_message.replace("'", "")
        commit_message = commit_message.replace("\"", "")
        log.append("%s %s" % (commit.hexsha, commit_message))
        if commit.hexsha.startswith(since_id):
            break

    return log


def rpm_bump_spec(specfile, log, user_name, user_email):
    comment = "\n".join(['- ' + l for l in log])
    user_string = "%(user_name)s <%(user_email)s>" % locals()
    cmd = "rpmdev-bumpspec -c '%s' -u '%s' %s" % (comment, user_string, specfile)
    utils.run_command(cmd)


def rpm_query_spec_file(tag, spec):
    return utils.run_command(
        "rpmspec --srpm -q --qf '%%{%s}' %s 2>/dev/null" % (
            tag.upper(), spec)).strip()

def rpm_cmp_versions(v1, v2):
    try:
        utils.run_command("rpmdev-vercmp %s %s" % (v1, v2))
        rc = 0
    except exception.SubprocessError as exc:
        if exc.returncode == 11:
            rc = 1
        elif exc.returncode == 12:
            rc = -1
        else:
            raise
    return rc


class Version(object):
    def __init__(self, pkg):
        self.pkg = pkg
        self._spec_version = None
        self._spec_release = None
        self._prerelease = "%{nil}"
        self._repo_version = None

        self._read_spec()

    @property
    def version(self):
        return self._spec_version

    @property
    def release(self):
        return self._spec_release

    def update(self, user_name, user_email):
        changelog = None

        pkg = copy.copy(self.pkg)
        pkg.commit_id = None
        pkg.download_files(recurse=False)
        pkg.commit_id = pkg.repository.head.commit.hexsha

        if pkg.commit_id == self.pkg.commit_id:
            LOG.debug("%s: no changes.", self.pkg)
            return

        self._read_version_from_repo(pkg.repository.working_tree_dir)

        result = rpm_cmp_versions(self._spec_version, self._repo_version)
        if result < 0:
            self._update_version()
            changelog = "Version update"
        elif result > 0:
            raise exception.PackageError(
                "Current version (%s) is greater than repo version (%s)" %
                (self._spec_version, self._repo_version))

        self._update_prerelease_tag()
        self._bump_release(pkg, changelog, user_name, user_email)

    def _update_version(self):
        LOG.info("%s: Updating version to: %s" % (self.pkg,
                                                  self._repo_version))

        with open(self.pkg.specfile, 'r+') as f:
            content = f.read()

            version = re.search(r'Version:\s*(\S+)', content).group(1)

            # we accept the Version tag in the format: xxx or %{xxx},
            # but not: xxx%{xxx}, %{xxx}xxx or %{xxx}%{xxx} because
            # there is no reliable way of knowing what the macro
            # represents in these cases.
            if re.match(r'(.+%{.*}|%{.*}.+)', version):
                raise exception.PackageSpecError("Failed to parse spec file "
                                                 "'Version' tag")

            if "%{" in version:
                macro_name = version[2:-1]
                content = self._replace_macro_definition(
                    macro_name, self._repo_version, content)
            else:
                content = re.sub(r'(Version:\s*)\S+',
                                 r'\g<1>' + self._repo_version, content)

            # since the version was updated, set the Release to 0. When
            # the release bump is made, it will increment to 1.
            content = re.sub(r'(Release:\s*)[\w.-]+', r'\g<1>0', content)

            f.seek(0)
            f.write(content)

    def _bump_release(self, pkg, log=None, user_name=None, user_email=None):
        LOG.info("%s: Bumping release" % self.pkg)

        if self.pkg.commit_id:
            LOG.info("Updating package %s from %s to %s" % (
                self.pkg.name, self.pkg.commit_id, pkg.commit_id))
            log = _get_git_log(pkg.repository, self.pkg.commit_id)
            _sed_yaml_descriptor(self.pkg.package_file, self.pkg.commit_id,
                                 pkg.commit_id)

        if log:
            assert user_name is not None
            assert user_email is not None
            rpm_bump_spec(pkg.specfile, log, user_name, user_email)

    def _update_prerelease_tag(self):
        with open(self.pkg.specfile, 'r+') as f:
            content = self._replace_macro_definition(
                'prerelease', self._prerelease, f.read())
            f.seek(0)
            f.write(content)
        LOG.info("%s: Updated prerelease tag" % self.pkg)

    def _replace_macro_definition(self, macro_name, replacement, text):
        return re.sub(r'(%%define\s+%s\s+)\S+' % macro_name,
                      r'\g<1>' + replacement, text)

    def _read_spec(self):
        self._spec_version = rpm_query_spec_file('version', self.pkg.specfile)
        LOG.info("%s: Current version: %s" % (self.pkg, self._spec_version))
        self._spec_release = rpm_query_spec_file(
            'release', self.pkg.specfile).split('.')[0]

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
                        self._prerelease = last_group.replace('-', '.')
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
        versions_repo_push_branch, committer_name, committer_email):
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


def main(args):
    CONF = utils.setup_default_config()
    versions_repo = utils.setup_versions_repository(CONF)
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
    pm.prepare_packages(packages_class=RPM_Package, download_source_code=False,
                        distro=distro)

    for pkg in pm.packages:
        try:
            pkg_version = Version(pkg)
            pkg_version.update(committer_name, committer_email)
        except exception.PackageError as e:
            LOG.exception("Failed to update versions")
            return e.errno

    release_date = datetime.today().date().isoformat()
    push_new_versions(versions_repo, release_date, push_repo_url,
                      push_repo_branch, committer_name, committer_email)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
