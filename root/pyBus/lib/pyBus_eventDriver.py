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

    '68': {                                 # RADIO
        '18': {
            '01': 'd_cdPollResponse',       # "I'm alive" message
            '380000': 'd_cdStatusPlaying',  # CD status Req         # 68 05 18 38 00 00
            '380100': '',                   # Stop press            # 68 05 18 38 01 00
            '380300': '',                   # Play press            # 68 05 18 38 03 00
            '380A00': '',                   # Skip forward          # 68 05 18 38 0A 00
            '380A01': '',                   # Skip Backward         # 68 05 18 38 0A 01
            '380700': '',                   # Scan Off press        # 68 05 18 38 07 00
            '380701': '',                   # Scan On press         # 68 05 18 38 07 01
            '380601': '',                   # CD Button 1 press     # 68 05 18 38 06 01
            '380602': '',                   # CD Button 2 press     # 68 05 18 38 06 02
            '380603': '',                   # CD Button 3 press     # 68 05 18 38 06 03
            '380604': '',                   # CD Button 4 press     # 68 05 18 38 06 04
            '380605': '',                   # CD Button 5 press     # 68 05 18 38 06 05
            '380606': '',                   # CD Button 6 press     # 68 05 18 38 06 06
            '380400': '',                   # Fast Rwd press        # 68 05 18 38 04 00
            '380401': '',                   # Fast Fwd press        # 68 05 18 38 04 01
            '380800': 'd_cdRandom',         # Random Off press      # 68 05 18 38 08 00
            '380801': 'd_cdRandom'          # Random On press       # 68 05 18 38 08 01
        }
    },

    'F0': {                         # BMBT Buttons
        '68': {
            '4807': 'infoP',        # Info press                        # F0 04 68 48 07
            '4844': 'infoH',        # Info hold                         # F0 04 68 48 44
            '4887': 'infoR',        # Info released                     # F0 04 68 48 87

            '4811': 'button1p',     # Button 1 press                    # F0 04 68 48 11
            '4851': 'button1H',     # Button 1 hold                     # F0 04 68 48 51
            '4891': 'button1R',     # Button 1 released                 # F0 04 68 48 91

            '4801': 'button2p',     # Button 2 press                    # F0 04 68 48 01
            '4841': 'button2H',     # Button 2 hold                     # F0 04 68 48 41
            '4881': 'button2R',     # Button 2 released                 # F0 04 68 48 81

            '4812': 'button3p',     # Button 3 press                    # F0 04 68 48 12
            '4852': 'button3H',     # Button 3 hold                     # F0 04 68 48 52
            '4892': 'button3R',     # Button 3 released                 # F0 04 68 48 92

            '4802': 'button4p',     # Button 4 press                    # F0 04 68 48 02
            '4842': 'button4H',     # Button 4 hold                     # F0 04 68 48 42
            '4882': 'button4R',     # Button 4 released                 # F0 04 68 48 82

            '4813': 'button5p',     # Button 5 press                    # F0 04 68 48 13
            '4853': 'button5H',     # Button 5 hold                     # F0 04 68 48 53
            '4893': 'button5R',     # Button 5 released                 # F0 04 68 48 93

            '4803': 'button6p',     # Button 6 press                    # F0 04 68 48 03
            '4843': 'button6H',     # Button 6 hold                     # F0 04 68 48 43
            '4883': 'button6R',     # Button 6 released                 # F0 04 68 48 83

            '4810': 'arrowLP',      # "<" ArrowLeft press               # F0 04 68 48 10
            '4850': 'arrowLH',      # "<" ArrowLeft hold                # F0 04 68 48 50
            '4890': 'arrowLR',      # "<" ArrowLeft released            # F0 04 68 48 90

            '4800': 'arrowRP',      # ">" ArrowRight press              # F0 04 68 48 00
            '4840': 'arrowRH',      # ">" ArrowRight hold               # F0 04 68 48 40
            '4880': 'arrowRR',      # ">" ArrowRight released           # F0 04 68 48 80

            '4814': 'arrowP',       # "<>" Arrow press                  # F0 04 68 48 14
            '4854': 'arrowH',       # "<>" Arrow hold                   # F0 04 68 48 54
            '4894': 'arrowR',       # "<>" Arrow released               # F0 04 68 48 94

            '4823': 'modeP',        # MODE press                        # F0 04 68 48 23
            '4863': 'modeH',        # MODE hold                         # F0 04 68 48 63
            '48A3': 'modeR',        # MODE released                     # F0 04 68 48 A3

            '4808': '',             # TELEPHONE pressed                 # F0 04 68 48 08
            '4848': '',             # TELEPHONE hold                    # F0 04 68 48 48
            '4888': '',             # TELEPHONE released                # F0 04 68 48 88

            '4901': '',             # right nob Right turn 1 step       # F0 04 3B 49 01
            '4902': '',             # right nob Right turn 2 steps      # F0 04 3B 49 02
            '4903': '',             # right nob Right turn 3 steps      # F0 04 3B 49 03
            '4905': '',             # right nob Left turn 5 steps       # F0 04 3B 49 05

            '4981': '',             # right nob Left turn 1 step        # F0 04 3B 49 81
            '4982': '',             # right nob Left turn 2 steps       # F0 04 3B 49 82
            '4983': '',             # right nob Left turn 3 steps       # F0 04 3B 49 83
            '4985': '',             # right nob Left turn 5 steps       # F0 04 3B 49 85

            '4805': '',             # right nob push                    # F0 04 3B 48 05
            '4845': '',             # right nob hold                    # F0 04 3B 48 45
            '4885': ''              # right nob released                # F0 04 3B 48 85
        }
    },

    '3B': {                             # BMBT Index fields
        '68': {
            '31600000': 'indexF0P',     # Index fields 0 press          # 3B 06 68 31 60 00 00
            '31600020': 'indexF0H',     # Index fields 0 hold           # 3B 06 68 31 60 00 20
            '31600040': 'indexF0R',     # Index fields 0 released       # 3B 06 68 31 60 00 40

            '31600001': 'indexF1P',     # Index fields 1 press          # 3B 06 68 31 60 00 01
            '31600021': 'indexF1H',     # Index fields 1 hold           # 3B 06 68 31 60 00 21
            '31600041': 'indexF1R',     # Index fields 1 released       # 3B 06 68 31 60 00 41

            '31600002': 'indexF2P',     # Index fields 2 press          # 3B 06 68 31 60 00 02
            '31600022': 'indexF2H',     # Index fields 2 hold           # 3B 06 68 31 60 00 22
            '31600042': 'indexF2R',     # Index fields 2 released       # 3B 06 68 31 60 00 42

            '31600003': 'indexF3P',     # Index fields 3 press          # 3B 06 68 31 60 00 03
            '31600023': 'indexF3H',     # Index fields 3 hold           # 3B 06 68 31 60 00 23
            '31600043': 'indexF3R',     # Index fields 3 released       # 3B 06 68 31 60 00 43

            '31600004': 'indexF4P',     # Index fields 4 press          # 3B 06 68 31 60 00 04
            '31600024': 'indexF4H',     # Index fields 4 hold           # 3B 06 68 31 60 00 24
            '31600044': 'indexF4R',     # Index fields 4 released       # 3B 06 68 31 60 00 44

            '31600005': 'indexF5P',     # Index fields 5 press          # 3B 06 68 31 60 00 05
            '31600025': 'indexF5H',     # Index fields 5 hold           # 3B 06 68 31 60 00 25
            '31600045': 'indexF5R',     # Index fields 5 released       # 3B 06 68 31 60 00 45

            '31600006': 'indexF6P',     # Index fields 6 press          # 3B 06 68 31 60 00 06
            '31600026': 'indexF6H',     # Index fields 6 hold           # 3B 06 68 31 60 00 26
            '31600046': 'indexF6R',     # Index fields 6 released       # 3B 06 68 31 60 00 46

            '31600007': 'indexF7P',     # Index fields 7 press          # 3B 06 68 31 60 00 07
            '31600027': 'indexF7H',     # Index fields 7 hold           # 3B 06 68 31 60 00 27
            '31600047': 'indexF7R',     # Index fields 7 released       # 3B 06 68 31 60 00 47

            '31600008': 'indexF8P',     # Index fields 8 press          # 3B 06 68 31 60 00 08
            '31600028': 'indexF8H',     # Index fields 8 hold           # 3B 06 68 31 60 00 28
            '31600048': 'indexF8R',     # Index fields 8 released       # 3B 06 68 31 60 00 48

            '31600009': 'indexF9P',     # Index fields 9 press          # 3B 06 68 31 60 00 09
            '31600029': 'indexF9H',     # Index fields 9 hold           # 3B 06 68 31 60 00 29
            '31600049': 'indexF9R'      # Index fields 9 released       # 3B 06 68 31 60 00 49
        }
    },

    '50': {                             # Multifunction steering wheel
        'C8': {                         # wheel phone buttons
            '01': 'd_cdPollResponse',   # This can happen via RT button or ignition
            '3B40': 'wheelRT',          # R/T                           # 50 04 C8 3B 40

            '3B80': 'wheelVoiceP',      # voice press                   # 50 04 C8 3B 80 27
            '3B90': 'wheelVoiceH',      # voice hold                    # 50 04 C8 3B 90 37
            '3BA0': 'wheelVoiceR'       # voice release                 # 50 04 C8 3B A0 07
        },
        '68': {                         # wheel buttons
            '3211': '',                 # "+" press                     # 50 04 68 32 11 1F
            '3210': '',                 # "-" press                     # 50 04 68 32 10 1E
            '3B01': 'wheelArrowUP',     # ">" press                     # 50 04 68 3B 01 06
            '3B11': 'wheelArrowUH',     # ">" hold                      # 50 04 68 3B 11 16
            '3B21': 'wheelArrowUR',     # ">" release                   # 50 04 68 3B 21 26
            '3B08': 'wheelArrowDP',     # "<" press                     # 50 04 68 3B 08 0F
            '3B18': 'wheelArrowDH',     # "<" hold                      # 50 04 68 3B 18 1F
            '3B28': 'wheelArrowDR'      # "<" release                   # 50 04 68 3B 28 2F
        }
    },

    '80': {
        'BF': {
            'ALL': 'd_custom_IKE'       # Use ALL to send all data to a particular function
        }
    }

#    '7F': {
#        '80': {
#            'ALL': 'navi_date'
#        }
#    }
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

    pB_cdc.enableFunc("announce", 10)  # default 30 (not worked)


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
            logging.debug('Directive found for packet - %s', methodName)
            try:
                result = methodToCall(packet)
            except:
                logging.error('Exception raised from [%s]', methodName)
                logging.error(traceback.format_exc())

        else:
            logging.debug('Method (%s) does not exist', methodName)
    else:
        logging.debug('MethodName (%s) does not match a function', methodName)

    return result


def listen():
    logging.info('Event listener initialized')
    while True:
        packet = WRITER.readBusPacket()
        if packet:
            manage(packet)

        time.sleep(TICK)  # sleep a bit


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
        revs = int(packet_data[2], 16) * 100
        customState = {'speed': speed, 'revs': revs}
        logging.debug('IKE - (%s)', customState)
    # 19 = Temperature
    elif packet_data[0] == '19':
        extTemp = int(packet_data[1], 16)
        oilTemp = int(packet_data[2], 16)
        customState = {'extTemp': extTemp, 'oilTemp': oilTemp}
        logging.debug('IKE - (%s)', customState)


############################################################################
# DATA
############################################################################
# 7F 80 1F 40 14 59 07 00 07 20 11,NAV --> IKE : Time & date: UTC 14:59 07 Juli 2011
#def navi_date(packet):
#    packet_data = packet['dat']
#    if packet_data[0] == '1F' and packet_data[1] == '40':
#        logging.debug('DATE - %s.%s.%s%s)', int(packet_data[4]), int(packet_data[6]),
#                      int(packet_data[7]), int(packet_data[8]))
#        logging.debug('TIME - %s:%s)', int(packet_data[2]), int(packet_data[3]))

############################################################################
# DIRECTIVE CDC FUNCTIONS
############################################################################
# Respond to the Poll for changer alive
def d_cdPollResponse(packet):
    pB_cdc.disableFunc('announce')          # stop announcing
    pB_cdc.disableFunc('pollResponse')
    pB_cdc.enableFunc('pollResponse', 10)   # default 30 (not worked)
    WRITER.writeBusPacket('68', 'c0', ['21', '40', '00', '09', '05', '05', '4D', '50', '53'])


def d_cdStatusPlaying(packet):
    pB_cdc.play('01', '01')


# def d_cdStop(packet):
#    pB_cdc.stop('01', '01')


# def d_cdPlay(packet):
#    pB_cdc.play('01', '01')


# def d_cdNext(packet):
#    pB_cdc.scanFWD('01', '01')


# def d_cdPrev(packet):
#    pB_cdc.scanBWD('01', '01')


############################################################################
# BUTTON DISPLAY
############################################################################
# Info #####################################################################
def infoP(packet):
    logging.debug('BMBT - Info press (%s)', packet)
    buttonIO.infoP()

def infoH(packet):
    logging.debug('BMBT - Info hold (%s)', packet)
    buttonIO.infoH()

def infoR(packet):
    logging.debug('BMBT - Info released (%s)', packet)
    buttonIO.infoR()


# Button 1 #################################################################
def button1P(packet):
    logging.debug('BMBT - Button 1 press (%s)', packet)
    buttonIO.button1P()

def button1H(packet):
    logging.debug('BMBT - Button 1 hold (%s)', packet)
    buttonIO.button1H()

def button1R(packet):
    logging.debug('BMBT - Button 1 released (%s)', packet)
    buttonIO.button1R()


# Button 2 #################################################################
def button2P(packet):
    logging.debug('BMBT - Button 2 press (%s)', packet)
    buttonIO.button2P()

def button2H(packet):
    logging.debug('BMBT - Button 2 hold (%s)', packet)
    buttonIO.button2H()

def button2R(packet):
    logging.debug('BMBT - Button 2 released (%s)', packet)
    buttonIO.button2R()


# Button 3 #################################################################
def button3P(packet):
    logging.debug('BMBT - Button 3 press (%s)', packet)
    buttonIO.button3P()

def button3H(packet):
    logging.debug('BMBT - Button 3 hold (%s)', packet)
    buttonIO.button3H()

def button3R(packet):
    logging.debug('BMBT - Button 3 released (%s)', packet)
    buttonIO.button3R()


# Button 4 #################################################################
def button4P(packet):
    logging.debug('BMBT - Button 4 press (%s)', packet)
    buttonIO.button4P()

def button4H(packet):
    logging.debug('BMBT - Button 4 hold (%s)', packet)
    buttonIO.button4H()

def button4R(packet):
    logging.debug('BMBT - Button 4 released (%s)', packet)
    buttonIO.button4R()


# Button 5 #################################################################
def button5P(packet):
    logging.debug('BMBT - Button 5 press (%s)', packet)
    buttonIO.button5P()

def button5H(packet):
    logging.debug('BMBT - Button 5 hold (%s)', packet)
    buttonIO.button5H()

def button5R(packet):
    logging.debug('BMBT - Button 5 released (%s)', packet)
    buttonIO.button5R()


# Button 6 #################################################################
def button6P(packet):
    logging.debug('BMBT - Button 6 press (%s)', packet)
    buttonIO.button6P()

def button6H(packet):
    logging.debug('BMBT - Button 6 hold (%s)', packet)
    buttonIO.button6H()

def button6R(packet):
    logging.debug('BMBT - Button 6 released (%s)', packet)
    buttonIO.button6R()


# "<" Arrow Left ###########################################################
def arrowLP(packet):
    logging.debug('BMBT - "<" ArrowLeft press (%s)', packet)
    buttonIO.arrowLP()

def arrowLH(packet):
    logging.debug('BMBT - "<" ArrowLeft hold (%s)', packet)
    buttonIO.arrowLH()

def arrowLR(packet):
    logging.debug('BMBT - "<" ArrowLeft released (%s)', packet)
    buttonIO.arrowLR()


# ">" Arrow Left ###########################################################
def arrowRP(packet):
    logging.debug('BMBT - ">" ArrowRight press (%s)', packet)
    buttonIO.arrowRP()

def arrowRH(packet):
    logging.debug('BMBT - ">" ArrowRight hold (%s)', packet)
    buttonIO.arrowRH()

def arrowRR(packet):
    logging.debug('BMBT - ">" ArrowRight released (%s)', packet)
    buttonIO.arrowRR()


# "<>" Arrow Left ##########################################################
def arrowP(packet):
    logging.debug('BMBT - "<>" Arrow press (%s)', packet)
    buttonIO.arrowP()

def arrowH(packet):
    logging.debug('BMBT - "<>" Arrow hold (%s)', packet)
    buttonIO.arrowH()

def arrowR(packet):
    logging.debug('BMBT - "<>" Arrow released (%s)', packet)
    buttonIO.arrowR()


# MODE #####################################################################
def modeP(packet):
    logging.debug('BMBT - MODE press (%s)', packet)
    buttonIO.modeP()

def modeH(packet):
    logging.debug('BMBT - MODE hold (%s)', packet)
    buttonIO.modeH()

def modeR(packet):
    logging.debug('BMBT - MODE released (%s)', packet)
    buttonIO.modeR()


# IndexF0 ##################################################################
def indexF0P(packet):
    logging.debug('BMBT - Index fields 0 (%s)', packet)
    buttonIO.slctIndexF0()

def indexF0H(packet):
    logging.debug('BMBT - Index fields 0 hold (%s)', packet)

def indexF0R(packet):
    logging.debug('BMBT - Index fields 0 released (%s)', packet)


# IndexF1 ##################################################################
def indexF1P(packet):
    logging.debug('BMBT - Index fields 1 press (%s)', packet)
    buttonIO.indexF1P()

def indexF1H(packet):
    logging.debug('BMBT - Index fields 1 hold (%s)', packet)

def indexF1R(packet):
    logging.debug('BMBT - Index fields 1 released (%s)', packet)


# IndexF2 ##################################################################
def indexF2P(packet):
    logging.debug('BMBT - Index fields 2 press (%s)', packet)
    buttonIO.indexF2P()

def indexF2H(packet):
    logging.debug('BMBT - Index fields 2 hold (%s)', packet)

def indexF2R(packet):
    logging.debug('BMBT - Index fields 2 released (%s)', packet)


# IndexF3 ##################################################################
def indexF3P(packet):
    logging.debug('BMBT - Index fields 3 press (%s)', packet)
    buttonIO.indexF3P()

def indexF3H(packet):
    logging.debug('BMBT - Index fields 3 hold (%s)', packet)

def indexF3R(packet):
    logging.debug('BMBT - Index fields 3 released (%s)', packet)


# IndexF4 ##################################################################
def indexF4P(packet):
    logging.debug('BMBT - Index fields 4 press (%s)', packet)
    buttonIO.indexF4P()

def indexF4H(packet):
    logging.debug('BMBT - Index fields 4 hold (%s)', packet)

def indexF4R(packet):
    logging.debug('BMBT - Index fields 4 released (%s)', packet)


# IndexF5 ##################################################################
def indexF5P(packet):
    logging.debug('BMBT - Index fields 5 press (%s)', packet)
    buttonIO.indexF5P()

def indexF5H(packet):
    logging.debug('BMBT - Index fields 5 hold (%s)', packet)

def indexF5R(packet):
    logging.debug('BMBT - Index fields 5 released (%s)', packet)


# IndexF6 ##################################################################
def indexF6P(packet):
    logging.debug('BMBT - Index fields 6 press (%s)', packet)
    buttonIO.indexF6P()

def indexF6H(packet):
    logging.debug('BMBT - Index fields 6 hold (%s)', packet)

def indexF6R(packet):
    logging.debug('BMBT - Index fields 6 released (%s)', packet)


# IndexF7 ##################################################################
def indexF7P(packet):
    logging.debug('BMBT - Index fields 7 press (%s)', packet)
    buttonIO.indexF7P()

def indexF7H(packet):
    logging.debug('BMBT - Index fields 7 hold (%s)', packet)

def indexF7R(packet):
    logging.debug('BMBT - Index fields 7 released (%s)', packet)


# IndexF8 ##################################################################
def indexF8P(packet):
    logging.debug('BMBT - Index fields 8 press (%s)', packet)
    buttonIO.indexF8P()

def indexF8H(packet):
    logging.debug('BMBT - Index fields 8 hold (%s)', packet)

def indexF8R(packet):
    logging.debug('BMBT - Index fields 8 released (%s)', packet)


# IndexF9 ##################################################################
def indexF9P(packet):
    logging.debug('BMBT - Index fields 9 press (%s)', packet)
    buttonIO.indexF9P()

def indexF9H(packet):
    logging.debug('BMBT - Index fields 9 hold (%s)', packet)

def indexF9R(packet):
    logging.debug('BMBT - Index fields 9 released (%s)', packet)


# Wheel R/T ################################################################
def wheelRT(packet):
    logging.debug('Multifunction steering wheel - R/T (%s)', packet)
    buttonIO.wheelRT()


# Wheel voice ##############################################################
def wheelVoiceP(packet):
    logging.debug('Multifunction steering wheel - voice press (%s)', packet)
    buttonIO.wheelVoiceP()

def wheelVoiceH(packet):
    logging.debug('Multifunction steering wheel - voice hold (%s)', packet)
    buttonIO.wheelVoiceH()

def wheelVoiceR(packet):
    logging.debug('Multifunction steering wheel - voice release (%s)', packet)
    buttonIO.wheelVoiceR()


# Wheel ">" ################################################################
def wheelArrowUP(packet):
    logging.debug('Multifunction steering wheel - ">" press (%s)', packet)
    buttonIO.wheelArrowUP()

def wheelArrowUH(packet):
    logging.debug('Multifunction steering wheel - ">" hold (%s)', packet)
    buttonIO.wheelArrowUH()

def wheelArrowUR(packet):
    logging.debug('Multifunction steering wheel - ">" release (%s)', packet)
    buttonIO.wheelArrowUR()


# Wheel "<" ################################################################
def wheelArrowDP(packet):
    logging.debug('Multifunction steering wheel - "<" press (%s)', packet)
    buttonIO.wheelArrowDP()

def wheelArrowDR(packet):
    logging.debug('Multifunction steering wheel - "<" hold (%s)', packet)
    buttonIO.wheelArrowDR()

def wheelArrowDR(packet):
    logging.debug('Multifunction steering wheel - "<" release (%s)', packet)
    buttonIO.wheelArrowDR()

############################################################################