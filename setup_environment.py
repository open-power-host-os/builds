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
# along with this program.  If not, see <http://www.gnu.ofrom lib import utils

import sys
import os

from tools import setup_environment

ROOT = 0
if __name__ == '__main__':
    if os.getuid() is not ROOT:
        print("You should run this script with root privileges.")
        sys.exit(1)
    if len(sys.argv) != 2:
        print("Usage: setup_environment.py YOUR_USER_LOGIN")
        sys.exit(1)

    sys.exit(setup_environment.main(sys.argv[1]))
