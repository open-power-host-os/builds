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

from lib import centos
from lib import exception

DISTRIBUTIONS = {
    "CentOS": centos.CentOS,
}
LOG = logging.getLogger(__name__)


def detect_distribution():
    """
    Detect current system Linux distribution, including name, version,
    arch and endianness.
    """
    # TODO(maurosr): Replace platform module by some alternative like distro
    # (https://github.com/nir0s/distro) or maybe just implementing our own
    # solution => platform module is deprecated in python 3.5 and will be
    # removed in python 3.7
    distro, version, _ = platform.linux_distribution(full_distribution_name=0)
    architecture = platform.machine()

    # NOTE(maurosr): when it fails to detect the distro it defaults to the
    # distro and version arguments passsed as parameters - their default
    # values are empty strings.
    if not distro or not version or not architecture:
        raise exception.DistributionDetectionError
    return (distro, version, architecture)


def get_distro(name, version, architecture):
    """
    Get a distro object from the parameters specified.
    Also check if the distro object matches the system's distribution
    and log a warning message otherwise.
    """
    detected_distribution = detect_distribution()
    detected_name, detected_version, detected_architecture = (
        detected_distribution)
    LOG.info("Detected distribution: %s" % str(detected_distribution))
    if (detected_name.lower() != name.lower()
            or not(detected_version.startswith(version))
            or detected_architecture.lower() != architecture.lower()):
        LOG.warning("Detected linux distribution differs from selected one. "
                    "Build might fail.")

    # let's make this explicity to avoid catching for a TypeError
    # exception which could be raised from the attempt to instantiate
    # the distro object.
    if not DISTRIBUTIONS.get(name):
        raise exception.DistributionNotSupportedError(
            distribution=name)
    distro_type = DISTRIBUTIONS.get(name)
    return distro_type(name, version, architecture)
