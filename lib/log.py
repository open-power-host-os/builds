import logging


class Log(object):
    def __init__(self, logfile=None, level=logging.DEBUG):
        logging.basicConfig(filename=logfile, level=level)
