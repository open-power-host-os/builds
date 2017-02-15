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

from lib import utils


class LogHelper(object):
    def __init__(self, log_file_path=None, verbose=False, rotate_size=0):
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
            log_dir = os.path.dirname(log_file_path)
            utils.create_directory(log_dir)

            logger.info("Logs available at %s" % log_file_path)

            rfh = logging.handlers.RotatingFileHandler(
                log_file_path, maxBytes=rotate_size, backupCount=1)
            rfh.setLevel(logging.DEBUG)
            rfh.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s: %(message)s'))
            logger.addHandler(rfh)
