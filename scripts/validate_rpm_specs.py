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

sys.path.insert(0, '..')

from lib import exception
from lib.utils import is_package_installed
from lib.utils import recursive_glob
from lib.utils import run_command

def validate_rpm_spec(spec_file_path):
    """
    Validate RPM specification file

    Args:
        spec_file_path (str): RPM specification file path

    Returns:
        bool: if RPM specification file is valid
    """

    try:
        run_command("rpmlint -f .rpmlint -v %s" % spec_file_path)
    except exception.SubprocessError as e:
        #pylint: disable=no-member
        print("validation of RPM specification file %s failed, output: %s" % (spec_file_path, e.stdout))
        return False

    return True


def validate_rpm_specs(base_dir):
    """
    Validate specification files of rpm packages in a base directory

    Args:
        base_dir (str): base directory path

    Returns:
        bool: if RPM specification files are valid
    """

    files = recursive_glob(base_dir, "*.spec")
    valid = True
    for _file in files:
        if not validate_rpm_spec(_file):
            valid = False

    return valid


def parse_cli_options():
    """
    Parse CLI options

    Returns:
        Namespace: CLI options. Valid attributes: rpm_specs_base_dir
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--rpm-specs-base-dir', dest='rpm_specs_base_dir',
                        required=True, help='RPM specification files base directory path')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    if not is_package_installed('rpmlint'):
        print("rpmlint package should be installed before running this script")
        sys.exit(1)
    args = parse_cli_options()
    if not validate_rpm_specs(args.rpm_specs_base_dir):
        sys.exit(2)
