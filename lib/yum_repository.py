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

from lib import utils

YUM_MAIN_CONFIG = """\
[main]
reposdir=/dev/null
plugins=1
"""

YUM_REPO_CONFIG_TEMPLATE = """\
[{short_name}]
name={long_name}
{url_type}={url}
failovermethod=priority
enabled=1
gpgcheck=0
{priority_line}\
"""


def create_repository(dir_path):
    """
    Create yum repository in a directory containing RPM packages.

    Args:
        directory (str): path to directory containing RPM packages
    """
    utils.run_command("createrepo %s" % dir_path)


def create_repository_config(short_name, long_name, url, url_type="baseurl", priority=None):
    """
    Create yum repository in a directory containing RPM packages.

    Args:
        short_name (str): repository's short name
        long_name (str): repository's long (descriptive) name
        url (str): URL to yum repository
        url_type (str): type of repository URL (baseurl or mirrorlist)
        priority (int): repository priority. Lower numbers have higher
            priority.

    Returns:
        str: repository configuration ready to be written to a yum
            config file

    """
    if priority is not None:
        priority_line = "priority={}\n".format(priority)
    else:
        priority_line = ""

    return YUM_REPO_CONFIG_TEMPLATE.format(
        short_name=short_name, long_name=long_name, url=url, url_type=url_type,
        priority_line=priority_line)
