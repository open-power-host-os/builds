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

from lib import exception
from lib import repository

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

                # NOTE(maurosr): Unfortunately some of the packages we build
                # depend on a gziped file which changes according to the build
                # version so we need to get that name somehow, grep the
                # specfile would be uglier imho.
                self.expects_source = package['expects_source']

                # NOTE(maurosr): branch and commit id are special cases for the
                # future, we plan to use tags on every project for every build
                # globally set in config.yaml, then this would allow some user
                # customization to set their prefered commit id/branch or even
                # a custom git tree.
                self.branch = package.get('branch', None)
                self.commit_id = package.get('commit_id', None)

                # load distro files
                files = package.get('files').get(self.distro_name).get(
                    self.distro_version)

                self.build_files = files.get('build_files', None)
                if self.build_files:
                    self.build_files = os.path.join(COMPONENTS_DIRECTORY,
                                                    package_name,
                                                    self.build_files)

                self.rpmmacro = files.get('rpmmacro', None)
                if self.rpmmacro:
                    self.rpmmacro = os.path.join(COMPONENTS_DIRECTORY,
                                                 package_name,
                                                 self.rpmmacro)

                self.specfile = os.path.join(
                    COMPONENTS_DIRECTORY,
                    package_name,
                    files.get('spec'))

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

    def setup_repository(self, dest=None, branch=None):
        self.repository = repository.Repo(package_name=self.name,
                                          clone_url=self.clone_url,
                                          dest_path=dest,
                                          branch=self.branch or branch)
