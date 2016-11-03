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

import copy
import logging
import os
import re
import sys

import pygit2

from lib import config
from lib import exception
from lib import log_helper
from lib import manager
from lib import repository
from lib import utils

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)
PACKAGES = ['qemu', 'kernel', 'libvirt', 'kimchi', 'ginger', 'gingerbase',
            'wok', 'sos', 'SLOF']


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
    for commit in repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL):
        commit_message = commit.message.split('\n')[0]
        commit_message = commit_message.replace("'", "")
        commit_message = commit_message.replace("\"", "")
        log.append("%s %s" % (commit.hex[:7], commit_message))
        if commit.hex.startswith(since_id):
            break

    return log


def rpm_bump_spec(specfile, log):
    comment = "\n".join(['- ' + l for l in log])
    cmd = "rpmdev-bumpspec -c '%s' %s" % (comment, specfile)
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
        self._repo_version = None

        self._read_spec()

    @property
    def version(self):
        return self._spec_version

    @property
    def release(self):
        return self._spec_release

    def update(self):
        changelog = None

        pkg = copy.copy(self.pkg)
        pkg.commit_id = None
        pkg.download_source_code()
        pkg.commit_id = pkg.repository.repo.head.target.hex[:7]

        if pkg.commit_id == self.pkg.commit_id:
            LOG.debug("%s: no changes.", self.pkg)
            return

        self._read_version_from_repo(pkg.repository.local_path)

        result = rpm_cmp_versions(self._spec_version, self._repo_version)
        if result < 0:
            self._update_version()
            changelog = "Version update"
        elif result > 0:
            raise exception.PackageError(
                "Current version (%s) is greater than repo version (%s)" %
                (self._spec_version, self._repo_version))

        self._bump_release(pkg, changelog)

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
                content = re.sub(r'(%define\s+%s\s+)\S+' % macro_name,
                                 r'\g<1>' + self._repo_version, content)
            else:
                content = re.sub(r'(Version:\s*)\S+',
                                 r'\g<1>' + self._repo_version, content)

            # since the version was updated, set the Release to 0. When
            # the release bump is made, it will increment to 1.
            content = re.sub(r'(Release:\s*)[\w.-]+', r'\g<1>0', content)

            f.seek(0)
            f.write(content)

    def _bump_release(self, pkg, log=None):
        LOG.info("%s: Bumping release" % self.pkg)

        if self.pkg.commit_id:
            LOG.info("Updating package %s from %s to %s" % (
                self.pkg.name, self.pkg.commit_id, pkg.commit_id))
            log = _get_git_log(pkg.repository.repo, self.pkg.commit_id)
            _sed_yaml_descriptor(self.pkg.package_file, self.pkg.commit_id,
                                 pkg.commit_id)

        if log:
            rpm_bump_spec(pkg.specfile, log)

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
                self._repo_version = '.'.join(s.strip()
                                              for s in match.groups() if s)
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


def main(args):
    log_helper.LogHelper(logfile=CONF.get('default').get('log_file'),
                         verbose=CONF.get('default').get('verbose'))
    LOG.info("Updating packages version...")

    try:
        # setup versions directory
        path, dirname = os.path.split(
            CONF.get('default').get('build_versions_repo_dir'))
        repository.Repo(
            dirname, CONF.get('default').get('build_versions_repository_url'),
            path, CONF.get('default').get('build_version'))
    except exception.RepositoryError as exc:
        LOG.exception("Failed to checkout versions repository")
        return exc.errno

    bm = manager.BuildManager(CONF.get('default').get('packages') or PACKAGES)
    bm.prepare_packages(download_source_code=False)

    for pkg in bm.packages:
        try:
            pkg_version = Version(pkg)
            pkg_version.update()
        except exception.PackageError as e:
            LOG.exception("Failed to update versions")
            return e.errno


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
