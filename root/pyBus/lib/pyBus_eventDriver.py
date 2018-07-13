#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import signal
import random
import logging
import traceback
from subprocess import Popen, PIPE
sys.path.append('/root/pyBus/lib/')

# Imports for the project
import pyBus_module_display as pB_display     # Only events can manipulate the display stack
import pyBus_module_audio2 as pB_audio         # Add the audio module as it will only be manipulated from here in pyBus
import pyBus_utilities as pB_util
import pyBus_cdc as pB_cdc
#import pyBus_ioMK4 as io

# This module will read a packet, match it against the json object 'DIRECTIVES' below.
# The packet is checked by matching the source value in packet (i.e. where the packet came from) to a key in the object if possible
# Then matching the Destination if possible
# The joining the 'data' component of the packet and matching that if possible.
# The resulting value will be the name of a function to pass the packet to for processing of sorts.

############################################################################
# GLOBALS DIRECTIVES
############################################################################
# directives list - maps function to src:dest:data
# first level of directives is filtering the src, so put in the integer representation of the src
# second level is destination
# third level is data : function name

DIRECTIVES = {
#    '00': {
#        'BF': {
#            '0200B9': '',                       # Unlocked via key
#            '7212DB': '',                       # Locked via key
#            '7A1000': '',                       # passenger door opened, probably
#            '7A5202': '',                       # passenger door closed, probably
#            '7A5020': '',                       # driver window popped up after closing door
#            '7A5021': '',                       # driver door closed
#            '7A5120': '',                       # driver window popped down before opening door
#            '7A5121': '',                       # driver door opened
#        }
#    },
#    '3F': {
#        '00': {
#            '0C3401': '',                       # All doors unlocked
#            '0C4601': '',                       # Passenger Door Locked
#            '0C4701': '',                       # Driver Door Locked
#        }
#    },
#    '44': {
#        'BF': {
#            '7401FF': '',                       # key position 1
#            '740401': '',                       # key
#            '7400FF': ''                        # key removed
#        }
#    },
#    'C0': {
#        '68': {
#            '3100000B': '',                     # Mode button pressed
#            '3100134B': '',                     # Mode button released
#        }
#    },
    '80': {
        'BF': {
            'ALL': 'd_custom_IKE'               # Use ALL to send all data to a particular function
        }
    },
    '68': {                                     # CD53
        '18': {
            '01':     'd_cdPollResponse',       # "I'm alive" message
            '380000': 'd_cdStatusPlaying',      # 68 05 18 38 00 00 - CD status Req
            '380100': 'd_cdStop',               # 68 05 18 38 01 00 - Stop press
            '380300': 'd_cdPlay',               # 68 05 18 38 03 00 - Play press
            '380A00': 'd_cdNext',               # 68 05 18 38 0A 00 - Skip forward
            '380A01': 'd_cdPrev',               # 68 05 18 38 0A 01 - Skip Backward
#            '380700': '',                       # 68 05 18 38 07 00 - Scan Off press
#            '380701': '',                       # 68 05 18 38 07 01 - Scan On press
            '380601': 'd_cdPlay',               # 68 05 18 38 06 01 - CD Button 1 press
            '380602': 'd_cdStop',               # 68 05 18 38 06 02 - CD Button 2 press
#            '380603': '',                       # 68 05 18 38 06 03 - CD Button 3 press
#            '380604': '',                       # 68 05 18 38 06 04 - CD Button 4 press
#            '380605': '',                       # 68 05 18 38 06 05 - CD Button 5 press
#            '380606': '',                       # 68 05 18 38 06 06 - CD Button 6 press
#            '380400': '',                       # 68 05 18 38 04 00 - Fast Rwd press
#            '380401': '',                       # 68 05 18 38 04 01 - Fast Fwd press
#            '380800': 'd_cdRandom',             # 68 05 18 38 08 00 - Random Off press
#            '380801': 'd_cdRandom'              # 68 05 18 38 08 01 - Random On press
        }
    },
    'F0': {                                     # MK4
        '68':{
#            '4807': '',                         # F0 05 68 48 07 - Info press
#            '4844': '',                         # F0 05 68 48 44 - Info hold
#            '4887': '',                         # F0 05 68 48 87 - Info released
            '4811': 'button1p',                 # F0 04 68 48 11 - Button 1 press
#            '4851': '',                         # F0 04 68 48 51 - Button 1 hold
#            '4891': '',                         # F0 05 68 48 91 - Button 1 released
            '4801': 'button2p',                 # F0 04 68 48 01 - Button 2 press
#            '4841': '',                         # F0 04 68 48 41 - Button 2 hold
#            '4881': '',                         # F0 05 68 48 81 - Button 2 released
            '4812': 'button3p',                 # F0 04 68 48 12 - Button 3 press
#            '4852': '',                         # F0 04 68 48 52 - Button 3 hold
#            '4892': '',                         # F0 05 68 48 92 - Button 3 released
            '4802': 'button4p',                 # F0 04 68 48 02 - Button 4 press
#            '4842': '',                         # F0 04 68 48 42 - Button 4 hold
#            '4882': '',                         # F0 05 68 48 82 - Button 4 released
            '4813': 'button5p',                 # F0 04 68 48 13 - Button 5 press
#            '4853': '',                         # F0 04 68 48 53 - Button 5 hold
#            '4893': '',                         # F0 05 68 48 93 - Button 5 released
            '4803': 'button6p',                 # F0 04 68 48 03 - Button 6 press
#            '4843': '',                         # F0 04 68 48 43 - Button 6 hold
#            '4883': '',                         # F0 05 68 48 83 - Button 6 released
#            '4810': '',                         # F0 04 68 48 10 - "<" ArrowLeft press
#            '4850': '',                         # F0 04 68 48 50 - "<" ArrowLeft hold
#            '4890': '',                         # F0 05 68 48 90 - "<" ArrowLeft released
#            '4800': '',                         # F0 04 68 48 00 - ">" ArrowRight press
#            '4840': '',                         # F0 04 68 48 40 - ">" ArrowRight hold
#            '4880': '',                         # F0 05 68 48 80 - ">" ArrowRight released
#            '4814': '',                         # F0 04 68 48 14 - "<>" Arrow press
#            '4854': '',                         # F0 04 68 48 54 - "<>" Arrow hold
#            '4894': '',                         # F0 05 68 48 94 - "<>" Arrow released
#            '4823': '',                         # F0 04 68 48 23 - MODE press
#            '4863': '',                         # F0 04 68 48 63 - MODE hold
#            '48A3':''                           # F0 05 68 48 A3 - MODE released
#        },
#        '3B':{
#            '4981': '',                         # F0 04 3B 49 81 - right nob Left turn
#            '4901': '',                         # F0 04 3B 49 01 - right nob Right turn
#
#            '4805': '',                         # F0 04 3B 48 05 - right nob push
#            '4845': '',                         # F0 04 3B 48 45 - right nob hold
#            '4885': ''                          # F0 04 3B 48 85 - right nob released
        }

    },
    '3B': {                                     # MK4 - Index fields
        '68': {
            '23623040': 'slctIndexF0',          # 3B 06 68 23 62 30 40 - selected Index fields 0
            '23623041': 'slctIndexF1',          # 3B 06 68 23 62 30 41 - selected Index fields 1
            '23623042': 'slctIndexF2',          # 3B 06 68 23 62 30 42 - selected Index fields 2
            '23623043': 'slctIndexF3',          # 3B 06 68 23 62 30 43 - selected Index fields 3
            '23623044': 'slctIndexF4',          # 3B 06 68 23 62 30 44 - selected Index fields 4
            '23623045': 'slctIndexF5',          # 3B 06 68 23 62 30 45 - selected Index fields 5
            '23623046': 'slctIndexF6',          # 3B 06 68 23 62 30 46 - selected Index fields 6
            '23623047': 'slctIndexF7',          # 3B 06 68 23 62 30 47 - selected Index fields 7
            '23623048': 'slctIndexF8',          # 3B 06 68 23 62 30 48 - selected Index fields 8
            '23623049': 'slctIndexF9'           # 3B 06 68 23 62 30 49 - selected Index fields 9

        }
    },
    '50': {
        'C8': {                                 # Multifunction steering wheel phone buttons
            '01':   'd_cdPollResponse',         # This can happen via RT button or ignition
#            '3B40': '',                         # 50 04 C8 3B 40    - R/T
#            '3B80': '',                         # 50 04 C8 3B 80 27 - voice press
#            '3B90': '',                         # 50 04 C8 3B 90 37 - voice hold
#            '3BA0': ''                          # 50 04 C8 3B A0 07 - voice release
        },
        '68': {                                 # Multifunction steering wheel buttons
            '3211': '',                         # 50 04 68 32 11 1F - "+" press
            '3210': '',                         # 50 04 68 32 10 1E - "-" press
            '3B01': '',                         # 50 04 68 3B 01 06 - ">" press
            '3B11': '',                         # 50 04 68 3B 11 16 - ">" hold
            '3B21': '',                         # 50 04 68 3B 21 26 - ">" release
            '3B08': '',                         # 50 04 68 3B 08 0F - "<" press
            '3B18': '',                         # 50 04 68 3B 18 1F - "<" hold
            '3B28': ''                          # 50 04 68 3B 28 2F - "<" release
        }
    }
}

############################################################################
# CONFIG
############################################################################

WRITER = None
SESSION_DATA = {}
#TICK = 0.02 # sleep interval in seconds used between iBUS reads
TICK = 0.1

MENU_LEVEL = None

############################################################################
# FUNCTIONS
############################################################################
# Set the WRITER object (the iBus interface class) to an instance passed in from the CORE module

def init(writer):
    global WRITER, SESSION_DATA
    WRITER = writer

    #pB_display.init(WRITER)
    pB_audio.init()
    pB_cdc.init(WRITER)
    pB_util.init(WRITER)

#    WRITER.writeBusPacket('18', 'FF', ['02', '01'])
#    logging.debug("CDC sent the status: Start")
    pB_cdc.enableFunc("announce", 10)

# Manage the packet, meaning traverse the JSON 'DIRECTIVES' object and attempt to determine a suitable function to pass the packet to.
def manage(packet):
    src = packet['src']
    dst = packet['dst']
    dataString = ''.join(packet['dat'])
    methodName = None

    try:
        dstDir = DIRECTIVES[src][dst]
        if ('ALL'    in dstDir.keys()):
            methodName = dstDir['ALL']
        else:
            methodName = dstDir[dataString]
    except Exception, e:
        pass

    result = None
    if methodName != None:
        methodToCall = globals().get(methodName, None)
        if methodToCall:
            logging.debug("Directive found for packet - %s" % methodName)
            try:
                result = methodToCall(packet)
            except:
                logging.error("Exception raised from [%s]" % methodName)
                logging.error(traceback.format_exc())

        else:
            logging.debug("Method (%s) does not exist" % methodName)
    else:
        logging.debug("MethodName (%s) does not match a function" % methodName)

    return result


def listen():
    logging.info('Event listener initialized')
    while True:
        packet = WRITER.readBusPacket()
        if packet:
            manage(packet)
        time.sleep(TICK) # sleep a bit


def shutDown():
    logging.debug("Quitting Audio CLIENT")
    pB_audio.quit()
    logging.debug("Stopping Display Driver")
#    pB_display.end()
    logging.debug("Killing CDC")
    pB_cdc.shutDown()
    logging.debug("Killing Utilities")
    pB_cdc.shutDown()


############################################################################
# FROM HERE ON ARE THE DIRECTIVES
# DIRECTIVES ARE WHAT I CALL SMALL FUNCTIONS WHICH ARE INVOKED WHEN A
# CERTAIN CODE IS READ FROM THE IBUS.
#
# SO ADD YOUR OWN IF YOU LIKE, OR MODIFY WHATS THERE.
# USE THE BIG JSON DICTIONARY AT THE TOP
############################################################################
# All directives should have a d_ prefix as we are searching GLOBALLY for function names..
# So best have unique enough names
############################################################################


def d_custom_IKE(packet):
    packet_data = packet['dat']
    # 18 : speed and RPM
    if packet_data[0] == '18':
        speed = int(packet_data[1], 16) * 2
        revs = int(packet_data[2], 16) * 10000
        customState = {'speed' : speed, 'revs' : revs}
    # 19 = Temperature
    elif packet_data[0] == '19':
        extTemp = int(packet_data[1], 16)
        oilTemp = int(packet_data[2], 16)
        customState = {'extTemp' : extTemp, 'oilTemp' : oilTemp}


############################################################################
# DIRECTIVE CDC FUNCTIONS
############################################################################

# Respond to the Poll for changer alive
def d_cdPollResponse(packet):
    #WRITER.writeBusPacket('18', 'FF', ['02','00'])
    #logging.debug("CDC sent the status: Alive")
    pB_cdc.disableFunc("announce")           # stop announcing
    pB_cdc.disableFunc("pollResponse")
    pB_cdc.enableFunc("pollResponse", 10)    # defaul 30 (not worked)


def d_cdStatusPlaying(packet):
    pB_cdc.play('01', '01')


def d_cdStop(packet):
    pB_cdc.stop('01', '01')



def d_cdPlay(packet):
    pB_cdc.play('01', '01')



def d_cdNext(packet):
    pB_cdc.scanFWD('01', '01')



def d_cdPrev(packet):
    pB_cdc.scanBWD('01', '01')


############################################################################
# BUTTON DISPLAY
############################################################################

def button1p(packet):
    logging.debug('MK4 - Button 1 press (%s)' %packet)
    pB_cdc.play('01', '01')

def button2p(packet):
    logging.debug('MK4 - Button 2 press (%s)' % packet)

def button3p(packet):
    logging.debug('MK4 - Button 3 press (%s)' % packet)
    pB_cdc.stop('01', '01')

def button4p(packet):
    logging.debug('MK4 - Button 4 press (%s)' % packet)

def button5p(packet):
    logging.debug('MK4 - Button 5 press (%s)' % packet)

def button6p(packet):
    logging.debug('MK4 - Button 6 press (%s)' % packet)



def slctIndexF0(packet):
    logging.debug('MK4 - selected Index fields 0 (%s)' % packet)

def slctIndexF1(packet):
    logging.debug('MK4 - selected Index fields 1 (%s)' % packet)

def slctIndexF2(packet):
    logging.debug('MK4 - selected Index fields 2 (%s)' % packet)

def slctIndexF3(packet):
    logging.debug('MK4 - selected Index fields 3 (%s)' % packet)

def slctIndexF4(packet):
    logging.debug('MK4 - selected Index fields 4 (%s)' % packet)

def slctIndexF5(packet):
    logging.debug('MK4 - selected Index fields 5 (%s)' % packet)

def slctIndexF6(packet):
    logging.debug('MK4 - selected Index fields 6 (%s)' % packet)

def slctIndexF7(packet):
    logging.debug('MK4 - selected Index fields 7 (%s)' % packet)

def slctIndexF8(packet):
    logging.debug('MK4 - selected Index fields 8 (%s)' % packet)

def slctIndexF9(packet):
    logging.debug('MK4 - selected Index fields 9 (%s)' % packet)


############################################################################
# MENU DISPLAY
############################################################################



