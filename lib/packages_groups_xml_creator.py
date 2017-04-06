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


def convert_name_to_id(element_name, suffix):
    """
    Convert a human readable name of an element of the XML to a more
    parser friendly ID.

    Args:
        element_name (str): human readable element name
        suffix (str): suffix to append to element ID

    Returns:
        str: element ID
    """
    return element_name.lower().replace(" ", "-") + "-" + suffix


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


def create_grouplist_xml(grps):
    """
    Construct XML representing the 'grouplist' element.

    Args:
        grps ([str]): groups names

    Returns:
        Element: object representing the 'grouplist' element
    """
    root = Element('grouplist')
    for grp in grps:
        grp_entry = Element('groupid')
        grp_entry.text = grp
        root.append(grp_entry)
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
    grp_id.text = convert_name_to_id(group_name, "group")
    grp_name = Element('name')
    grp_name.text = group_name
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


def create_environment_xml(environment_name, environment_groups):
    """
    Construct an XML object representing an 'environment' element.
    Those elements will appear as options during the installation.
    An environment contains a list of packages groups.

    Args:
        environment_name (str): name of the environment
        environment_groups ([str]): list of groups that are members of
            the environment

    Returns:
        Element: object representing the 'environment' element
    """
    env = Element('environment')
    env_id = Element('id')
    env_id.text = convert_name_to_id(environment_name, "environment")
    env_name = Element('name')
    env_name.text = environment_name.lower().title()
    env_desc = Element('description')
    env_desc.text = '{0} packages environment'.format(env_name.text)
    env_uservisible = Element('uservisible')
    env_uservisible.text = 'true'
    env_grouplist = create_grouplist_xml(environment_groups)
    env.append(env_id)
    env.append(env_name)
    env.append(env_desc)
    env.append(env_uservisible)
    env.append(env_grouplist)

    return env


def create_comps_xml(packages_environments):
    """
    Construct XML string representing the 'comps' element.

    Args:
        packages_environments ({str: [str]}): dictionary where key is
            the package environment and value is the list of packages
            that will (indirectly) belong to that environment. An
            intermediary packages group with the same name will be
            created to contain those packages.

    Returns:
        str: string representing the XML generated
    """
    root = Element('comps')
    for group_name, group_pkgs in packages_environments.iteritems():
        root.append(create_group_xml(group_name, group_pkgs))

    for environment_name in packages_environments:
        groups = [convert_name_to_id(environment_name, "group")]
        root.append(create_environment_xml(environment_name, groups))

    return E.tostring(root, pretty_print=True, doctype=COMPS_DOCTYPE,
                      xml_declaration=True, encoding="UTF-8")
