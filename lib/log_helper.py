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
import logging.handlers
import os
import sys


class LogHelper(object):
    def __init__(self, logfile=None, level=logging.DEBUG, verbose=False):
        self.logfile = logfile
        self.loglevel = level

        self._directory_setup()

        logger = logging.getLogger()
        logging.basicConfig(filename=logfile, level=level)
        print("Logs available at %s" % logfile)
        # NOTE(maurosr): RotatingFileHandler expects file size in bytes, in
        # short terms we're defining 2MB limit here.
        logger.addHandler(logging.handlers.RotatingFileHandler(
            logfile, maxBytes=2 << 20, backupCount=1))
        if verbose:
            logger.addHandler(logging.StreamHandler(sys.stdout))

    def _directory_setup(self):
        logpath, _ = os.path.split(self.logfile)

        # empty logpath means local directory and thus the next steps are
        # unnecessary
        if logpath:
            try:
                os.makedirs(logpath)
            except OSError:
                # failed to create
                if not os.path.exists(logpath):
                    raise
                # Directory already exists
                pass
