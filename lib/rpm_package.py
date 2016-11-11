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
import logging
import yaml

from lib import config
from lib import exception
from lib.package import Package

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)
BUILD_DEPENDENCIES = "build_dependencies"
DEPENDENCIES = "dependencies"


class RPM_Package(Package):

    def __init__(self, name, distro, *args, **kwargs):
        self.distro = distro
        super(RPM_Package, self).__init__(name, *args, **kwargs)

    def _load(self):
        """
        Read yaml file describing this package.
        """
        super(RPM_Package, self)._load()
        try:
            # load distro files
            files = self.package_data.get('files').get(
                self.distro.lsb_name).get(self.distro.version)

            self.build_files = files.get('build_files', None)
            if self.build_files:
                self.build_files = os.path.join(
                    self.package_dir, self.name, self.build_files)
            self.download_build_files = files.get('download_build_files', [])

            # list of dependencies
            for dep_name in files.get('dependencies', []):
                dep = RPM_Package.get_instance(
                    dep_name, self.distro, category=DEPENDENCIES)
                self.dependencies.append(dep)

            for dep_name in files.get('build_dependencies', []):
                dep = RPM_Package.get_instance(
                    dep_name, self.distro, category=BUILD_DEPENDENCIES)
                self.build_dependencies.append(dep)

            self.rpmmacro = files.get('rpmmacro', None)
            if self.rpmmacro:
                self.rpmmacro = os.path.join(
                    self.package_dir, self.name, self.rpmmacro)

            self.specfile = os.path.join(self.package_dir, self.name,
                                         files.get('spec'))

            if os.path.isfile(self.specfile):
                LOG.info("Package found: %s for %s %s" % (
                    self.name, self.distro.lsb_name, self.distro.version))
            else:
                raise exception.PackageSpecError(
                    package=self.name,
                    distro=self.distro.lsb_name,
                    distro_version=self.distro.version)
        except TypeError:
            raise exception.PackageDescriptorError(package=self.name)
