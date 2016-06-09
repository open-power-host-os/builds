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
import exception
import logging

LOG = logging.getLogger(__name__)


class LinuxDistribution(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name=None, version=None):
        """
        :raises exception.DistributionVersionNotSupportedError: Unsupported
        distro.
        """
        self.lsb_name = name

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

    @abc.abstractmethod
    def build_packages(self):
        """
        This is were distro and builder interact and produce the packages we
        want.
        """
