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
