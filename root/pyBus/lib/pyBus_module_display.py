#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, time, signal, json, traceback, logging
import threading
import datetime

############################################################################
# WARNING: Behaviour of this module is going to be rebuilt entirely, it is moving towards spaghetti code.
############################################################################

############################################################################
# GLOBALS
############################################################################

TICK = 1  # sleep interval in seconds used after displaying a string from DISPLAY_QUE
WRITER = None  # Writer thread

MENU_LEVEL = False

textT0 = None
textT1 = None
textT2 = None
textT3 = None
textT4 = None
textT5 = None
textT6 = None

indexF0 = None
indexF1 = None
indexF2 = None
indexF3 = None
indexF4 = None
indexF5 = None
indexF6 = None
indexF7 = None
indexF8 = None
indexF9 = None

############################################################################
#
############################################################################

def init(IBUS):
    global WRITER
    WRITER = busWriter(IBUS)
    WRITER.start()


def end():
    if WRITER:
        WRITER.stop()

############################################################################
# FUNCTIONS
############################################################################
# Convert text to hex and prepends the required data for displaying text on the Radio

def _hexText(string, dataPacket ,max_stringlen):
    stringLen = 0
    logging.debug("Got string for hexing: %s", string)
    while (stringLen < max_stringlen) and (len(string) > 0):
        c = string[stringLen]  # stringLen doubles up as the index to use when retrieving characters of the string to be displayed.. apologies for how misleading this may be
        dataPacket.append('%02X' % (ord(c)))
        stringLen = stringLen + 1
        if (stringLen == len(string)):
            break
    return dataPacket

############################################################################
# Scroll text
############################################################################

class TextScroller:
    'Class for scrolling text'
    text = ''
    position = 0
    textLength = 0

    def __init__(self, initialText):
        self.text = initialText

    def scroll(self):
        doubleText = self.text + '    ' + self.text
        scrolledText = doubleText[self.position:len(doubleText)]
        self.position = self.position + 1

        # We add five extra spaces between each complete text scroll.
        if self.position > len(self.text) + 1:
            self.position = 0

        return scrolledText

    def setNewText(self, newText):
        self.text = newText
        self.position = 0

############################################################################
# TEXT
############################################################################

def immediateText(string):
    WRITER.immediate(string)

def immediateTextClear(string):
    WRITER.immediateClear()

# MK4 - Title ##############################################################

def setNewTextT0(string):
    global textT0
    textT0 = string

def setNewTextT1(string):
    global textT1
    textT1 = string

def setNewTextT2(string):
    global textT2
    textT2 = string

def setNewTextT3(string):
    global textT3
    textT3 = string

def setNewTextT4(string):
    global textT4
    textT4 = string

def setNewTextT5(string):
    global textT5
    textT5 = string

def setNewTextT6(string):
    global textT6
    textT6 = string

# MK4 - Index ##############################################################

def setNewIndexF0(string):
    global indexF0
    indexF0 = string
    WRITER.writeIndexF0(string)

def setNewIndexF1(string):
    global indexF1
    indexF1 = string
    WRITER.writeIndexF1(string)

def setNewIndexF2(string):
    global indexF2
    indexF2 = string
    WRITER.writeIndexF2(string)

def setNewIndexF3(string):
    global indexF3
    indexF3 = string
    WRITER.writeIndexF3(string)

def setNewIndexF4(string):
    global indexF4
    indexF4 = string
    WRITER.writeIndexF4(string)

def setNewIndexF5(string):
    global indexF5
    indexF5 = string
    WRITER.writeIndexF5(string)

def setNewIndexF6(string):
    global indexF6
    indexF6 = string
    WRITER.writeIndexF6(string)

def setNewIndexF7(string):
    global indexF7
    indexF7 = string
    WRITER.writeIndexF7(string)

def setNewIndexF8(string):
    global indexF8
    indexF8 = string
    WRITER.writeIndexF8(string)

def setNewIndexF9(string):
    global indexF9
    indexF9 = string
    WRITER.writeIndexF9(string)

def refreshIndexMK4():
    WRITER.refreshIndex()

############################################################################
# THREAD FOR TICKING AND WRITING
############################################################################

class busWriter(threading.Thread):
    def __init__(self, ibus):
        self.IBUS = ibus

        threading.Thread.__init__(self)

# Immediate Text ################

    # 12 characters
    def immediate(self, string):
        self.IBUS.writeBusPacket('C8', '80', _hexText(string, ['23', '42', '01'], 12))
        logging.debug('Immediate text - write Text: %s' %string)

    def immediateClear(self):
        self.IBUS.writeBusPacket('c8', '80', ['23', '42', '32', '1e'])
        logging.debug('Immediate text - Clear')

# MK4 - Title ######################################################################

    # Title field T0 - 11 characters
    # <68 xx 3B> <23 62 30> <Text in ASCII Hex>
    def writeTitleT0(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['23', '62', '30'], 11))
        logging.debug('MK4 - write TitleT0: %s' %string)

    # Title field T1 - 4 characters
    # <68 xx 3B> <A5 62 01> <01> <Text in ASCII Hex>
    def writeTitleT1(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '01'], 4))
        logging.debug('MK4 - write TitleT1: %s' %string)

    # Title field T2 - 2 characters
    # <68 xx 3B> <A5 62 01> <02> <Text in ASCII Hex>
    def writeTitleT2(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '02'], 2))
        logging.debug('MK4 - write TitleT2: %s' %string)

    # Title field T3 - 4 characters
    # <68 xx 3B> <A5 62 01> <03> <Text in ASCII Hex>
    def writeTitleT3(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '03'], 4))
        logging.debug('MK4 - write TitleT3: %s' %string)

    # Title field T4 - 2 characters
    # <68 xx 3B> <A5 62 01> <04> <Text in ASCII Hex>
    def writeTitleT4(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '04'], 2))
        logging.debug('MK4 - write TitleT4: %s' %string)

    # Title field T5 - 7 characters
    # <68 xx 3B> <A5 62 01> <05> <Text in ASCII Hex>
    def writeTitleT5(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '05'], 7))
        logging.debug('MK4 - write TitleT5: %s' %string)

    # Title field T6 - 11 characters
    # <68 xx 3B> <A5 62 01> <06> <Text in ASCII Hex>
    def writeTitleT6(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['A5', '62', '01', '06'], 11))
        logging.debug('MK4 - write TitleT6: %s' %string)

# MK4 - Index ######################################################################

    # Index fields 0 - 23 characters
    # <68 xx 3B> <21 60 00> <40> <Text in ASCII Hex>
    def writeIndexF0(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '40'], 23))
        logging.debug('MK4 - write IndexF0: %s' %string)

    # Index fields 1 - 23 characters
    # <68 xx 3B> <21 60 00> <41> <Text in ASCII Hex>
    def writeIndexF1(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '41'], 23))
        logging.debug('MK4 - write IndexF1: %s' %string)

    # Index fields 2 - 23 characters
    # <68 xx 3B> <21 60 00> <42> <Text in ASCII Hex>
    def writeIndexF2(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '42'], 23))
        logging.debug('MK4 - write IndexF2: %s' %string)

    # Index fields 3 - 23 characters
    # <68 xx 3B> <21 60 00> <43> <Text in ASCII Hex>
    def writeIndexF3(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '43'], 23))
        logging.debug('MK4 - write IndexF3: %s' %string)

    # Index fields 4 - 23 characters
    # <68 xx 3B> <21 60 00> <44> <Text in ASCII Hex>
    def writeIndexF4(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '44'], 23))
        logging.debug('MK4 - write IndexF4: %s' %string)

    # Index fields 5 - 23 characters
    # <68 xx 3B> <21 60 00> <45> <Text in ASCII Hex>
    def writeIndexF5(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '45'], 23))
        logging.debug('MK4 - write IndexF5: %s' %string)

    # Index fields 6 - 23 characters
    # <68 xx 3B> <21 60 00> <46> <Text in ASCII Hex>
    def writeIndexF6(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '46'], 23))
        logging.debug('MK4 - write IndexF6: %s' %string)

    # Index fields 7 - 23 characters
    # <68 xx 3B> <21 60 00> <47(07)>  <Text in ASCII Hex>
    def writeIndexF7(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '47'], 23))
        logging.debug('MK4 - write IndexF7: %s' %string)

    # Index fields 8 - 23 characters
    # <68 xx 3B> <21 60 00> <48> <Text in ASCII Hex>
    def writeIndexF8(self, string):
        self.IBUS.writeBusPacket('68', '3B', _hexText(string, ['21', '60', '00', '48'], 23))
        logging.debug('MK4 - write IndexF8: %s' %string)

    # Index fields 9 - 23 characters
    # <68 xx 3B> <21 60 00> <49> <Text in ASCII Hex>
    def writeIndexF9(self, string):
        self.IBUS.writeBusPacket('18', '68', _hexText(string, ['21', '60', '00', '49'], 23))
        logging.debug('MK4 - write IndexF9: %s' %string)

    # To refresh the index fields
    # <68 06 3B> <A5 60 01 00 91>
    def refreshIndex(self):
        self.IBUS.writeBusPacket('68', '3B', ['A5', '60', '01', '00', '91'])
        logging.debug('MK4 - refresh Index')

############################################################################

    def run(self):
        logging.info('Display thread initialized')
        while True:

# MK4 - Title ######################################################################

            if textT0 != None:
                busWriter.writeTitleT0(self, textT0)

            if textT1 != None:
                busWriter.writeTitleT1(self, textT1)

            if textT2 != None:
                busWriter.writeTitleT2(self, textT2)

            if textT3 != None:
                busWriter.writeTitleT3(self, textT3)

            if textT4 != None:
                busWriter.writeTitleT4(self, textT4)

            if textT5 != None:
                busWriter.writeTitleT5(self, textT5)

            if textT6 != None:
                busWriter.writeTitleT6(self, textT6)

# MK4 - Index ######################################################################

#            if IndexF0 != None:
#                busWriter.writeIndexF0(self, indexF0)

#            if IndexF1 != None:
#                busWriter.writeIndexF1(self, indexF1)

#            if IndexF2 != None:
#                busWriter.writeIndexF2(self, indexF2)

#            if IndexF3 != None:
#                busWriter.writeIndexF3(self, indexF3)

#            if IndexF4 != None:
#                busWriter.writeIndexF4(self, indexF4)

#            if IndexF5 != None:
#                busWriter.writeIndexF5(self, indexF5)

#            if IndexF6 != None:
#                busWriter.writeIndexF6(self, indexF6)

#            if IndexF7 != None:
#                busWriter.writeIndexF7(self, indexF7)

#            if IndexF8 != None:
#                busWriter.writeIndexF8(self, indexF8)

#            if IndexF9 != None:
#                busWriter.writeIndexF9(self, indexF9)


    def stop(self):
        logging.info('Display shutdown')
        self.IBUS = None
        self._Thread__stop()

############################################################################

############################################################################

