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

import lib.centos
from lib import exception
import lib.scheduler
from lib.packages_manager import PackagesManager
from lib.rpm_package import RPM_Package

LOG = logging.getLogger(__name__)


class BuildManager(object):
    def __init__(self, packages_names, distro):
        self.packages_manager = PackagesManager(packages_names)
        self.distro = distro
        self.repositories = None

    def __call__(self):
        try:
            self.packages_manager.prepare_packages(
                packages_class=RPM_Package, distro=self.distro)
        # distro related issues
        except (exception.DistributionNotSupportedError,
                exception.DistributionVersionNotSupportedError,
                exception.DistributionDetectionError):
            LOG.error("Error during distribution detection. "
                      "See the logs for more information")
            raise

        self.build()

    def build(self):
        scheduler = lib.scheduler.Scheduler()
        self.distro.build_packages(scheduler(self.packages_manager.packages))
