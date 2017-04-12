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

import logging
import os

from lxml import etree

from lib import packages_manager
from lib import rpm_package


LOG = logging.getLogger(__name__)


def create_html_table(packages):
    """
    Create a HTML table with the packages versions

    Args:
        packages ([Package]): packages
    """

    table = etree.Element('table')
    thead = etree.SubElement(table, 'thead')
    software_th = etree.SubElement(thead, 'th')
    software_th.text = 'Software'

    version_th = etree.SubElement(thead, 'th')
    version_th.text = 'Version'

    tbody = etree.SubElement(table, 'tbody')

    for package in packages:
        tr = etree.SubElement(tbody, 'tr')
        package_name_td = etree.SubElement(tr, 'td')
        package_name_td.text = package.name

        package_version_td = etree.SubElement(tr, 'td')
        package_version_td.text = package.version

    return etree.tostring(table, pretty_print=True)


def replace_file_section(
        file_path, new_contents, start_delimiter, end_delimiter=None):
    """
    Replace contents enclosed in delimiters in file.

    Args:
        file_path (str): file path
        new_contents (str): contents that will replace the old ones
        start_delimiter (str): delimiter marking start of contents to be
            replaced
        end_delimiter (str): delimiter marking end of contents to be
            replaced, or None for end of file
    """

    with file(file_path, "r") as f:
        lines = f.readlines()

    # replace
    new_lines = []
    in_delimiters = False
    for line in lines:
        if not in_delimiters and start_delimiter in line:
            in_delimiters = True
            new_lines.append(new_contents)
            if end_delimiter is None:
                break
        elif in_delimiters:
            if end_delimiter in line:
                in_delimiters = False
        else:
            new_lines.append(line)

    with file(file_path, "w") as f:
        f.writelines(new_lines)


def update_versions_in_readme(versions_repo, distro, packages_names):
    """
    Update packages versions in README

    Args:
        versions_repo (GitRepository): versions git repository handler
        distro (distro.LinuxDistribution): Linux distribution
        packages_names ([str]): list of packages whose versions must be updated
    """

    LOG.info("Generating packages versions HTML table from packages: %s",
             ", ".join(packages_names))
    pm = packages_manager.PackagesManager(packages_names)
    # TODO: this is coupled with RPM-based Linux distributions
    pm.prepare_packages(packages_class=rpm_package.RPM_Package,
                        download_source_code=False, distro=distro)

    html_table = create_html_table(pm.packages)
    output_readme_path = os.path.join(versions_repo.working_tree_dir,
                                      'README.md')
    replace_file_section(output_readme_path, html_table, "<table>", "</table>")
