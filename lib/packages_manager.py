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

from lib import config
from lib import exception
from lib.package import Package

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)


class PackagesManager(object):
    def __init__(self, packages_names):
        self.packages_names = packages_names
        self.packages = []

    def prepare_packages(self, packages_class=Package,
                         download_source_code=True, **packages_keyword_args):
        """
        Load packages data and optionally download files.
        Use packages keyword args parameter to pass extra parameters to
        an inherited class.
        """
        for package_name in self.packages_names:
            try:
                package = packages_class.get_instance(
                    package_name, **packages_keyword_args)
            except exception.PackageError:
                LOG.error("Failed to load the %s package metadata from the git repository. "
                          "See the logs for more information" % package_name)
                raise
            if download_source_code:
                package.download_files()
            self.packages.append(package)
