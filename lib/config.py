
import argparse
import logging
import yaml

import utils

LOG = logging.getLogger(__name__)


class ConfigParser(object):

    def __init__(self, argv):
        cmdline_args = self._parse_arguments(argv)
        self.config = self._parse_config(cmdline_args.get('config_file'))

        # NOTE(maurosr): update the config object overwriting its contents with
        # data gathered from cmdline (cmdline precedence > config file's )
        self.config.get('default').update(cmdline_args)

    def _parse_config(self, config_file):
        conf = {}
        with open(config_file) as stream:
            conf = yaml.safe_load(stream)
        return conf

    def _parse_arguments(self, argv):
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
        args = parser.parse_args()
        return vars(args)
