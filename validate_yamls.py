#!/usr/bin/env python
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

import argparse
import sys

from lib import exception
from lib.utils import is_package_installed
from lib.utils import recursive_glob
from lib.utils import run_command

def validate_yaml(yaml_file_path):
    """
    Validate yaml file

    Args:
        yaml_file_path (str): yaml file path

    Returns:
        bool: if YAML file is valid
    """

    try:
        run_command("yamllint %s" % yaml_file_path)
    except exception.SubprocessError as e:
        #pylint: disable=no-member
        print("validation of yaml file %s failed, output: %s" % (yaml_file_path, e.stdout))
        return False

    return True


def validate_yamls(base_dir):
    """
    Validate yaml files

    Args:
        base_dir (str): base directory path

    Returns:
        bool: if YAML files are valid
    """

    files = recursive_glob(base_dir, "*.yaml")
    valid = True
    for _file in files:
        if not validate_yaml(_file):
            valid = False

    return valid


def parse_cli_options():
    """
    Parse CLI options

    Returns:
        Namespace: CLI options. Valid attributes: yamls_base_dir
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--yamls-base-dir', dest='yamls_base_dir',
                        required=True, help='YAML files base directory path')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    if not is_package_installed('yamllint'):
        print("yamllint package should be installed before running this script")
        sys.exit(1)
    args = parse_cli_options()
    if not validate_yamls(args.yamls_base_dir):
        sys.exit(2)
