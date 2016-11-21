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

from collections import OrderedDict
import logging

LOG = logging.getLogger(__name__)


class Scheduler(object):
    """
    A *very primitive* scheduler just to deal with dependencies between the
    packages we build. In the case qemu needs libseccomp, but this may become
    more useful once kimchi, ginger, wok and some other projects at
    open-power-host-os namespace are added.
    This class basically returns a tuple containing the best order to build
    things.
    """
    def __call__(self, packages):
        self.packages = packages
        LOG.info("Scheduling packages and their dependecies: %s" % packages)
        ordered_packages = self._dfs(packages, [])
        LOG.debug("Scheduled order: %s" % ordered_packages)
        return tuple(ordered_packages)

    def _dfs(self, packages, visited):
        """
        Return a list containing unique package names.
        """
        order = []
        try:
            p = packages[0]
        except IndexError:
            pass
        else:
            if p not in visited:
                visited.append(p)
                if p.dependencies:
                    order.extend(self._dfs(p.dependencies, visited))
                if p.build_dependencies:
                    order.extend(self._dfs(p.build_dependencies, visited))
                order.append(p)
            order.extend(self._dfs(packages[1:], visited))
        return list(OrderedDict.fromkeys(order))
