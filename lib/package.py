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

import exception

LOG = logging.getLogger(__name__)
COMPONENTS_DIRECTORY = os.path.join(os.getcwd(), "components")


class Package(object):

    def __init__(self, package, distro):
        self.load_package(package, distro)

    def load_package(self, package_name, distro):
        """
        Read yaml files descbring our supported packages
        """
        self.name = package_name
        self.distro_name = distro.lsb_name
        self.distro_version = distro.version
        try:
            with open(os.path.join(COMPONENTS_DIRECTORY, package_name,
                                   '%s.yaml' % package_name),
                      'r') as package_file:
                package = yaml.load(package_file)['Package']
                self.name = package['name']
                self.clone_url = package['clone_url']
                self.branch = package.get('branch', None)
                self.specfile = os.path.join(
                    COMPONENTS_DIRECTORY,
                    package_name,
                    package.get(
                        'specs')[self.distro_name][self.distro_version])

                if os.path.isfile(self.specfile):
                    LOG.info("Package found: %(name)s for %(distro_name)s "
                             "%(distro_version)s" % vars(self))
                else:
                    raise exception.PackageSpecError(
                        package=self.name,
                        distro=self.distro_name,
                        distro_version=self.distro_version)

        except TypeError:
            raise exception.PackageDescriptorError(package=self.name)
