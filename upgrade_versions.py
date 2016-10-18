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
import sys

import pygit2

from lib import config
from lib import exception
from lib import manager
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
    comment = "\n".join(log)
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

    def bump_release(self):
        if self.pkg.commit_id:
            pkg = copy.copy(self.pkg)
            pkg.commit_id = None
            pkg.download_source_code()
            pkg.commit_id = pkg.repository.repo.head.target.hex[:7]
            if pkg.commit_id != self.pkg.commit_id:
                print("Updating package %s from %s to %s" % (
                      self.pkg.name, self.pkg.commit_id, pkg.commit_id))
                log = _get_git_log(pkg.repository.repo, self.pkg.commit_id)
                rpm_bump_spec(pkg.specfile, log)
                _sed_yaml_descriptor(self.pkg.package_file, self.pkg.commit_id,
                                     pkg.commit_id)


def main(args):
    bm = manager.BuildManager(CONF.get('default').get('packages') or PACKAGES)
    bm.prepare_packages(download_source_code=False)

    for pkg in bm.packages:
        try:
            pkg_version = Version(pkg)
            pkg_version.bump_release()
        except:
            LOG.exception("Failed to update versions")
            return False


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
