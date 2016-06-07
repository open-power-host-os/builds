import sys

from lib import config
from lib import log


def main(args):
    try:
        conf = config.ConfigParser(args)
    except OSError:
        print("Failed to parse settings")
        return 2

    log.Log(conf.config.get('log_file'))

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
