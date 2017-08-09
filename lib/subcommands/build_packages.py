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

from lib import distro_utils
from lib import build_info
from lib import build_manager
from lib import packages_manager
from lib.versions_repository import setup_versions_repository

LOG = logging.getLogger(__name__)


def run(CONF):
    setup_versions_repository(CONF)
    packages_to_build = (CONF.get('packages') or
                         packages_manager.discover_packages())
    distro = distro_utils.get_distro(
        CONF.get('distro_name'),
        CONF.get('distro_version'),
        CONF.get('architecture'))

    # get packages names
    packages_to_build_names = []
    for package in packages_to_build:
        packages_to_build_names.append(package.split("#")[0])

    LOG.info("Building packages: %s", ", ".join(packages_to_build_names))
    bm = build_manager.BuildManager(packages_to_build_names, distro)
    bm.build()

    build_info.write_built_pkgs_info_file(bm)
