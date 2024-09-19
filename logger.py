import logging


class MyLogger(object):
    def debug(self, msg):
        logging.debug(msg)

    def info(self, msg):
        logging.info(msg)

    def warning(self, msg):
        logging.warning(msg)

    def error(self, msg):
        logging.warning(msg)

    def fatal(self, msg):
        logging.fatal(msg)
