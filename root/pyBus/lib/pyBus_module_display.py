#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import signal
import json
import traceback
import logging
import threading
import datetime

############################################################################
# GLOBALS
############################################################################

WRITER = None  # Writer thread

############################################################################
# FUNCTIONS
############################################################################
# Convert text to hex and prepends the required data for displaying text on the Radio

def _hexText(string, dataPacket ,max_stringlen):
    stringLen = 0
    logging.debug('Got string for hexing: %s', string)
    while (stringLen < max_stringlen) and (len(string) > 0):
        # stringLen doubles up as the index to use when retrieving characters of
        #  the string to be displayed.. apologies for how misleading this may be
        c = string[stringLen]
        dataPacket.append('%02X' % (ord(c)))
        stringLen = stringLen + 1
        if (stringLen == len(string)):
            break
    return dataPacket

############################################################################
# TEXT DISPLAY
############################################################################

class busWriter:
    def __init__(self, ibus):
        self.IBUS = ibus

# IKEConsole LCD  #######################################################################

    # Text IKEConsole LCD - 12 characters
    def textIKE(self, string):
        self.IBUS.writeBusPacket('C8', '80', _hexText(string, ['23', '42', '01'], 12))
        logging.debug('Immediate text - write Text: %s', string)

    # Clear IKEConsole LCD
    def clearIKE(self):
        self.IBUS.writeBusPacket('c8', '80', ['23', '42', '32', '1e'])
        logging.debug('Immediate text - Clear')

# MK4 - Title ######################################################################

    # Title field T0 - 11 characters
    # <68 xx 3B> <23 62 30> <Text in ASCII Hex>
    def writeTitleT0(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['23', '62', '30'], 11))
        #self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['23', '62', '10'], 11))
        logging.debug('MK4 - write TitleT0: %s', string)

    # Title field T1 - 4 characters
    # <68 xx 3B> <A5 62 01> <01> <Text in ASCII Hex>
    def writeTitleT1(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '01'], 4))
        logging.debug('MK4 - write TitleT1: %s', string)

    # Title field T2 - 2 characters
    # <68 xx 3B> <A5 62 01> <02> <Text in ASCII Hex>
    def writeTitleT2(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '02'], 2))
        logging.debug('MK4 - write TitleT2: %s', string)

    # Title field T3 - 4 characters
    # <68 xx 3B> <A5 62 01> <03> <Text in ASCII Hex>
    def writeTitleT3(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '03'], 4))
        logging.debug('MK4 - write TitleT3: %s', string)

    # Title field T4 - 2 characters
    # <68 xx 3B> <A5 62 01> <04> <Text in ASCII Hex>
    def writeTitleT4(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '04'], 2))
        logging.debug('MK4 - write TitleT4: %s', string)

    # Title field T5 - 7 characters
    # <68 xx 3B> <A5 62 01> <05> <Text in ASCII Hex>
    def writeTitleT5(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '05'], 7))
        logging.debug('MK4 - write TitleT5: %s', string)

    # Title field T6 - 11 characters
    # <68 xx 3B> <A5 62 01> <06> <Text in ASCII Hex>
    def writeTitleT6(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '06'], 11))
        logging.debug('MK4 - write TitleT6: %s', string)

# MK4 - Index ######################################################################

    # Index fields 0 - 23 characters
    # <68 xx 3B> <21 60 00> <40> <Text in ASCII Hex>
    def writeIndexF0(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '40'], 23))
        logging.debug('MK4 - write IndexF0: %s', string)

    # Index fields 1 - 23 characters
    # <68 xx 3B> <21 60 00> <41> <Text in ASCII Hex>
    def writeIndexF1(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '41'], 23))
        logging.debug('MK4 - write IndexF1: %s', string)

    # Index fields 2 - 23 characters
    # <68 xx 3B> <21 60 00> <42> <Text in ASCII Hex>
    def writeIndexF2(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '42'], 23))
        logging.debug('MK4 - write IndexF2: %s', string)

    # Index fields 3 - 23 characters
    # <68 xx 3B> <21 60 00> <43> <Text in ASCII Hex>
    def writeIndexF3(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '43'], 23))
        logging.debug('MK4 - write IndexF3: %s', string)

    # Index fields 4 - 23 characters
    # <68 xx 3B> <21 60 00> <44> <Text in ASCII Hex>
    def writeIndexF4(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '44'], 23))
        logging.debug('MK4 - write IndexF4: %s', string)

    # Index fields 5 - 23 characters
    # <68 xx 3B> <21 60 00> <45> <Text in ASCII Hex>
    def writeIndexF5(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '45'], 23))
        logging.debug('MK4 - write IndexF5: %s', string)

    # Index fields 6 - 23 characters
    # <68 xx 3B> <21 60 00> <46> <Text in ASCII Hex>
    def writeIndexF6(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '46'], 23))
        logging.debug('MK4 - write IndexF6: %s', string)

    # Index fields 7 - 23 characters
    # <68 xx 3B> <21 60 00> <47(07)>  <Text in ASCII Hex>
    def writeIndexF7(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '47'], 23))
        logging.debug('MK4 - write IndexF7: %s', string)

    # Index fields 8 - 23 characters
    # <68 xx 3B> <21 60 00> <48> <Text in ASCII Hex>
    def writeIndexF8(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '48'], 23))
        logging.debug('MK4 - write IndexF8: %s', string)

    # Index fields 9 - 23 characters
    # <68 xx 3B> <21 60 00> <49> <Text in ASCII Hex>
    def writeIndexF9(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '49'], 23))
        logging.debug('MK4 - write IndexF9: %s', string)

# MK4 - ############################################################################

    # To refresh the index fields
    # <68 06 3B> <A5 60 01 00 91>
    def refreshIndex(self):
        self.IBUS.writeBusPacket('68', '3B', ['A5', '60', '01', '00'])
        logging.debug('MK4 - refresh Index')

    def updateScreen(self):
        self.IBUS.writeBusPacket('68', '3B', ['A5', '62', '01'])
        logging.debug('MK4 - update Screen')

    def clearScreen(self):
        self.IBUS.writeBusPacket('68', '3B', ['46', '0C'])
        logging.debug('MK4 - clear Screen')

    def radioMenuDisable(self):
        self.IBUS.writeBusPacket('3B', '68', ['45', '02'])
        logging.debug('MK4 - radio menu disable')

    def radioMenuEnable(self):
        self.IBUS.writeBusPacket('3B', '68', ['45', '00'])
        logging.debug('MK4 - radio menu enable')

    def screenSwitchedNav(self):
        self.IBUS.writeBusPacket('68', '3B', ['46', '01'])
        logging.debug('MK4 - screen switched Nav')

    def screenSwitchedRadio(self):
        self.IBUS.writeBusPacket('68', '3B', ['46', '02'])
        logging.debug('MK4 - screen switched Radio')

############################################################################