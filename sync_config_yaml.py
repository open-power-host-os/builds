#!/usr/bin/python2

import yaml

CONFIG_METADATA_FILE_PATH = "config_metadata.yaml"
CONFIG_FILE_PATH = "config.yaml"

def sync_config_yaml(config_metadata_file_path, config_file_path):
    """
    Create configuration file from configuration metadata file

    Args:
        config_metadata_file_path (str): config metadata file path
        config_file_path (str): config file path
    """

    with open(config_metadata_file_path) as fh:
        config_metadata = yaml.safe_load(fh)

    config = {}
    for section in config_metadata:
        config[section] = {}
        for attribute in config_metadata[section]:
            if attribute != "help":
                config[section][attribute] = config_metadata[section][attribute]["default"]
    with open(config_file_path, "w") as fh:
        fh.write(yaml.dump(config, default_flow_style=False, indent=1))


if __name__ == '__main__':
    sync_config_yaml(CONFIG_METADATA_FILE_PATH, CONFIG_FILE_PATH)

