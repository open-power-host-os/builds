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
    def __init__(self, log_file_path=None, verbose=False, rotate_size=None):
        self.log_file_path = log_file_path

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        sh = logging.StreamHandler(sys.stdout)
        if verbose:
            sh.setLevel(logging.DEBUG)
        else:
            sh.setLevel(logging.INFO)
        sh.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(sh)

        if log_file_path:
            self._directory_setup()
            logger.info("Logs available at %s" % log_file_path)

            # NOTE(maurosr): RotatingFileHandler expects file size in bytes, in
            # short terms we're defining 2MB limit here.
            if not rotate_size:
                rotate_size = 2 << 20
            rfh = logging.handlers.RotatingFileHandler(
                log_file_path, maxBytes=rotate_size, backupCount=1)
            rfh.setLevel(logging.DEBUG)
            rfh.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s: %(message)s'))
            logger.addHandler(rfh)

    def _directory_setup(self):
        logpath, _ = os.path.split(self.log_file_path)

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
