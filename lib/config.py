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

import yaml

from lib import utils

LOG = logging.getLogger(__name__)


config_parser = None


def get_config():
    global config_parser
    if not config_parser:
        config_parser = ConfigParser()
    return config_parser


class ConfigParser(object):

    def __init__(self):
        cmdline_args = self._parse_arguments()

        self._CONF = self._parse_config(cmdline_args.get('config_file'))

        # NOTE(maurosr): update the config object overwriting its contents with
        # data gathered from cmdline (cmdline precedence > config file's )
        self._CONF.get('default').update(cmdline_args)

    @property
    def CONF(self):
        return self._CONF

    def _parse_config(self, config_file):
        conf = {}
        with open(config_file) as stream:
            conf = yaml.safe_load(stream)
        return conf

    def _parse_arguments(self):
        supported_software = utils.discover_software()
        parser = argparse.ArgumentParser()
        parser.add_argument('--config-file', '-c',
                            help='Path of the configuration file for build '
                                 'scrpits',
                            #NOTE(maurosr): move this to /etc in the future
                            default='./config.yaml')
        parser.add_argument('--packages', '-p',
                            help='Packages to be built',
                            nargs='*',
                            choices=supported_software,
                            default=supported_software)
        parser.add_argument('--log-file', '-l',
                            help='Log file',
                            default='/var/log/host-os/builds.log')
        parser.add_argument('--verbose', '-v',
                            help='Set the scripts to be verbose',
                            action='store_true')
        args = parser.parse_args()
        return vars(args)
