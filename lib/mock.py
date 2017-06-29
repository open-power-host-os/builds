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

from lib import config
from lib import utils

CONF = config.get_config().CONF

class Mock(object):
    """
    Centralize calls to mock command, setting the arguments common to
    all of them.
    """

    def __init__(self, config_file, unique_extension):
        """
        Initialize arguments common to all mock calls.

        Args:
            config_file (str): configuration file path
            unique_extension (str): unique extension to append to chroot
                directory name
        """
        self.binary_file = CONF.get('mock_binary')
        self.config_file = config_file
        self.extra_args = CONF.get('mock_args') or ""
        self.unique_extension = unique_extension

        self.common_mock_args = [
            self.binary_file, "-r", self.config_file, self.extra_args,
            "--uniqueext", self.unique_extension]

    def run_command(self, cmd):
        """
        Run mock command using arguments passed to the constructor.

        Args:
            cmd (str): mock command to execute

        Returns:
            mock command standard output
        """
        cmd = " ".join(self.common_mock_args + [cmd])
        return utils.run_command(cmd)
