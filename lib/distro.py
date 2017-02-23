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

import abc
import logging

from lib import exception

LOG = logging.getLogger(__name__)
# NOTE(maurosr): make it a constant since we only plan to work with little
# endian GNU/Linux distributions.
SUPPORTED_ARCH_AND_ENDIANNESS = ("PPC64LE")


class LinuxDistribution(object):
    __metaclass__ = abc.ABCMeta
    supported_versions = []

    def __init__(self, name=None, version=None, arch_and_endianness=None):
        """
        :raises exception.DistributionVersionNotSupportedError: Unsupported
        distro.
        """
        self.lsb_name = name
        if arch_and_endianness.upper() not in SUPPORTED_ARCH_AND_ENDIANNESS:
            raise exception.DistributionVersionNotSupportedError(
                msg="Endianness not supported: %s" % arch_and_endianness)
        self.arch_and_endianness = arch_and_endianness

        # NOTE(maurosr): to support multiple builds of a same version
        for supported_version in self.supported_versions:
            if version.startswith(supported_version):
                self.version = supported_version
                break
        else:
            raise exception.DistributionVersionNotSupportedError(
                distribution=name, version=version)
        LOG.info("Distribution detected: %(lsb_name)s %(version)s" %
                 vars(self))
