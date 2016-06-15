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

import centos
import exception
import package

LOG = logging.getLogger(__name__)
DISTRIBUTIONS = {
    "centos": centos.CentOS,
}


def discover_software():
    """
    Simple mechanism for discoverability of the software we build.

    A discoverable software, and thus potentially buildable, will be assume as
    any directory name under SOFTWARE_DIRECTORY containing a yaml file with
    the same name.
    Considering the example:

    components
    +-- kernel
    |   +-- kernel.yaml
    +-- libvirt
    |   +-- libvirt.yaml
    |   +-- someother_file_or_directory
    +-- not-a-software
    |   +-- not-following-standards.yaml
    +-- file

    "kernel" and "libvirt" will be discovered, "not-a-software" and "file"
    will not.
    """
    return [software for software in os.listdir(package.COMPONENTS_DIRECTORY)
            if os.path.isdir(os.path.join(package.COMPONENTS_DIRECTORY,
                                          software)) and
            os.path.isfile(os.path.join(package.COMPONENTS_DIRECTORY,
                                        software,
                                        "".join([software, ".yaml"])))
            ]


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
    if not DISTRIBUTIONS.get(distro, None):
        raise exception.DistributionNotSupportedError(distribution=distro)

    return DISTRIBUTIONS.get(distro, None)(distro, version, arch_and_endianess)
