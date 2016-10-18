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


class Versions(object):
    def __init__(self, package_list):
        self.bm = manager.BuildManager(package_list)
        self.bm.prepare_packages(download_source_code=False)

    def upgrade_versions(self):
        stable_versioning = self.bm.packages
        new_versioning = []
        for x in stable_versioning:
            if x.commit_id:
                copy_of_x = copy.copy(x)
                copy_of_x.commit_id = None
                new_versioning.append(copy_of_x)
                copy_of_x.download_source_code()
                copy_of_x.commit_id = (
                    copy_of_x.repository.repo.head.target.hex[:7])
                if copy_of_x.commit_id != x.commit_id:
                    print("Updating package %s from %s to %s" % (
                          x.name, x.commit_id, copy_of_x.commit_id))
                    log = _get_git_log(copy_of_x.repository.repo, x.commit_id)
                    rpm_bump_spec(copy_of_x.specfile, log)
                    _sed_yaml_descriptor(x.package_file, x.commit_id,
                                         copy_of_x.commit_id)


def main(args):
    env = Versions(CONF.get('default').get('packages') or PACKAGES)
    env.upgrade_versions()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
