#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
import os
import sys
import time
import signal
import logging
from shairportdecoder import decoder
sys.path.append('/root/pyBus/lib/')

############################################################################
# GLOBALS
############################################################################

def main():
  processor = decoder.Processor()
  processor.add_listener(event_processor)
  processor.parse("/tmp/shairport-sync-metadata")

def event_processor(event_type, info):

    assert(isinstance(event_type, info))
    print info
    if event_type == decoder.VOLUME:
        print info.volume
    elif event_type == decoder.META:
        print info.to_simple_string()
    elif event_type == decoder.CLIENT_REMOTE_AVAILABLE:
        print("Got Airplay Remote informations.")

############################################################################
# FUNCTIONS
############################################################################

def init():
    logging.info('Initializing: module AirPlay')


def end():
    logging.info('End: module AirPlay')


def getTrackInfo():
    pass
    # https://github.com/luckydonald/shairport-decoder


############################################################################
# CONTROL
############################################################################

def Play():
    os.system('/bin/echo -ne play | /bin/nc -u localhost 3391 -q 1')
    logging.debug('Through AirPlay sent status: Play')


def Stop():
    os.system('/bin/echo -ne stop | /bin/nc -u localhost 3391 -q 1')
    logging.debug('Through AirPlay sent status: Stop')


def Pause():
    os.system('/bin/echo -ne pause | /bin/nc -u localhost 3391 -q 1')
    logging.debug('Through AirPlay sent status: Pause')


def Next():
    os.system('/bin/echo -ne nextitem | /bin/nc -u localhost 3391 -q 1')
    logging.debug('Through AirPlay sent status: Next')


def Prev():
    os.system('/bin/echo -ne previtem | /bin/nc -u localhost 3391 -q 1')
    logging.debug('Through AirPlay sent status: Prev')


def RewindPrev():
    os.system('/bin/echo -ne beginrew | /bin/nc -u localhost 3391 -q 1')
    logging.debug('Through AirPlay sent status: RewindPrev')


def RewindNext():
    os.system('/bin/echo -ne beginff | /bin/nc -u localhost 3391 -q 1')
    logging.debug('Through AirPlay sent status: RewindNext')


def RewindPlayResume():
    os.system('/bin/echo -ne playresume | /bin/nc -u localhost 3391 -q 1')
    logging.debug('Through AirPlay sent status: PlayResume')


def Random():
    os.system('/bin/echo -ne shuffle_songs | /bin/nc -u localhost 3391 -q 1')
    logging.debug('Through AirPlay sent status: Random')


############################################################################
