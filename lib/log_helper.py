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


class LogHelper(object):
    def __init__(self, logfile=None, level=logging.DEBUG):
        self.logfile = logfile
        self.loglevel = level

        self._directory_setup()
        logging.basicConfig(filename=logfile, level=level)

    def _directory_setup(self):
        logpath, _ = os.path.split(self.logfile)
        try:
            os.makedirs(logpath)
        except OSError:
            # failled to create
            if not os.path.exists(logpath):
                raise
            # Directory already exists
            pass
