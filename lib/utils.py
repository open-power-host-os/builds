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

LOG = logging.getLogger(__name__)

SOFTWARE_DIRECTORY = os.path.join(os.getcwd(), "components")


def discover_software():
    """
    Simple mechanism for discoverability of the software we build.

    A discoverable software, and thus potentially buildable, will be assume as
    any directory name under SOFTWARE_DIRECTORY containing a yaml file with
    the same name.
    Considering the example:

    components
    +-- kernel
    |   +-- kernel.yaml
    +-- libvirt
    |   +-- libvirt.yaml
    |   +-- someother_file_or_directory
    +-- not-a-software
    |   +-- not-following-standards.yaml
    +-- file

    "kernel" and "libvirt" will be discovered, "not-a-software" and "file"
    will not.
    """
    return [software for software in os.listdir(SOFTWARE_DIRECTORY)
            if os.path.isdir(os.path.join(SOFTWARE_DIRECTORY, software)) and
            os.path.isfile(os.path.join(SOFTWARE_DIRECTORY, software,
                                        "".join([software, ".yaml"])))
            ]
