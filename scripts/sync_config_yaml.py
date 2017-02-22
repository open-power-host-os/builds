#!/usr/bin/python2

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

import yaml

CONFIG_METADATA_FILE_PATH = "config/metadata.yaml"
CONFIG_FILE_PATH = "config/host_os.yaml"


def sync_config_yaml(config_metadata_file_path, config_file_path):
    """
    Create configuration file from configuration metadata file.

    Args:
        config_metadata_file_path (str): configuration metadata file path
        config_file_path (str): configuration file path
    """

    with open(config_metadata_file_path) as config_metadata_file:
        config_metadata = yaml.safe_load(config_metadata_file)

    config = {}
    for command_name, command_dict in config_metadata["commands"].items():
        config[command_name] = {}
        for option_name in command_dict["options"]:
            option_default = config_metadata["options"][option_name]["default"]
            config[command_name][option_name] = option_default

    # Do not use aliases in the YAML to make it simpler
    class NoAliasDumper(yaml.Dumper):
        def ignore_aliases(self, _data):
            return True

    with open(config_file_path, "w") as config_file:
        config_file.write(yaml.dump(config, default_flow_style=False,
        Dumper=NoAliasDumper))


if __name__ == '__main__':
    sync_config_yaml(CONFIG_METADATA_FILE_PATH, CONFIG_FILE_PATH)
