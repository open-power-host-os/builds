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

import lib.centos
from lib import config
from lib import exception
from lib import mockbuilder
from lib.packages_manager import PackagesManager
from lib.rpm_package import RPM_Package
import lib.scheduler

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)


class BuildManager(object):
    def __init__(self, packages_names, distro):
        self.packages_manager = PackagesManager(packages_names)
        self.distro = distro
        self.repositories = None

    def _build_packages(self, distro, packages):
        """
        Build packages

        Args:
            distro (Distribution): Linux distribution
            packages ([Package]): packages
        """

        # create package builder based on distro
        if distro.lsb_name == "CentOS":
            mock_config_file = os.path.join(
                "mock_configs", distro.lsb_name, distro.version,
                "%s-%s-%s.cfg" % (distro.lsb_name, distro.version, distro.arch_and_endianness))
            if not os.path.isfile(mock_config_file):
                raise exception.BaseException("Mock config file not found at %s" % mock_config_file)
            package_builder = mockbuilder.Mock(mock_config_file)
        else:
            raise exception.DistributionError()
        # create packages
        package_builder.initialize()
        for package in packages:
            if package.force_rebuild:
                LOG.info("%s: Forcing rebuild." % package.name)
                build_package = True
            elif package.needs_rebuild():
                build_package = True
            else:
                LOG.info("%s: Skipping rebuild." % package.name)
                build_package = False

            if build_package:
                package.lock()
                package.download_files(recurse=False)
                package_builder.prepare_sources(package)
                package.unlock()
                package_builder.build(package)
            package_builder.copy_results(package)

        package_builder.clean()

    def build(self):
        """
        Schedule package build order and build
        """

        force_rebuild = CONF.get('build_packages').get('force_rebuild')
        try:
            # TODO: should not restrict building to RPM packages
            self.packages_manager.prepare_packages(
                packages_class=RPM_Package, distro=self.distro,
                download_source_code=False, force_rebuild=force_rebuild)
        # distro related issues
        except (exception.DistributionNotSupportedError,
                exception.DistributionVersionNotSupportedError,
                exception.DistributionDetectionError):
            LOG.error("Error during distribution detection. "
                      "See the logs for more information")
            raise

        scheduler = lib.scheduler.Scheduler()
        ordered_packages = scheduler.schedule(self.packages_manager.packages)
        self._build_packages(self.distro, ordered_packages)
