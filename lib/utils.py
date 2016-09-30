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
import platform
import subprocess
import sys

from lib import config
from lib import exception
from lib import log_helper
from lib import repository

LOG = logging.getLogger(__name__)


def setup_default_config():
    """
    Setup the script environment. Parse configurations, setup logging
    and halt execution if anything fails.
    """
    try:
        CONF = config.get_config().CONF
    except OSError:
        print("Failed to parse settings")
        sys.exit(2)

    log_helper.LogHelper(logfile=CONF.get('default').get('log_file'),
                         verbose=CONF.get('default').get('verbose'),
                         rotate_size=CONF.get('default').get('log_size'))

    return CONF


def setup_versions_repository(config):
    """
    Clone and checkout the versions repository and halt execution if
    anything fails.
    """
    path, dir_name = os.path.split(
        config.get('default').get('build_versions_repo_dir'))
    url = config.get('default').get('build_versions_repository_url')
    branch = config.get('default').get('build_version')
    try:
        versions_repo = repository.get_git_repository(dir_name, url, path)
        versions_repo.checkout(branch)
    except exception.RepositoryError as exc:
        LOG.exception("Failed to checkout versions repository")
        sys.exit(exc.errno)


def run_command(cmd, **kwargs):
    LOG.debug("Command: %s" % cmd)
    shell = kwargs.pop('shell', True)

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=shell, **kwargs)
    output, error_output = process.communicate()

    if process.returncode:
        raise exception.SubprocessError(cmd=cmd, returncode=process.returncode,
                                        stdout=output, stderr=error_output)

    LOG.debug("stdout: %s" % output)
    LOG.debug("stderr: %s" % error_output)

    return output
