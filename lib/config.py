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

import json
import yaml

from lib import log_helper
from lib import utils

BUILD_REPO_ARGS = {
    ('--packages-metadata-repo-url',):
        dict(help='Packages metadata git repository URL'),
    ('--packages-metadata-repo-branch',):
        dict(help='Packages metadata git repository branch'),
    ('--packages-metadata-repo-target-path',):
        dict(help='Directory to clone the packages metadata git repository. '
             'A subdirectory with the name of the git repository will be created here'),
    ('--http-proxy',):
        dict(help='HTTP proxy URL'),
}
PACKAGE_ARGS = {
    ('--packages', '-p'):
        dict(help='Packages to be built',
             nargs='*'),
    ('--result-dir', '-r'):
        dict(help='Directory to save the RPMs.'),
    ('--packages-repos-target-path', '-R'):
        dict(help='Directory where to clone code repositories'),
    ('--no-update-packages-repos-before-build',):
        dict(help='Update code repositories before building',
             action='store_false', dest='update_packages_repos_before_build'),
    ('--keep-build-dir',):
        dict(help='Keep build directory and its logs and artifacts.',
             action='store_true'),
    ('--force-rebuild',):
        dict(help='Force the rebuild of packages. The default is to only '
             'build packages when they have updated files since the last '
             'build results.',
             action='store_true'),
}
DISTRO_ARGS = {
    ('--distro-name',):
        dict(help='Base Linux distribution'),
    ('--distro-version',):
        dict(help='Base Linux distribution version')
}
MOCK_ARGS = {
    ('--mock-binary',):
        dict(help='Mock binary path'),
    ('--mock-config',):
        dict(help='Mock config file'),
    ('--mock-args',):
        dict(help='Arguments passed to mock command'),
}
RELEASE_NOTES_ARGS = {
    ('--release-notes-repo-url',):
        dict(help='Release notes repository URL'),
    ('--release-notes-repo-branch',):
        dict(help='Branch of the release notes repository to checkout'),
}
PUSH_REPO_ARGS = {
    ('--no-commit-updates',):
        dict(help='Commit file updates to local repository', action='store_false',
             dest='commit_updates'),
    ('--no-push-updates',):
        dict(help='Push file updates to remote repository', action='store_false',
             dest='push_updates'),
    ('--push-repo-url',):
        dict(help='URL of the repository used for pushing'),
    ('--push-repo-branch',):
        dict(help='Branch of the repository used for pushing'),
    ('--updater-name',):
        dict(help='Name used when updating RPM specification files change logs '
             'and creating git commits'),
    ('--updater-email',):
        dict(help='Email used when updating RPM specification files change logs '
             'and creating git commits'),
}
SETUP_ENVIRONMENT_ARGS = {
    ('--user', '-u'):
        dict(help='User login that will run Host OS commands',
             required=True),
}
ISO_ARGS = {
    ('--packages-dir', '-d'):
        dict(help='Directory of packages used in the ISO image.'),
    ('--iso-name',):
        dict(help='ISO name.'),
    ('--log-file',):
        dict(help='ISO name.'),
    ('--automated-install-file',):
        dict(help='Path of a kickstart file, used to automate the installation of a RPM-based Linux distribution'),
    ('--hostos-packages-groups',):
        dict(help='Packages groups in yum repository. Expected format is a dictionary in JSON; key '
                  'is the package group name, value is the list of packages in the package group'),
    ('--automated-install-packages-groups',):
        dict(help='Packages and packages groups which are installed using automated installation', nargs='*'),
    ('--mock-iso-repo-name',):
        dict(help='Name of the yum repository which will be created with OpenPOWER Host OS packages'),
    ('--mock-iso-repo-dir',):
        dict(help='Directory path of the yum repository which will be created with OpenPOWER Host OS packages'),
    ('--distro-repos-urls',):
        dict(help='Base Linux distribution yum repositories URLs'),
}
SUBCOMMANDS = [
    ('build-packages', 'Build packages.',
        [PACKAGE_ARGS, MOCK_ARGS, DISTRO_ARGS, BUILD_REPO_ARGS]),
    ('build-release-notes', 'Create release notes',
        [RELEASE_NOTES_ARGS, PUSH_REPO_ARGS, DISTRO_ARGS, BUILD_REPO_ARGS]),
    ('update-versions', 'Update packages versions',
        [PUSH_REPO_ARGS, DISTRO_ARGS, BUILD_REPO_ARGS]),
    ('update-versions-readme', 'Update the supported software versions table',
        [PUSH_REPO_ARGS, DISTRO_ARGS, BUILD_REPO_ARGS]),
    ('set-env', 'Setup user and directory for build scripts',
        [SETUP_ENVIRONMENT_ARGS]),
    ('build-iso', 'Build ISO image',
        [ISO_ARGS, MOCK_ARGS]),
]


config_parser = None


def get_config():
    global config_parser
    if not config_parser:
        config_parser = ConfigParser()
        config_parser.parse()
    return config_parser


class ConfigParser(object):
    """
    Parses configuration options sources.

    Precedence is:
    command line > config file
    """
    def __init__(self):
        # create the top-level parser
        self.parser = argparse.ArgumentParser()
        self._CONF = None
        self._setup_command_line_parser(SUBCOMMANDS)

    @property
    def CONF(self):
        return self._CONF


    def _setup_command_line_parser(self, subcommands):
        """
        Configures the argument parser object to match the expected
            configuration.

        Args:
            subcommands ([(str, str, [dict])]): subcommands. Each subcommand is
                a tuple with subcommand name, subcommand help message, subcommand arguments.
                Each subcommand argument is a dict from a tuple with argument possible names
                to a dict with argument attributes. See ArgParse documentation for possible
                values in this dict.
        """
        self.parser.add_argument('--config-file', '-c',
                                 help='Path of the configuration file for build '
                                      'scripts',
                                 # NOTE(maurosr): move this to /etc in the future
                                 default='./config.yaml')
        self.parser.add_argument('--log-file', '-l',
                                 help='Log file')
        self.parser.add_argument('--verbose', '-v',
                                 help='Set the scripts to be verbose',
                                 action='store_true')
        self.parser.add_argument('--log-size',
                                 help='Size in bytes above which the log file '
                                 'should rotate', type=int)

        subparsers = self.parser.add_subparsers(
            dest="subcommand",
            help="Available subcommands")
        for command, help_msg, arg_groups in subcommands:
            command_parser = subparsers.add_parser(command, help=help_msg)
            for arg_group in arg_groups:
                for arg, options in arg_group.items():
                    command_parser.add_argument(*arg, **options)

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

        # parse command line and config file
        # parse command line first so we can get config file path
        command_line_args = self.parse_command_line_arguments(command_line_args)
        config_file = command_line_args["config_file"]
        config = self.parse_config_file(config_file)

        # update subcommand config node with command line subcommand arguments
        if command_line_args["subcommand"]:
            node_name = command_line_args["subcommand"].replace("-", "_")
            for key, value in command_line_args.items():
                if key in config[node_name]:
                    if value is not None:
                        if type(config[node_name][key]) == str:
                            config[node_name][key] = value
                        elif type(config[node_name][key]) == dict:
                            config[node_name][key] = json.loads(value)
                    command_line_args.pop(key)
        # update common config node with remaining command line arguments
        node_name = "common"
        for key, value in command_line_args.items():
            if key in config[node_name]:
                if value is not None:
                    if type(config[node_name][key]) == str:
                        config[node_name][key] = value
                    elif type(config[node_name][key]) == dict:
                        config[node_name][key] = json.loads(value)
                command_line_args.pop(key)
        # add subcommand to config
        config["subcommand"] = command_line_args["subcommand"]

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

    log_helper.LogHelper(log_file_path=CONF.get('common').get('log_file'),
                         verbose=CONF.get('common').get('verbose'),
                         rotate_size=CONF.get('common').get('log_size'))

    proxy = CONF.get('common').get('http_proxy')
    if proxy:
        utils.set_http_proxy_env(proxy)

    return CONF
