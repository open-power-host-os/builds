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
import platform
import subprocess

import exception

LOG = logging.getLogger(__name__)


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


def detect_distribution():
    # TODO(maurosr): Replace platform module by some alternative like distro
    # (https://github.com/nir0s/distro) or maybe just implementing our own
    # solution => platform module is deprecated in python 3.5 and will be
    # removed in python 3.7
    distro, version, _ = platform.linux_distribution(full_distribution_name=0)
    arch_and_endianess = platform.machine()

    # NOTE(maurosr): when it fails to detect the distro it defaults to the
    # distro and version arguments passsed as parameters - their default
    # values are empty strings.
    if not distro or not version or not arch_and_endianess:
        raise exception.DistributionDetectionError
    return (distro, version, arch_and_endianess)
