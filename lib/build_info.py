# Copyright (C) IBM Corp. 2017.
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

import pprint
import logging

LOG = logging.getLogger(__name__)


class PackageInfo(object):
    def __init__(self, pkg):
        self.pkg = pkg

    def __getattr__(self, attr):
        if hasattr(self.pkg, attr):
            return getattr(self.pkg, attr)
        raise AttributeError("%r object has no attribute %r" %
                             (self.pkg.__class__, attr))


def query_pkgs_info(packages, target_attrs, include_unbuilt=False):
    """
    Query information about packages

    Args:
        packages([Package]): packages from which to extract information
        target_attrs([str]): attributes to return for each package
        include_unbuilt(bool): whether to include in the query results
                               packages that were not built

    Returns:
        dict: packages information
    """

    packages_info = {pkg.name: {attr: getattr(PackageInfo(pkg), attr)
                                for attr in target_attrs}
                     for pkg in packages if pkg.built or include_unbuilt}

    LOG.debug("Query:\n%s\nResult:\n%s", sorted(target_attrs),
              pprint.pformat(packages_info, width=1))
    return packages_info
