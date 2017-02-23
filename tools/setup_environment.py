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
# along with this program.  If not, see <http://www.gnu.ofrom lib import utils

import grp
import os
import stat

from lib import utils

MOCK_GROUP_ID = grp.getgrnam('mock').gr_gid
USER_EXISTS = 9


def setup_user(user):
    # just add the user first and if it exists proceed gracefully
    useradd_cmd = "useradd -M %s" % (user)
    utils.run_command(useradd_cmd, success_return_codes=[0, USER_EXISTS])
    print("Created user %s." % user)
    group = "mock"
    group_cmd = "usermod -a -G %s %s" % (group, user)
    print("Added user %s to group %s" % (user, group))
    utils.run_command(group_cmd)


def set_group_permissions(gid, path):
    file_perms = os.stat(path)
    # add group read permission
    perms = file_perms.st_mode | stat.S_IRGRP
    # add group write permission
    perms = perms | stat.S_IWGRP
    if os.path.isdir(path):
        # add group execution permission
        perms = perms | stat.S_IXGRP
    os.chmod(path, perms)
    os.chown(path, -1, gid)


def setup_directory(directory, gid):
    """
    Set the directory's owners, creating it if it does not exist.
    """
    utils.create_directory(directory)
    set_group_permissions(gid, directory)
    for root, dirnames, filenames in os.walk(directory):
        for path in dirnames + filenames:
            set_group_permissions(gid, os.path.join(root, path))


def setup_default_directories(directories, gid):
    for dirname in directories:
        setup_directory(dirname, gid)


def run(CONF):
    # NOTE(maurosr): this is just a helper script in order to do some
    # environment settings as it would be done if our scripts were installed
    # through a package like rpm or deb. If the user decides to use different
    # user or log files he needs to handle permissions by his own.
    log_dir = os.path.dirname(CONF.get('common').get('log_file'))
    repo_dir = CONF.get('common').get('packages_repos_target_path')
    user = CONF.get('common').get('user')

    setup_user(user)
    setup_default_directories([log_dir, repo_dir], MOCK_GROUP_ID)
