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
import subprocess

from lib import exception

LOG = logging.getLogger(__name__)


def set_http_proxy_env(proxy):
    LOG.info('Setting up http proxy: {}'.format(proxy))
    os.environ['https_proxy'] = proxy
    os.environ['http_proxy'] = proxy


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
