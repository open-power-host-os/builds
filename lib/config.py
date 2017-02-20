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

LOG_FILE_NAME = 'builds.log'
RAW_TEXT_ID = "R|"
BUILD_REPO_ARGS = {
    ('--packages-metadata-repo-url',):
        dict(help='Packages metadata git repository URL'),
    ('--packages-metadata-repo-branch',):
        dict(help='Packages metadata git repository branch'),
    ('--packages-metadata-repo-refspecs',):
        dict(help='Packages metadata git repository refspecs to fetch. Refer '
             'to https://git-scm.com/book/id/v2/Git-Internals-The-Refspec',
             nargs='*'),
    ('--http-proxy',):
        dict(help='HTTP proxy URL'),
}
PACKAGE_ARGS = {
    ('--packages', '-p'):
        dict(help=RAW_TEXT_ID + "Packages to be built. Each package option may have several\n"
           "fields, separated by `#` character, and the expected format can\n"
           "be one of the following:\n\n"
           "package_name#repo_url#branch_name#revision_id (SVN source only)\n"
           "package_name#repo_url#reference (Git/Mercurial source only)\n"
           "package_name##reference (Git/Mercurial source only)\n"
           "package_name\n\n"
        "The fields after package name override the corresponding data in the\n"
        "first source of the package YAML.",
             nargs='*'),
}
PACKAGE_BUILD_ARGS = {
    ('--no-update-packages-repos-before-build',):
        dict(help='Do not update code repositories before building',
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
        dict(help='Mock binary path', default='/usr/bin/mock'),
    ('--mock-config',):
        dict(help='Mock config file'),
    ('--mock-args',):
        dict(help='Arguments passed to mock command', default=''),
}
PUNGI_ARGS = {
    ('--pungi-binary',): dict(help='Pungi binary path'),
    ('--pungi-args',): dict(help='Arguments passed to pungi command'),
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
        dict(help='Branch of the repository used for pushing',
             default='master'),
    ('--updater-name',):
        dict(help='Name used when updating RPM specification files change logs '
             'and creating git commits'),
    ('--updater-email',):
        dict(help='Email used when updating RPM specification files change logs '
             'and creating git commits'),
}
BUILD_ARGS = {
    ('--result-dir', '-r'):
        dict(help='Directory to save the results.',
             default='result'),
}
ISO_ARGS = {
    ('--packages-dir', '-d'):
        dict(help='Directory of packages used in the ISO image.',
             default='result/packages/latest'),
    ('--iso-name',):
        dict(help='ISO name.',
             default='OpenPOWER-Host_OS'),
    ('--automated-install-file',):
        dict(help='Path of a kickstart file, used to automate the installation of a RPM-based Linux distribution',
             default='host-os.ks'),
    ('--installable-environments',):
        dict(help='Those environments will be available at the "Sofware '
             'selection" screen, along with the ones that come from the base '
             'distro (e.g. CentOS) repository. They will contain a group with '
             'the same name, that will in turn contain the packages listed. '
             'Those groups must be available in the ISO yum repository in '
             'order to show up.'),
    ('--iso-repo-packages-groups',):
        dict(help='Packages groups that will be available in the ISO yum '
             'repository, in addition to the ones required by a minimal '
             'installation of the base distro.', nargs='*'),
    ('--iso-repo-packages',):
        dict(help='Packages that will be available in the ISO yum '
             'repository, in addition to the ones required by a minimal '
             'installation of the base distro.', nargs='*'),
    ('--mock-iso-repo-name',):
        dict(help='Name of the yum repository, to create from OpenPOWER Host OS packages'),
    ('--mock-iso-repo-dir',):
        dict(help='Directory path of the yum repository, to create from OpenPOWER Host OS packages'),
    ('--distro-repos-urls',):
        dict(help='Base Linux distribution yum repositories URLs'),
}
SUBCOMMANDS = [
    ('build-packages', 'Build packages.',
        [PACKAGE_ARGS, PACKAGE_BUILD_ARGS, MOCK_ARGS, DISTRO_ARGS, BUILD_REPO_ARGS, BUILD_ARGS]),
    ('build-release-notes', 'Create release notes',
        [RELEASE_NOTES_ARGS, PUSH_REPO_ARGS, DISTRO_ARGS, BUILD_REPO_ARGS]),
    ('update-versions', 'Update packages versions',
        [PACKAGE_ARGS, PUSH_REPO_ARGS, DISTRO_ARGS, BUILD_REPO_ARGS]),
    ('update-metapackage', 'Update the metapackage dependencies',
        [PUSH_REPO_ARGS, DISTRO_ARGS, BUILD_REPO_ARGS]),
    ('update-versions-readme', 'Update the supported software versions table',
        [PUSH_REPO_ARGS, DISTRO_ARGS, BUILD_REPO_ARGS]),
    ('build-iso', 'Build ISO image',
        [ISO_ARGS, MOCK_ARGS, PUNGI_ARGS, BUILD_ARGS]),
]


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
    cmdline > config file > argparse defaults
    """
    def __init__(self):
        # create the top-level parser
        self.parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
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
                                 default='config/host_os.yaml')
        self.parser.add_argument('--verbose', '-v',
                                 help='Set the scripts to be verbose',
                                 action='store_true')
        self.parser.add_argument('--log-size',
                                 help='Size in bytes above which the log file '
                                 'should rotate', type=int, default=2<<20)
        self.parser.add_argument('--work-dir', '-w',
                                 help='Directory used to store all temporary '
                                 'files created during the process.',
                                 default='workspace')

        subparsers = self.parser.add_subparsers(
            dest="subcommand",
            help="Available subcommands")
        for command, help_msg, arg_groups in subcommands:
            command_parser = subparsers.add_parser(command, help=help_msg,
                                                   formatter_class=CustomHelpFormatter)
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

        # Parse command line and config file
        # Parse command line first so we can get config file path
        command_line_args = self.parse_command_line_arguments(command_line_args)
        config_file = command_line_args.pop("config_file")
        config = self.parse_config_file(config_file)
        subcommand = command_line_args.pop("subcommand")

        # Add options not present in the config file to the config dict
        config["common"]["config_file"] = config_file
        config["common"]["subcommand"] = subcommand

        # Update config node with command line arguments applicable to
        # the subcommand
        subcommand_node_name = subcommand.replace("-", "_")
        for key, value in command_line_args.items():
            if value is None:
                continue
            for node_name in ["common", subcommand_node_name]:
                if key in config[node_name]:
                    config[node_name][key] = value
                    break
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

    log_file_path = os.path.join(CONF.get('common').get('work_dir'),
                                 LOG_FILE_NAME)
    log_helper.LogHelper(log_file_path=log_file_path,
                         verbose=CONF.get('common').get('verbose'),
                         rotate_size=CONF.get('common').get('log_size'))

    proxy = CONF.get('common').get('http_proxy')
    if proxy:
        utils.set_http_proxy_env(proxy)

    return CONF
