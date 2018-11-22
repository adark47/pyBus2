#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
sys.path.append('/root/pyBus/lib')
from pyBus_interface import *

DEVPATH = '/dev/ttyUSB0'
IBUS = None

while IBUS is None:
    if os.path.exists(DEVPATH):
        IBUS = ibusFace(DEVPATH)
    else:
        print 'USB interface not found at (%s). Waiting 1 seconds.', DEVPATH
        time.sleep(2)
IBUS.waitClearBus()

############################################################################
# TEST #####################################################################
############################################################################

IBUS.writeBusPacket('68', '3B', ['46', '0C'])               #clearScreen

IBUS.writeBusPacket('68', '3B', ['A5', '60', '01', '00'])   #refreshIndex

IBUS.writeBusPacket('68', '3B', ['A5', '62', '01'])         #updateScreen

IBUS.writeBusPacket('3B', '68', ['45', '02'])               #radioMenuDisable

IBUS.writeBusPacket('3B', '68', ['45', '00'])               #radioMenuEnable

IBUS.writeBusPacket('68', '3B', ['46', '01'])               #screenSwitchedNav

IBUS.writeBusPacket('68', '3B', ['46', '02'])               #screenSwitchedRadio

############################################################################

IBUS.writeBusPacket('C8', 'E7', ['2B', '00'])               # Telephone LED All_off         # C8 E7 2B 00

IBUS.writeBusPacket('C8', 'E7', ['2B', '01'])               # Telephone LED red, solid      # C8 E7 2B 01

IBUS.writeBusPacket('C8', 'E7', ['2B', '02'])               # Telephone LED red, flash      # C8 E7 2B 02

IBUS.writeBusPacket('C8', 'E7', ['2B', '04'])               # Telephone LED yellow, solid   # C8 E7 2B 04

IBUS.writeBusPacket('C8', 'E7', ['2B', '08'])               # Telephone LED yellow, flash   # C8 E7 2B 08

IBUS.writeBusPacket('C8', 'E7', ['2B', '10'])               # Telephone LED green, solid    # C8 E7 2B 10

IBUS.writeBusPacket('C8', 'E7', ['2B', '20'])               # Telephone LED green, flash    # C8 E7 2B 20

IBUS.writeBusPacket('C8', 'E7', ['2С', '01'])               # Handsfree                     # C8 E7 2C 01

IBUS.writeBusPacket('C8', 'E7', ['2С', '02'])  # Active call (false = phone menu displayed) #  C8 E7 2C 02

IBUS.writeBusPacket('C8', 'E7', ['2С', '04'])               # Incoming call                 # C8 E7 2C 04

IBUS.writeBusPacket('C8', 'E7', ['2С', '08'])               # Phone screen disabled         # C8 E7 2C 08

IBUS.writeBusPacket('C8', 'E7', ['2С', '10'])               # Phone on                      # C8 E7 2C 10

IBUS.writeBusPacket('C8', 'E7', ['2С', '20'])               # Phone active                  # C8 E7 2C 20

IBUS.writeBusPacket('C8', 'E7', ['2С', '40'])               # Phone adapter installed       # C8 E7 2C 40

# bit_0 = 0x01;
# bit_1 = 0x02;
# bit_2 = 0x04;
# bit_3 = 0x08;
# bit_4 = 0x10;
# bit_5 = 0x20;
# bit_6 = 0x40;
# bit_7 = 0x80;

