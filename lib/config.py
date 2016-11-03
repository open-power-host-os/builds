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
import logging
import os
import sys

import yaml

LOG = logging.getLogger(__name__)

config_parser = None


def get_config():
    global config_parser
    if not config_parser:
        config_parser = ConfigParser()
        config_parser.parse()
    return config_parser


def discover_software():
    """
    Simple mechanism for discoverability of the software we build.

    A discoverable software, and thus potentially buildable, will be assume as
    any directory name under SOFTWARE_DIRECTORY containing a yaml file with
    the same name.
    Considering the example:

    components
    +-- kernel
    |   +-- kernel.yaml
    +-- libvirt
    |   +-- libvirt.yaml
    |   +-- someother_file_or_directory
    +-- not-a-software
    |   +-- not-following-standards.yaml
    +-- file

    "kernel" and "libvirt" will be discovered, "not-a-software" and "file"
    will not.
    """
    build_versions_repo_dir = get_config().CONF.get('default').get(
        'build_versions_repo_dir')
    software_list = []
    try:
        software_list = [
            software for software in os.listdir(build_versions_repo_dir)
            if os.path.isdir(os.path.join(build_versions_repo_dir, software)) and
            os.path.isfile(os.path.join(build_versions_repo_dir, software,
                                        "".join([software, ".yaml"])))
        ]
    except OSError:
        # This is expected to happen on the first run, when the build
        # versions directory doesn't exist yet.
        pass
    finally:
        return software_list


class ConfigParser(object):
    """
    Parses configuration options sources.

    Precedence is:
    cmdline > config file > argparse defaults
    """
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self._CONF = None
        self._setup_config_parser_options()

    @property
    def CONF(self):
        return self._CONF

    def _setup_config_parser_options(self):
        """
        Configures the argument parser object to match the expected
            configuration.
        """
        self.parser.add_argument('--config-file', '-c',
                                 help='Path of the configuration file for build '
                                      'scripts',
                                 # NOTE(maurosr): move this to /etc in the future
                                 default='./config.yaml')
        self.parser.add_argument('--packages', '-p',
                                 help='Packages to be built',
                                 nargs='*')
        self.parser.add_argument('--log-file', '-l',
                                 help='Log file',
                                 default='/var/log/host-os/builds.log')
        self.parser.add_argument('--verbose', '-v',
                                 help='Set the scripts to be verbose',
                                 action='store_true')
        self.parser.add_argument('--result-dir', '-r',
                                 help='Directory to save the RPMs.',
                                 default='./result')
        self.parser.add_argument('--repositories-path', '-R',
                                 help='Directory where to clone code repositories',
                                 default='/var/lib/host-os/repositories')
        self.parser.add_argument('--keep-builddir',
                                 help='Keep build directory and its logs and '
                                 'artifacts.', action='store_true')
        self.parser.add_argument('--build-versions-repository-url',
                                 help='Build versions repository URL')
        self.parser.add_argument('--build-version',
                                 help='Select build version from versions '
                                 'repository')
        self.parser.add_argument('--build-versions-repo-dir',
                                 help='Directory to clone the build versions '
                                 'repository',
                                 default='./components')
        self.parser.add_argument('--log-size',
                                 help='Size in bytes above which the log file '
                                 'should rotate', type=int)

    def parse_arguments_list(self, args):
        """
        Parses the arguments provided in the argument list and returns
            the result object.
        """
        result = self.parser.parse_args(args)
        return vars(result)

    def parse_config_file(self, config_file_path):
        """
        Parse the configuration file and return a dictionary containing the
            parsed values.
        """
        conf = {}
        with open(config_file_path) as stream:
            conf = yaml.safe_load(stream)
        return conf

    def parse(self):
        # parse the 'config-file' argument early so that we can use
        # the defaults defined in the config file to override the ones
        # in the 'add_argument' calls below.
        config_file = self.parser.parse_known_args()[0].config_file

        config = self.parse_config_file(config_file)
        self.parser.set_defaults(**config['default'])

        args = self.parse_arguments_list(sys.argv[1:])

        # drop None values
        for key, value in args.items():
            if not value:
                args.pop(key)

        config['default'].update(args)
        self._CONF = config
        return config
