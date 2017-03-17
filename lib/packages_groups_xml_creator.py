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

from lxml import etree as E
from lxml.etree import Element

COMPS_DOCTYPE = (
    '<!DOCTYPE comps PUBLIC "-//Host OS//DTD Comps info//EN" "comps.dtd">')


def create_packagelist_xml(pkgs):
    """
    Construct XML representing the 'packagelist' element.

    Args:
        pkgs ([str]): packages names

    Returns:
        Element: object representing the 'packagelist' element
    """
    root = Element('packagelist')
    for pkg in pkgs:
        pkg_entry = Element('packagereq')
        pkg_entry.text = pkg
        root.append(pkg_entry)
    return root


def create_group_xml(group_name, group_pkgs):
    """
    Construct XML object representing a 'group' element.

    Args:
        group_name (str): name of a group of packages.
        group_pkgs ([str]): list of packages that are member of the group.

    Returns:
        Element: object representing the 'group' element
    """
    grp = Element('group')
    grp_id = Element('id')
    grp_id.text = group_name.lower()
    grp_name = Element('name')
    grp_name.text = group_name.lower().title()
    grp_desc = Element('description')
    grp_desc.text = '{0} packages group'.format(grp_name.text)
    grp_uservisible = Element('uservisible')
    grp_uservisible.text = 'true'
    grp_packagelist = create_packagelist_xml(group_pkgs)
    grp.append(grp_id)
    grp.append(grp_name)
    grp.append(grp_desc)
    grp.append(grp_uservisible)
    grp.append(grp_packagelist)

    return grp


def create_comps_xml(packages_groups):
    """
    Construct XML string representing the 'comps' element.

    Args:
        packages_groups ({str:[str]}): dictionary where key is the package group
                                       name and value is the list of packages
                                       that are member of the group

    Returns:
        str: string representing the XML generated
    """
    root = Element('comps')
    for group_name, group_pkgs in packages_groups.iteritems():
        root.append(create_group_xml(group_name, group_pkgs))

    return E.tostring(root, pretty_print=True, doctype=COMPS_DOCTYPE,
                      xml_declaration=True, encoding="UTF-8")
