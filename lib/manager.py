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
from lib import package
import lib.scheduler
from lib import utils

LOG = logging.getLogger(__name__)


class BuildManager(object):
    def __init__(self, packages_names, distro):
        self.packages_names = packages_names
        self.packages = []
        self.distro = distro
        self.repositories = None

    def __call__(self):
        try:
            self.prepare_packages()

        # distro related issues
        except (exception.DistributionNotSupportedError,
                exception.DistributionVersionNotSupportedError,
                exception.DistributionDetectionError) as exc:
            LOG.exception("Error during distribution detection. "
                          "See the logs for more information")
            return exc.errno
        # package issues
        except exception.PackageError as exc:
            LOG.exception("Failed to load the package in components. "
                          "See the logs for more information")
            return exc.errno

        return self.build()

    def build(self):
        scheduler = lib.scheduler.Scheduler()
        self.distro.build_packages(scheduler(self.packages))

    def prepare_packages(self, download_source_code=True):
        for package_name in self.packages_names:
            package = package.Package.get_instance(
                package_name, self.distro)
            if download_source_code:
                package.download_files()
            self.packages.append(package)
