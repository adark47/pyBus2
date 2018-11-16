# !/usr/bin/python#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import string
import time
import signal
import json
import logging
import traceback
import threading

############################################################################
# GLOBALS
############################################################################

WRITER = None
STATE_DATA = {}
FUNC_STACK = {}
leadTime = None


############################################################################
# FUNCTIONS
############################################################################

# Set the WRITER object (the iBus interface class) to an instance passed in from the CORE module
def init(writer):
    global WRITER
    logging.info('Initializing: the iBus TEL')
    WRITER = writer


def shutDown():
    global WRITER
    logging.info('End: iBus TEL')
    WRITER = None


def enableFunc(funcName, interval, count=0):
    global FUNC_STACK

    # Cancel Thread if it already exists.
    if FUNC_STACK.get(funcName) and FUNC_STACK.get(funcName).get('THREAD'):
        FUNC_STACK[funcName]['THREAD'].cancel()

    # Dont worry about checking if a function is already enabled, as the thread would have died. Rather than updating the spec, just run a new thread.
    if getattr(sys.modules[__name__], funcName):
        FUNC_STACK[funcName] = {
            'COUNT': count,
            'INTERVAL': interval,
            'THREAD': threading.Timer(
                interval,
                revive, [funcName]
            )
        }
        logging.debug('Enabling New Thread: %s %s', funcName, FUNC_STACK[funcName])
        worker_func = getattr(sys.modules[__name__], funcName)
        worker_func()
        FUNC_STACK[funcName]['THREAD'].start()
    else:
        logging.warning('No function found (%s)', funcName)


def disableFunc(funcName):
    global FUNC_STACK
    if funcName in FUNC_STACK.keys():
        thread = FUNC_STACK[funcName].get('THREAD')
        if thread: thread.cancel()
        del FUNC_STACK[funcName]


def disableAllFunc():
    global FUNC_STACK
    for funcName in FUNC_STACK:
        thread = FUNC_STACK[funcName].get('THREAD')
        if thread: thread.cancel()
    FUNC_STACK = {}


def timePollResponse(difference):
    global leadTime
    leadTimeNow = datetime.datetime.now()
    if leadTime is None:
        leadTime = leadTimeNow
        return True
    else:
        lead = leadTimeNow - leadTime
        leadTime = leadTimeNow
        timeDifference = divmod(lead.days * 86400 + lead.seconds, 60)
        if timeDifference[0] > 0 or timeDifference[1] > difference:
            logging.warning('Time difference on request - %s', timeDifference)
            return False
        else:
            logging.debug('Time difference on request - %s', timeDifference)
            return True


############################################################################
# THREAD FOR TICKING AND CHECKING EVENTS
# Calls itself again
############################################################################

def revive(funcName):
    global FUNC_STACK
    funcSpec = FUNC_STACK.get(funcName, None)
    if funcSpec:
        count = funcSpec['COUNT']
        if count != 1:
            FUNC_STACK[funcName]['COUNT'] = count - 1
            funcSpec['THREAD'].cancel()  # Kill off this thread just in case..
            enableFunc(funcName, funcSpec['INTERVAL'])  # REVIVE!


############################################################################
# TEL Functions
############################################################################
# https://github.com/kmalinich/node-bmw-client/blob/master/modules/TEL.js

def pollResponse():
    WRITER.writeBusPacket('C8', 'FF', ['02', '00'])
    logging.debug('TEL sent the status: Alive')

############################################################################

def announce():
    WRITER.writeBusPacket('C8', 'FF', ['02', '01'])
    logging.debug('TEL sent the status: Start')

def ledAllOff():
    WRITER.writeBusPacket('C8', 'E7', ['2B', '00'])         # Telephone LED All_off         # C8 E7 2B 00
    logging.debug('TEL sent the status: LED all off')

def ledRedSolid():
    WRITER.writeBusPacket('C8', 'E7', ['2B', '01'])         # Telephone LED red, solid      # C8 E7 2B 01
    logging.debug('TEL sent the status: LED red, solid')

def ledRedFlash ():
    WRITER.writeBusPacket('C8', 'E7', ['2B', '02'])         # Telephone LED red, flash      # C8 E7 2B 02
    logging.debug('TEL sent the status: LED red, flash')

def ledYellowSolid():
    WRITER.writeBusPacket('C8', 'E7', ['2B', '04'])         # Telephone LED yellow, solid   # C8 E7 2B 04
    logging.debug('TEL sent the status: LED yellow, solid')

def ledYellowFlash():
    WRITER.writeBusPacket('C8', 'E7', ['2B', '08'])         # Telephone LED yellow, flash   # C8 E7 2B 08
    logging.debug('TEL sent the status: LED yellow, flash')

def ledGreenSolid():
    WRITER.writeBusPacket('C8', 'E7', ['2B', '10'])         # Telephone LED green, solid    # C8 E7 2B 10
    logging.debug('TEL sent the status: LED green, solid')

def ledGreenFlash():
    WRITER.writeBusPacket('C8', 'E7', ['2B', '20'])         # Telephone LED green, flash    # C8 E7 2B 20
    logging.debug('TEL sent the status: LED green, flash')

############################################################################

def handsfree():
    WRITER.writeBusPacket('C8', 'E7', ['2С', '01'])         # Handsfree                     # C8 E7 2C 01
    logging.debug('TEL sent the status: Handsfree')

def activeCall():
    WRITER.writeBusPacket('C8', 'E7', ['2С', '02'])  # Active call (false = phone menu displayed) #  C8 E7 2C 02
    logging.debug('TEL sent the status: Active call (false = phone menu displayed)')

def incomingCall():
    WRITER.writeBusPacket('C8', 'E7', ['2С', '04'])         # Incoming call                 # C8 E7 2C 04
    logging.debug('TEL sent the status: Incoming call')

def screenDisabled():
    WRITER.writeBusPacket('C8', 'E7', ['2С', '08'])         # Phone screen disabled         # C8 E7 2C 08
    logging.debug('TEL sent the status: Phone screen disabled')

def phoneOn():
    WRITER.writeBusPacket('C8', 'E7', ['2С', '10'])         # Phone on                      # C8 E7 2C 10
    logging.debug('TEL sent the status: Phone on ')

def phoneActive():
    WRITER.writeBusPacket('C8', 'E7', ['2С', '20'])         # Phone active                  # C8 E7 2C 20
    logging.debug('TEL sent the status: Phone active')

def phonedInstalled ():
    WRITER.writeBusPacket('C8', 'E7', ['2С', '40'])         # Phone adapter installed       # C8 E7 2C 40
    logging.debug('TEL sent the status: Phone adapter installed ')

############################################################################
