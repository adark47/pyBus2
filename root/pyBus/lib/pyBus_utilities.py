# !/usr/bin/python

import os, sys, time, signal, json, logging, traceback
import threading

# This module will read a packet, match it against the json object 'DIRECTIVES' below.
# The packet is checked by matching the source value in packet (i.e. where the packet came from) to a key in the object if possible
# Then matching the Destination if possible
# The joining the 'data' component of the packet and matching that if possible.
# The resulting value will be the name of a function to pass the packet to for processing of sorts.

# THE MAJOR DIFFRENCE BETWEEN THIS DRIVER AND EVENT DRIVER:
# This one should manipulate the state data object and use that with
# a ticking thread to figure out what to do. So tick every .5 sec or
# so and perform an action depending on the state data like skipping
# back or forward.

#####################################
# GLOBALS
#####################################
WRITER = None
STATE_DATA = {}
FUNC_STACK = {}


#####################################
# FUNCTIONS
#####################################
# Set the WRITER object (the iBus interface class) to an instance passed in from the CORE module
def init(writer):
    global WRITER
    logging.info("Initializing the iBus interface for Utilities")
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


# ------------------------------------
# THREAD FOR TICKING AND CHECKING EVENTS
# Calls itself again
# ------------------------------------
def revive(funcName):
    global FUNC_STACK
    funcSpec = FUNC_STACK.get(funcName, None)
    if funcSpec:
        count = funcSpec["COUNT"]
        if count != 1:
            FUNC_STACK[funcName]["COUNT"] = count - 1
            funcSpec["THREAD"].cancel()  # Kill off this thread just in case..
            enableFunc(funcName, funcSpec["INTERVAL"])  # REVIVE!


# ------------------------------------

#####################################
# Functions
#####################################

def lockDoors():
    WRITER.writeBusPacket('3F','00', ['0C', '34', '01'])
    logging.debug("Utilities: Lock doors")


def openTrunk():
    WRITER.writeBusPacket('3F','00', ['0C', '02', '01'])
    logging.debug("Utilities: Open trunk doors")


def windClose(packet):
    global SESSION_DATA
    WRITER.writeBusPacket('3F', '00', ['0C', '53', '01'])           # 3F 05 00 0C 53 01 - Close window 1 - DF
    WRITER.writeBusPacket('3F', '00', ['0C', '55', '01'])           # 3F 05 00 0C 55 01 - Close window 2 - PF

    WRITER.writeBusPacket('3F', '00', ['0C', '42', '01'])           # 3F 05 00 0C 42 01 - Close window 3 - DR
    WRITER.writeBusPacket('3F', '00', ['0C', '43', '01'])           # 3F 05 00 0C 43 01 - Close window 4 - PR
    logging.debug("Utilities: Close window")


def windOpen(packet):
    global SESSION_DATA
    WRITER.writeBusPacket('3F', '00', ['0C', '52', '01'])           # 3F 05 00 0C 52 01 - Open window 1 - DF
    WRITER.writeBusPacket('3F', '00', ['0C', '54', '01'])           # 3F 05 00 0C 54 01 - Open window 2 - PF

#    WRITER.writeBusPacket('3F', '00', ['0C', '41', '01'])          # 3F 05 00 0C 41 01 - Open window 1 - DR
#    WRITER.writeBusPacket('3F', '00', ['0C', '44', '01'])          # 3F 05 00 0C 44 01 - Open window 2 - PR
    logging.debug("Utilities: Open window")


def sunRoofClose(packet):
    global SESSION_DATA
    WRITER.writeBusPacket('3F', '00', ['0C', '7F', '01'])           # 3F 05 00 0C 7F 01 - Sun Roof Close
    logging.debug("Utilities: Sun Roof Close")


def sunRoofOpen(packet):
    global SESSION_DATA
    WRITER.writeBusPacket('3F', '00', ['0C', '7E', '01'])           # 3F 05 00 0C 7E 01 - Sun Roof Open
    logging.debug("Utilities: Sun Roof Open")


def mirrorsFold(packet):
    global SESSION_DATA
    WRITER.writeBusPacket('3F', '00', ['0C', '01', '31', '01'])     # 3F 06 00 0C 01 31 01 - Mirror Fold - D
    WRITER.writeBusPacket('3F', '00', ['0C', '02', '31', '01'])     # 3F 06 00 0C 02 31 01 - Mirror Fold - P
    logging.debug("Utilities: Mirror Fold")


def mirrorsOut(packet):
    global SESSION_DATA
    WRITER.writeBusPacket('3F', '00', ['0C', '01', '30', '01'])     # 3F 06 00 0C 01 30 01 - Mirror Out - D
    WRITER.writeBusPacket('3F', '00', ['0C', '02', '30', '01'])     # 3F 06 00 0C 02 30 01 - Mirror Out - P
    logging.debug("Utilities: Mirror Out")

