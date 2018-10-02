#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import signal
import traceback
import logging
from logging import handlers
import argparse
import gzip
import pyBus_core as core

#####################################
# FUNCTIONS
#####################################
# Manage Ctrl+C gracefully
def signal_handler_quit(signal, frame):
    logging.info('Shutting down pyBus...')
    core.shutdown()
    logging.critical('pyBus shutdown.\n')
    sys.exit(0)



#################################
# LOGGING
#################################

# Convert verbose count in loggin level for the loggin module
def logging_level(verbosity):
    levels = [
        logging.CRITICAL,   # 50
        logging.ERROR,      # 40
        logging.WARNING,    # 30
        logging.INFO,       # 20
        logging.DEBUG       # 10
    ]
    return levels[max(min(len(levels) - 1, verbosity), 0)]

def configureLogging(numeric_level, logfile):
    ## VARIABLES
    format_entry = '%(asctime)s.%(msecs)03d | %(module)-17s [%(levelname)-8s] %(message)s'
    format_date = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(format_entry, format_date)
    log_lvl = logging_level(numeric_level)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Logging to sys.stderr
    consolehandler = logging.StreamHandler(sys.stdout)
    consolehandler.setLevel(log_lvl)
    consolehandler.setFormatter(formatter)
    logger.addHandler(consolehandler)

    # Logging to file is provided
    if logfile:
        # Put the right filename to core.LOGFILE
        core.LOGFILE = logfile
        # Use rotating files : 1 per day, and all are kept (no rotation thus)
        filehandler = handlers.TimedRotatingFileHandler(logfile, when='d', interval=1, backupCount=0)
        filehandler.suffix = "%Y-%m-%d"
        # We can set here different log formats for the stderr output !
        filehandler.setLevel(0)
        # use the same format as the file
        filehandler.setFormatter(formatter)
        # add the handler to the root logger
        logger.addHandler(filehandler)

    logging.info('Logging level set to %s' % (logging_level(numeric_level),))

#################################
# Program options
#################################
def createParser():
    parser = argparse.ArgumentParser(epilog='Free BMW Linux Music Player - Version 1.1', description='This is %(prog)s, the programm to turn a RapsberryPi into an mp3 player for a BMW E46')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increases verbosity of logging (up to -vvvv).')
    parser.add_argument('-d', '--device', action='store', default='/dev/ttyUSB0', help = 'Path to iBus USB interface (Bought from reslers.de)')
    parser.add_argument('-o', '--output_file', action='store', default='', help='Path/Name of log file (log level of 0). If no file specified, output only to std.out')
    return parser

def restart():
    args = sys.argv[:]
    logging.info('Re-spawning %s', ' '.join(args))

    args.insert(0, sys.executable)

    os.chdir(_startup_cwd)
    os.execv(sys.executable, args)

#####################################
# MAIN
#####################################
parser = createParser()
results = parser.parse_args()
loglevel = results.verbose
core.DEVPATH = results.device
_startup_cwd = os.getcwd()

# Manage Ctrl+C
signal.signal(signal.SIGINT, signal_handler_quit)

configureLogging(loglevel, results.output_file)

try:
    logging.critical('pyBus started!')
    core.initialize()
    core.run()
except Exception:
    logging.error('Caught unexpected exception:')
    logging.error(traceback.format_exc())
    logging.info('Going to sleep 2 seconds and restart')
    time.sleep(2)
    restart()

sys.exit(0)
