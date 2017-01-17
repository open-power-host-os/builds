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

import os

from lib import distro
from lib import mockbuilder

# The old versions contains directories erroneously named "7.2" instead
# of just "7". To keep backwards compatibility, we have to list "7.2" as
# a supported version in addition to "7". To build those versions,
# you'll have to edit the version in your "config.yaml" file to "7.2".
CENTOS_VERSIONS = ["7.2", "7", ]


class CentOS(distro.LinuxDistribution):

    supported_versions = CENTOS_VERSIONS

    def __init__(self, name, version, arch_and_endianness):
        super(CentOS, self).__init__(name=name, version=version,
                                     arch_and_endianness=arch_and_endianness)
        mock_config_dir = os.path.join(os.getcwd(), 'extras/centOS/7/mock')
        self.package_builder = mockbuilder.Mock(os.path.join(
            mock_config_dir,
            'epel-7-ppc64le.cfg'))
