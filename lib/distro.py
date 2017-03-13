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
SUPPORTED_ARCHITECTURES = ("ppc64le")


class LinuxDistribution(object):
    __metaclass__ = abc.ABCMeta
    supported_versions = []

    def __init__(self, name=None, version=None, architecture=None):
        """
        Constructor

        Args:
            name (str): distribution name
            version (str): distribution version
            architecture (str): distribution architecture codename
                (e.g. ppc64le)

        Raises:
            exception.DistributionVersionNotSupportedError: unsupported
                distribution
        """
        self.lsb_name = name
        if architecture.lower() not in SUPPORTED_ARCHITECTURES:
            raise exception.DistributionVersionNotSupportedError(
                msg="Architecture not supported: %s" % architecture)

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
