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

import json
import yaml

from lib import log_helper
from lib import utils


RAW_TEXT_ID = "R|"
CONFIG_METADATA_FILE_PATH = "config_metadata.yaml"
LOG_FILE_NAME = 'builds.log'

config_parser = None


def get_config():
    global config_parser
    if not config_parser:
        config_parser = ConfigParser()
        config_parser.parse()
    return config_parser

# disable argument abbreviation in Python's ArgumentParser class
class ArgumentParserWithoutAbbrev(argparse.ArgumentParser):
    def _get_option_tuples(self, option_string):
        return []

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
        self.parser = ArgumentParserWithoutAbbrev(formatter_class=CustomHelpFormatter)
        self._CONF = None
        self._setup_command_line_parser(CONFIG_METADATA_FILE_PATH)

    @property
    def CONF(self):
        return self._CONF


    def _setup_command_line_arg_from_config_metadata(self, section, attribute, target_parser):

        argument = attribute.replace("_", "-")
        argument_default = section[attribute]["default"]
        argument_type = type(argument_default)
        argument_help = section[attribute]["help"]
        action = "store"
        argument = "--%s" % argument
        keyword_args = {"help": argument_help}
        if argument_type is bool:
            if bool(argument_default):
                argument = "--no-%s" % argument[2:]
                action = "store_false"
            else:
                action= "store_true"
        elif argument_type is list:
            keyword_args["nargs"] = "*"
        keyword_args["action"] = action
        keyword_args["dest"] = attribute
        target_parser.add_argument(argument, **keyword_args)


    def _setup_command_line_parser(self, config_metadata_file_path):
        """
        Configures the argument parser object to match the expected
            configuration.

        Args:
            config_metadata_file_path (str): config metadata file path
        """
        self.parser.add_argument('--config-file', '-c',
                                 help='Path of the configuration file for build '
                                      'scripts',
                                 default='./config.yaml')

        subparsers = self.parser.add_subparsers(
            dest="subcommand",
            help="Available subcommands")
        _subparsers = {}

        # setup parser from config metadata file
        with open(config_metadata_file_path) as fh:
            config_metadata = yaml.safe_load(fh)
        for section in config_metadata:
            if section == "common":
                continue
            command = section.replace("_", "-")
            command_help = config_metadata[section]["help"]
            config_metadata[section].pop("help")
            _subparsers[command] = subparsers.add_parser(command, help=command_help,
                                                         formatter_class=CustomHelpFormatter)
            target_parser = _subparsers[command]
            for attribute in config_metadata[section]:
                if attribute == "help":
                    continue
                self._setup_command_line_arg_from_config_metadata(config_metadata[section], attribute, target_parser)
        section = "common"
        for attribute in config_metadata[section]:
            if attribute == "help":
                continue
            if "target_subcommands" in config_metadata[section][attribute]:
                for command in config_metadata[section][attribute]["target_subcommands"]:
                    self._setup_command_line_arg_from_config_metadata(config_metadata[section], attribute, _subparsers[command])
            else:
                self._setup_command_line_arg_from_config_metadata(config_metadata[section], attribute, self.parser)


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


    def parse_value_from_str(self, value, _type):

        if _type == str or _type == bool or _type == list:
            return value
        # argparse does not have a mechanism to convert a str to a dict,
        # so we must do it manually
        elif _type == dict:
            return json.loads(value)
        else:
            raise Exception("Unexpected type %s in value %s" % (_type, value))

    def parse(self, command_line_args=None):
        """
        Parse configuration from a YAML configuration file and command line arguments

        Args:
            command_line_args (tuple): command line arguments. Used only by tests

        Returns:
            dict: Configuration options. Key is option name, value is option value.
        """

        print("ConfigParser::parse(), cmd line args: %s" % command_line_args)

        # parse command line and config file
        # parse command line first so we can get config file path
        command_line_args = self.parse_command_line_arguments(command_line_args)
        print("ConfigParser::parse(), cmd line args 2: %s" % command_line_args)
        config_file = command_line_args["config_file"]
        config = self.parse_config_file(config_file)

        # parse config metadata file
        CONFIG_METADATA_FILE_PATH = "config_metadata.yaml"
        with open(CONFIG_METADATA_FILE_PATH) as stream:
            config_metadata = yaml.safe_load(stream)

        # update subcommand and common config nodes with command line subcommand arguments
        if command_line_args["subcommand"]:
            command_node_name = command_line_args["subcommand"].replace("-", "_")
            for key, value in command_line_args.items():
                if key in config[command_node_name] or key in config["common"]:
                    if value is not None:
                        if key in config["common"]:
                            node_name = "common"
                        else:
                            node_name = command_node_name
                        parsed_value = self.parse_value_from_str(value, type(config_metadata[node_name][key]["default"]))
                        config[node_name][key] = parsed_value
                    command_line_args.pop(key)
        # add the only argument which is defined in command line, but does not
        # exist in config file
        key = "config_file"
        if key in command_line_args:
            config["common"][key] = command_line_args[key]
            command_line_args.pop(key)
        # remove all configs which are not common and not subcommand-specific
        for key, value in config.items():
            command_node = command_line_args["subcommand"].replace("-", "_")
            if key != command_node and key != "common":
                del config[key]
        # add subcommand (automatically defined by argparse) to config
        config["subcommand"] = command_line_args["subcommand"]
        command_line_args.pop("subcommand")

        if command_line_args:
            raise Exception("options %s were not parsed from command line" % command_line_args.keys())

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

    log_file_path = os.path.join(CONF.get('common').get('work_dir'),
                                 LOG_FILE_NAME)
    log_helper.LogHelper(log_file_path=log_file_path,
                         verbose=CONF.get('common').get('verbose'),
                         rotate_size=CONF.get('common').get('log_size'))

    proxy = CONF.get('common').get('http_proxy')
    if proxy:
        utils.set_http_proxy_env(proxy)

    return CONF
