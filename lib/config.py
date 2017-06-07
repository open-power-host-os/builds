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
import os
import sys

import yaml

from lib import log_helper
from lib import utils


RAW_TEXT_ID = "R|"
CONFIG_METADATA_FILE_PATH = "config/metadata.yaml"
LOG_FILE_NAME = 'builds.log'

config_parser = None


def get_config():
    global config_parser
    if not config_parser:
        config_parser = ConfigParser()
        config_parser.parse()
    return config_parser


class CustomHelpFormatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        if text.startswith(RAW_TEXT_ID):
            return text[len(RAW_TEXT_ID):].splitlines()
        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)


class ConfigParser(object):
    """
    Parses configuration options sources.

    Precedence is:
    command line > config file
    """
    def __init__(self):
        # create the top-level parser
        self.parser = argparse.ArgumentParser(
            formatter_class=CustomHelpFormatter)
        self._CONF = None
        self._setup_command_line_parser(CONFIG_METADATA_FILE_PATH)

    @property
    def CONF(self):
        return self._CONF


    def _setup_command_line_arg_from_config_metadata(
            self, target_parser, option_name, option_dict):
        """
        Add a command line parser argument based on the metadata
        dictionary.

        Args:
            target_parser (ArgumentParser): parser that will have the
                specified option
            option_name (str): name of the destination variable after
                the options are parsed
            option_dict (str): dictionary containing option parameters
        """

        keyword_args = dict(option_dict)
        # The default value should be obtained from the configuration file
        keyword_args["default"] = None
        keyword_args["dest"] = option_name
        long_option_string = "--" + option_name.replace("_", "-")
        if keyword_args.get("action", "store") == "store":
            option_type = type(option_dict["default"])
            if option_type == list:
                keyword_args["nargs"] = "*"
            else:
                keyword_args["type"] = option_type
        elif keyword_args.get("action", "store") == "store_false":
            long_option_string = "--no-" + option_name.replace("_", "-")
        option_strings = [long_option_string]
        if "short_option_string" in keyword_args:
            option_strings.append(keyword_args.pop("short_option_string"))

        target_parser.add_argument(*option_strings, **keyword_args)


    def _setup_command_line_parser(self, config_metadata_file_path):
        """
        Configures the argument parser object to match the expected
            configuration.

        Args:
            config_metadata_file_path (str): configuration metadata file
                path
        """
        self.parser.add_argument('--config-file', '-c',
                                 help='Path of the configuration file for build '
                                      'scripts',
                                 default='config/host_os.yaml')

        subparsers = self.parser.add_subparsers(
            dest="subcommand",
            help="Available subcommands")

        # Setup parser from configuration metadata file
        with open(config_metadata_file_path) as config_metadata_file:
            config_metadata = yaml.safe_load(config_metadata_file)

        for command_name, command_dict in config_metadata["commands"].items():
            if command_name == "host_os":
                target_parser = self.parser
            else:
                # Add subparser
                command_help = command_dict["help"]
                target_parser = subparsers.add_parser(
                    command_name, help=command_help,
                    formatter_class=CustomHelpFormatter)

            # Add arguments to command line parser
            for option_name in command_dict["options"]:
                option_dict = config_metadata["options"][option_name]
                self._setup_command_line_arg_from_config_metadata(
                    target_parser, option_name, option_dict)


    def parse_command_line_arguments(self, args):
        """
        Parse configuration from command line arguments
        Used only for unit testing

        Args:
            args ([str]): command line arguments

        Returns:
            dict: Command line options provided by user. Key is option name,
                value is option value
        """
        result = self.parser.parse_args(args)
        return vars(result)

    def parse_command_line(self, command_line_args):
        """
        Parse configuration from the command line

        Args:
            command_line_args (tuple): command line arguments. Used only by tests

        Returns:
            dict: Command line options provided by user. Key is option name,
                value is option value.
        """
        if not command_line_args:
            command_line_args = sys.argv[1:]
        result = self.parser.parse_args(command_line_args)
        return vars(result)


    def parse_config_file(self, config_file_path):
        """
        Parse configuration from a YAML configuration file

        Args:
            config_file_path(str): YAML configuration file path

        Returns:
            dict: Configuration options set in configuration file.
                Key is option name, value is option value.
        """
        conf = {}
        with open(config_file_path) as stream:
            conf = yaml.safe_load(stream)
        return conf


    def parse(self, command_line_args=None):
        """
        Parse configuration from a YAML configuration file and command line arguments

        Args:
            command_line_args (tuple): command line arguments. Used only by tests

        Returns:
            dict: Configuration options. Key is option name, value is option value.
        """

        # Parse command line and config file
        # Parse command line first so we can get config file path
        command_line_args = self.parse_command_line_arguments(command_line_args)
        config_file = command_line_args.pop("config_file")
        config_file_options = self.parse_config_file(config_file)
        subcommand = command_line_args.pop("subcommand")

        # Create config with options that apply to the subcommand only
        config = config_file_options["host_os"]
        config.update(config_file_options[subcommand])

        # Add options not present in the config file to the config dict
        config["config_file"] = config_file
        config["subcommand"] = subcommand

        # Parse configuration metadata file
        with open(CONFIG_METADATA_FILE_PATH) as stream:
            config_metadata = yaml.safe_load(stream)

        # Update config node with command line arguments applicable to
        # the subcommand
        for key, value in command_line_args.items():
            if value is None:
                continue
            if key in config:
                target_type = type(
                    config_metadata["options"][key]["default"])
                assert(type(value) == target_type)
                config[key] = value
            else:
                raise Exception("Option {} not applicable to subcommand {}"
                                .format(key, subcommand))

        self._CONF = config
        return config


def setup_default_config():
    """
    Setup the script environment. Parse configurations, setup logging
    and halt execution if anything fails.
    """
    try:
        CONF = get_config().CONF
    except OSError:
        print("Failed to parse settings")
        sys.exit(2)

    log_file_path = os.path.join(CONF.get('work_dir'), LOG_FILE_NAME)
    log_helper.LogHelper(log_file_path=log_file_path,
                         verbose=CONF.get('verbose'),
                         rotate_size=CONF.get('log_size'))

    proxy = CONF.get('http_proxy')
    if proxy:
        utils.set_http_proxy_env(proxy)

    return CONF
