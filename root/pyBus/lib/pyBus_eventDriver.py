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
import datetime
from subprocess import Popen, PIPE
sys.path.append('/root/pyBus/lib/')

# Imports for the project
import pyBus_util as pB_util
import pyBus_cdc as pB_cdc
import pyBus_io as pB_io

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
#            '7A5121': ''                        # driver door opened
#        }
#    },
#    '3F': {
#        '00': {
#            '0C3401': '',                       # All doors unlocked
#            '0C4601': '',                       # Passenger Door Locked
#            '0C4701': ''                        # Driver Door Locked
#        }
#    },
#    '44': {
#        'BF': {
#            '740400': ''                        # Ignition key in
#            '7401FF': '',                       # Ignition key position 1
#            '740401': '',                       # Ignition key position 2
#            '7400FF': ''                        # Ignition key removed
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
#            '4807': 'infoP',                    # F0 05 68 48 07 - Info press
#            '4844': 'infoH',                    # F0 05 68 48 44 - Info hold
#            '4887': 'infoR',                    # F0 05 68 48 87 - Info released
            '4811': 'button1p',                 # F0 04 68 48 11 - Button 1 press
#            '4851': 'button1H',                 # F0 04 68 48 51 - Button 1 hold
#            '4891': 'button1R',                 # F0 05 68 48 91 - Button 1 released
            '4801': 'button2p',                 # F0 04 68 48 01 - Button 2 press
#            '4841': 'button2H',                 # F0 04 68 48 41 - Button 2 hold
#            '4881': 'button2R',                 # F0 05 68 48 81 - Button 2 released
            '4812': 'button3p',                 # F0 04 68 48 12 - Button 3 press
#            '4852': 'button3H',                 # F0 04 68 48 52 - Button 3 hold
#            '4892': 'button3R',                 # F0 05 68 48 92 - Button 3 released
            '4802': 'button4p',                 # F0 04 68 48 02 - Button 4 press
#            '4842': 'button4H',                 # F0 04 68 48 42 - Button 4 hold
#            '4882': 'button4R',                 # F0 05 68 48 82 - Button 4 released
            '4813': 'button5p',                 # F0 04 68 48 13 - Button 5 press
#            '4853': 'button5H',                 # F0 04 68 48 53 - Button 5 hold
#            '4893': 'button5R',                 # F0 05 68 48 93 - Button 5 released
            '4803': 'button6p',                 # F0 04 68 48 03 - Button 6 press
#            '4843': 'button6H',                 # F0 04 68 48 43 - Button 6 hold
#            '4883': 'button6R',                 # F0 05 68 48 83 - Button 6 released
#            '4810': 'ArrowLP',                  # F0 04 68 48 10 - "<" ArrowLeft press
#            '4850': 'ArrowLH',                  # F0 04 68 48 50 - "<" ArrowLeft hold
#            '4890': 'ArrowLR',                  # F0 05 68 48 90 - "<" ArrowLeft released
#            '4800': 'ArrowRP',                  # F0 04 68 48 00 - ">" ArrowRight press
#            '4840': 'ArrowRH',                  # F0 04 68 48 40 - ">" ArrowRight hold
#            '4880': 'ArrowRR',                  # F0 05 68 48 80 - ">" ArrowRight released
#            '4814': 'ArrowP',                   # F0 04 68 48 14 - "<>" Arrow press
#            '4854': 'ArrowH',                   # F0 04 68 48 54 - "<>" Arrow hold
#            '4894': 'ArrowR',                   # F0 05 68 48 94 - "<>" Arrow released
#            '4823': 'modeP',                    # F0 04 68 48 23 - MODE press
#            '4863': 'modeH',                    # F0 04 68 48 63 - MODE hold
#            '48A3':'modeR'                      # F0 05 68 48 A3 - MODE released
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
            '23': {
                '62': {
                    '3040': 'slctIndexF0',          # 3B 06 68 23 62 30 40 - selected Index fields 0
                    '3041': 'slctIndexF1',          # 3B 06 68 23 62 30 41 - selected Index fields 1
                    '3042': 'slctIndexF2',          # 3B 06 68 23 62 30 42 - selected Index fields 2
                    '3043': 'slctIndexF3',          # 3B 06 68 23 62 30 43 - selected Index fields 3
                    '3044': 'slctIndexF4',          # 3B 06 68 23 62 30 44 - selected Index fields 4
                    '3045': 'slctIndexF5',          # 3B 06 68 23 62 30 45 - selected Index fields 5
                    '3046': 'slctIndexF6',          # 3B 06 68 23 62 30 46 - selected Index fields 6
                    '3047': 'slctIndexF7',          # 3B 06 68 23 62 30 47 - selected Index fields 7
                    '3048': 'slctIndexF8',          # 3B 06 68 23 62 30 48 - selected Index fields 8
                    '3049': 'slctIndexF9'           # 3B 06 68 23 62 30 49 - selected Index fields 9
                }
            }
        }
    },

    '50': {
        'C8': {                                 # Multifunction steering wheel phone buttons
            '01':   'd_cdPollResponse',         # This can happen via RT button or ignition
            '3B40': 'wheelRT',                  # 50 04 C8 3B 40    - R/T
#            '3B80': 'wheelVoiceP',              # 50 04 C8 3B 80 27 - voice press
#            '3B90': 'wheelVoiceH',              # 50 04 C8 3B 90 37 - voice hold
#            '3BA0': 'wheelVoiceR'               # 50 04 C8 3B A0 07 - voice release
        },
        '68': {                                 # Multifunction steering wheel buttons
            '3211': '',                         # 50 04 68 32 11 1F - "+" press
            '3210': '',                         # 50 04 68 32 10 1E - "-" press
            '3B01': 'wheelArrowUP',             # 50 04 68 3B 01 06 - ">" press
            '3B11': 'wheelArrowUH',             # 50 04 68 3B 11 16 - ">" hold
            '3B21': 'wheelArrowUR',             # 50 04 68 3B 21 26 - ">" release
            '3B08': 'wheelArrowDP',             # 50 04 68 3B 08 0F - "<" press
            '3B18': 'wheelArrowDH',             # 50 04 68 3B 18 1F - "<" hold
            '3B28': 'wheelArrowDR'              # 50 04 68 3B 28 2F - "<" release
        }
    }
}

############################################################################
# CONFIG
############################################################################

WRITER = None
SESSION_DATA = {}
buttonIO = None
TICK = 0.02  # sleep interval in seconds used between iBUS reads


############################################################################
# FUNCTIONS
############################################################################

def init(writer):
    global WRITER
    global SESSION_DATA
    global buttonIO
    WRITER = writer

    pB_io.init(WRITER)
    buttonIO = pB_io.ButtonIO()
    pB_cdc.init(WRITER)
    pB_util.init(WRITER)

    WRITER.writeBusPacket('18', 'FF', ['02', '01'])
    logging.debug('CDC sent the status: Start')
    #pB_cdc.enableFunc("announce", 10)              # default 30 (not worked)

# Manage the packet, meaning traverse the JSON 'DIRECTIVES' object and attempt to determine a suitable function to pass the packet to.
def manage(packet):
    src = packet['src']
    dst = packet['dst']
    dataString = ''.join(packet['dat'])
    methodName = None

    try:
        dstDir = DIRECTIVES[src][dst]
        if 'ALL' in dstDir.keys():
            methodName = dstDir['ALL']
        else:
            methodName = dstDir[dataString]
    except Exception, e:
        pass

    result = None
    if methodName is not None:
        methodToCall = globals().get(methodName, None)
        if methodToCall:
            logging.debug('Directive found for packet - %s' % methodName)
            try:
                result = methodToCall(packet)
            except:
                logging.error('Exception raised from [%s]' % methodName)
                logging.error(traceback.format_exc())

        else:
            logging.debug('Method (%s) does not exist' % methodName)
    else:
        logging.debug('MethodName (%s) does not match a function' % methodName)

    return result


def listen():
    logging.info('Event listener initialized')
    while True:
        packet = WRITER.readBusPacket()
        if packet:
            manage(packet)
        time.sleep(TICK)    # sleep a bit


def shutDown():
    logging.debug('Stopping IO Driver')
    pB_io.end()
    logging.debug('Killing CDC')
    pB_cdc.shutDown()
    logging.debug('Killing Util')
    pB_util.shutDown()


############################################################################
# IKE
############################################################################

def d_custom_IKE(packet):
    packet_data = packet['dat']
    # 18 : speed and RPM
    if packet_data[0] == '18':
        speed = int(packet_data[1], 16) * 2
        revs = int(packet_data[2], 16) * 10000
        customState = {'speed': speed, 'revs': revs}
    # 19 = Temperature
    elif packet_data[0] == '19':
        extTemp = int(packet_data[1], 16)
        oilTemp = int(packet_data[2], 16)
        customState = {'extTemp': extTemp, 'oilTemp': oilTemp}


############################################################################
# DIRECTIVE CDC FUNCTIONS
############################################################################

# Respond to the Poll for changer alive
def d_cdPollResponse(packet):
    #pB_cdc.disableFunc('announce')                          # stop announcing
    WRITER.writeBusPacket('18', 'FF', ['02', '00'])
    logging.debug('CDC sent the status: Alive')
    #pB_cdc.disableFunc('pollResponse')
    #pB_cdc.enableFunc('pollResponse', 10)               # default 30 (not worked)
    WRITER.writeBusPacket('68', 'c0', ['21', '40', '00', '09', '05', '05', '4D', '50', '53'])


def d_cdStatusPlaying(packet):
    pB_cdc.play('01', '01')


#def d_cdStop(packet):
#    pB_cdc.stop('01', '01')


#def d_cdPlay(packet):
#    pB_cdc.play('01', '01')


#def d_cdNext(packet):
#    pB_cdc.scanFWD('01', '01')


#def d_cdPrev(packet):
#    pB_cdc.scanBWD('01', '01')


############################################################################
# BUTTON DISPLAY
############################################################################
def infoP(packet):
    logging.debug('MK4 - Info press (%s)' % packet)
    buttonIO.infoP()


def infoH(packet):
    logging.debug('MK4 - Info hold (%s)' % packet)
    buttonIO.infoH()


def infoR(packet):
    logging.debug('MK4 - Info released (%s)' % packet)
    buttonIO.infoR()


def button1P(packet):
    logging.debug('MK4 - Button 1 press (%s)' % packet)
    buttonIO.button1P()


def button1H(packet):
    logging.debug('MK4 - Button 1 hold (%s)' % packet)
    buttonIO.button1H()


def button1R(packet):
    logging.debug('MK4 - Button 1 released (%s)' % packet)
    buttonIO.button1R()


def button2P(packet):
    logging.debug('MK4 - Button 2 press (%s)' % packet)
    buttonIO.button2P()


def button2H(packet):
    logging.debug('MK4 - Button 2 hold (%s)' % packet)
    buttonIO.button2H()


def button2R(packet):
    logging.debug('MK4 - Button 2 released (%s)' % packet)
    buttonIO.button2R()


def button3P(packet):
    logging.debug('MK4 - Button 3 press (%s)' % packet)
    buttonIO.button3P()


def button3H(packet):
    logging.debug('MK4 - Button 3 hold (%s)' % packet)
    buttonIO.button3H()


def button3R(packet):
    logging.debug('MK4 - Button 3 released (%s)' % packet)
    buttonIO.button3R()


def button4P(packet):
    logging.debug('MK4 - Button 4 press (%s)' % packet)
    buttonIO.button4P()


def button4H(packet):
    logging.debug('MK4 - Button 4 hold (%s)' % packet)
    buttonIO.button4H()


def button4R(packet):
    logging.debug('MK4 - Button 4 released (%s)' % packet)
    buttonIO.button4R()


def button5P(packet):
    logging.debug('MK4 - Button 5 press (%s)' % packet)
    buttonIO.button5P()


def button5H(packet):
    logging.debug('MK4 - Button 5 hold (%s)' % packet)
    buttonIO.button5H()


def button5R(packet):
    logging.debug('MK4 - Button 5 released (%s)' % packet)
    buttonIO.button5R()


def button6P(packet):
    logging.debug('MK4 - Button 6 press (%s)' % packet)
    buttonIO.button6P()


def button6H(packet):
    logging.debug('MK4 - Button 6 hold (%s)' % packet)
    buttonIO.button6H()


def button6R(packet):
    logging.debug('MK4 - Button 6 released (%s)' % packet)
    buttonIO.button6R()


def ArrowLP(packet):
    logging.debug('MK4 - "<" ArrowLeft press (%s)' % packet)
    buttonIO.ArrowLP()


def ArrowLH(packet):
    logging.debug('MK4 - "<" ArrowLeft hold (%s)' % packet)
    buttonIO.ArrowLH()


def ArrowLR(packet):
    logging.debug('MK4 - "<" ArrowLeft released (%s)' % packet)
    buttonIO.ArrowLR()


def ArrowRP(packet):
    logging.debug('MK4 - ">" ArrowRight press (%s)' % packet)
    buttonIO.ArrowRP()


def ArrowRH(packet):
    logging.debug('MK4 - ">" ArrowRight hold (%s)' % packet)
    buttonIO.ArrowRH()


def ArrowRR(packet):
    logging.debug('MK4 - ">" ArrowRight released (%s)' % packet)
    buttonIO.ArrowRR()


def ArrowP(packet):
    logging.debug('MK4 - "<>" Arrow press (%s)' % packet)
    buttonIO.ArrowP()


def ArrowH(packet):
    logging.debug('MK4 - "<>" Arrow hold (%s)' % packet)
    buttonIO.ArrowH()


def ArrowR(packet):
    logging.debug('MK4 - "<>" Arrow released (%s)' % packet)
    buttonIO.ArrowR()


def modeP(packet):
    logging.debug('MK4 -  MODE press (%s)' % packet)
    buttonIO.modeP()


def modeH(packet):
    logging.debug('MK4 - MODE hold (%s)' % packet)
    buttonIO.modeH()


def modeR(packet):
    logging.debug('MK4 - MODE released (%s)' % packet)
    buttonIO.modeR()


def slctIndexF0(packet):
    logging.debug('MK4 - Index fields 0 (%s)' % packet)
    buttonIO.slctIndexF0()


def slctIndexF1(packet):
    logging.debug('MK4 - Index fields 1 (%s)' % packet)
    buttonIO.slctIndexF1()


def slctIndexF2(packet):
    logging.debug('MK4 - Index fields 2 (%s)' % packet)
    buttonIO.slctIndexF2()


def slctIndexF3(packet):
    logging.debug('MK4 - Index fields 3 (%s)' % packet)
    buttonIO.slctIndexF3()


def slctIndexF4(packet):
    logging.debug('MK4 - Index fields 4 (%s)' % packet)
    buttonIO.slctIndexF4()


def slctIndexF5(packet):
    logging.debug('MK4 - Index fields 5 (%s)' % packet)
    buttonIO.slctIndexF5()


def slctIndexF6(packet):
    logging.debug('MK4 - Index fields 6 (%s)' % packet)
    buttonIO.slctIndexF6()


def slctIndexF7(packet):
    logging.debug('MK4 - Index fields 7 (%s)' % packet)
    buttonIO.slctIndexF7()


def slctIndexF8(packet):
    logging.debug('MK4 - Index fields 8 (%s)' % packet)
    buttonIO.slctIndexF8()


def slctIndexF9(packet):
    logging.debug('MK4 - Index fields 9 (%s)' % packet)
    buttonIO.slctIndexF9()


def wheelRT(packet):
    logging.debug('Multifunction steering wheel - R/T (%s)' % packet)
    buttonIO.wheelRT()


def wheelVoiceP(packet):
    logging.debug('Multifunction steering wheel - voice press (%s)' % packet)
    buttonIO.wheelVoiceP()


def wheelVoiceH(packet):
    logging.debug('Multifunction steering wheel - voice hold (%s)' % packet)
    buttonIO.wheelVoiceH()


def wheelVoiceR(packet):
    logging.debug('Multifunction steering wheel - voice release (%s)' % packet)
    buttonIO.wheelVoiceR()


def wheelArrowUP(packet):
    logging.debug('Multifunction steering wheel - ">" press (%s)' % packet)
    buttonIO.wheelArrowUP()


def wheelArrowUH(packet):
    logging.debug('Multifunction steering wheel - ">" hold (%s)' % packet)
    buttonIO.wheelArrowUH()


def wheelArrowUR(packet):
    logging.debug('Multifunction steering wheel - ">" release (%s)' % packet)
    buttonIO.wheelArrowUR()


def wheelArrowDP(packet):
    logging.debug('Multifunction steering wheel - "<" press (%s)' % packet)
    buttonIO.wheelArrowDP()


def wheelArrowDR(packet):
    logging.debug('Multifunction steering wheel - "<" hold (%s)' % packet)
    buttonIO.wheelArrowDR()


def wheelArrowDR(packet):
    logging.debug('Multifunction steering wheel - "<" release (%s)' % packet)
    buttonIO.wheelArrowDR()


############################################################################