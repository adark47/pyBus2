# !/usr/bin/python#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
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

############################################################################
# FUNCTIONS
############################################################################

# Set the WRITER object (the iBus interface class) to an instance passed in from the CORE module
def init(writer):
    global WRITER
    logging.info("Initializing the iBus interface for CDChanger")
    WRITER = writer


def shutDown():
    global WRITER
    logging.info("Dereferencing iBus interface")
    WRITER = None


def enableFunc(funcName, interval, count=0):
    global FUNC_STACK

    # Cancel Thread if it already exists.
    if FUNC_STACK.get(funcName) and FUNC_STACK.get(funcName).get("THREAD"):
        FUNC_STACK[funcName]["THREAD"].cancel()

    # Dont worry about checking if a function is already enabled, as the thread would have died. Rather than updating the spec, just run a new thread.
    if getattr(sys.modules[__name__], funcName):
        FUNC_STACK[funcName] = {
            "COUNT": count,
            "INTERVAL": interval,
            "THREAD": threading.Timer(
                interval,
                revive, [funcName]
            )
        }
        logging.debug("Enabling New Thread: %s %s" % (funcName, FUNC_STACK[funcName]))
        worker_func = getattr(sys.modules[__name__], funcName)
        worker_func()
        FUNC_STACK[funcName]["THREAD"].start()
    else:
        logging.warning("No function found (%s)" % funcName)


def disableFunc(funcName):
    global FUNC_STACK
    if funcName in FUNC_STACK.keys():
        thread = FUNC_STACK[funcName].get("THREAD")
        if thread: thread.cancel()
        del FUNC_STACK[funcName]


def disableAllFunc():
    global FUNC_STACK
    for funcName in FUNC_STACK:
        thread = FUNC_STACK[funcName].get("THREAD")
        if thread: thread.cancel()
    FUNC_STACK = {}

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
# CDC Functions
############################################################################

def pollResponse():
    WRITER.writeBusPacket('18', 'FF', ['02', '00'])
    logging.debug('CDC sent the status: Alive')


def announce():
    WRITER.writeBusPacket('18', 'FF', ['02', '01'])
    logging.debug('CDC sent the status: Start')


# General Use: CD title and status when the CD changer is not playing (Status = Pause)
def stop(cdNumber, cdSong):
    WRITER.writeBusPacket('18', '68', ['39', '00', '02', '00', '3F', '00', cdNumber, cdSong])
    logging.debug('CDC sent the status: Stop')


# General Use: Start playing the title (Status = Play)
def pause(cdNumber, cdSong):
    WRITER.writeBusPacket('18', '68', ['39', '01', '09', '00', '3F', '00', cdNumber, cdSong])
    logging.debug('CDC sent the status: Pause')


# General Use: CD title and status if CD changer plays (Status = Play)
def play(cdNumber, cdSong):
    WRITER.writeBusPacket('18', '68', ['39', '02', '09', '00', '3F', '00', cdNumber, cdSong])
    logging.debug('CDC sent the status: Play')


# General Use: Start playing the title
def scanFWD(cdNumber, cdSong):
    WRITER.writeBusPacket('18', '68', ['39', '03', '09', '00', '3F', '00', cdNumber, cdSong])
    logging.debug('CDC sent the status: FFWD')


# General Use: Start playing the title
def scanBWD(cdNumber, cdSong):
    WRITER.writeBusPacket('18', '68', ['39', '04', '09', '00', '3F', '00', cdNumber, cdSong])
    logging.debug('CDC sent the status: FRWD')

def end(cdNumber, cdSong):
    WRITER.writeBusPacket('18', '68', ['39', '07', '02', '00', '3F', '00', cdNumber, cdSong])
    logging.debug('CDC sent the status: End')

def load(cdNumber, cdSong):
    WRITER.writeBusPacket('18', '68', ['39', '08', '02', '00', '3F', '00', cdNumber, cdSong])
    logging.debug('CDC sent the status: Load')

############################################################################