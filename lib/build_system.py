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

import abc
import logging

LOG = logging.getLogger(__name__)


class PackageBuilder(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def build(self):
        """
        This is where all the action really happens, rpm or deb classes have
        to implement this with their respective build steps
        """

    @abc.abstractmethod
    def clean(self):
        """
        clean up steps.
        """
