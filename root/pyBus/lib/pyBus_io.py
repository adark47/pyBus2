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
import threading
from subprocess import Popen, PIPE

sys.path.append('/root/pyBus/lib/')

# Imports for the project
import pyBus_module_display as pB_display
import pyBus_module_audio as pB_audio
import pyBus_util as pB_util
import pyBus_cdc as pB_cdc
import pyBus_bluetooth as bt

############################################################################
# CONFIG
############################################################################

versionPB = 'v1.2'
WRITER = None
menuLevel = 'homeMain'
display = None
displayThread = None
ERROR = None
TrackInfo = None
TICK = 0.05  # sleep interval in seconds used after displaying a string (default 0.1)


############################################################################
# FUNCTIONS
############################################################################

def init(writer):
    global WRITER
    global display
    WRITER = writer

    pB_audio.init()
    display = pB_display.busWriter(WRITER)
    displayThread = DisplayIO()
    displayThread.start()


def end():
    if displayThread:
        displayThread.stop()
    pB_audio.end()
    logging.debug("Quitting Audio CLIENT")


def error(errorID):
    global ERROR
    ERROR = errorID


############################################################################
# Scroll text
############################################################################

class TextScroller:
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
# DISPLAY CLASS
############################################################################
# T0 Dialog / Name artist - song(Scroll)                 # Title field T0 - 11 characters
# T1 mp3 / waw / flac                                    # Title field T1 - 4 characters
# T2 OK / ER                                             # Title field T2 - 2 characters
# T3 Number of songs in the folder                       # Title field T3 - 4 characters
# T4 number of the playing song in the folder            # Title field T4 - 2 characters
# T5 Play / Stop / Pause / Status: / Error:              # Title field T5 - 7 characters
# T6 Bluetooth / AirPlay / Volumio                       # Title field T6 - 11 characters


def displayF(titleT0=None, titleT1=None, titleT2=None, titleT3=None, titleT4=None, titleT5=None, titleT6=None,
             indexF0=None, indexF1=None, indexF2=None, indexF3=None, indexF4=None,
             indexF5=None, indexF6=None, indexF7=None, indexF8=None, indexF9=None,
             clearScreen=False, refreshIndex=False):

    time.sleep(TICK)
    if clearScreen is True:
        display.clearScreen()
    time.sleep(TICK)
    if titleT0 is not None:
        display.writeTitleT0(titleT0)
    time.sleep(TICK)
    if titleT1 is not None:
        display.writeTitleT1(titleT1)
    time.sleep(TICK)
    if titleT3 is not None:
        display.writeTitleT3(titleT3)
    time.sleep(TICK)
    if titleT4 is not None:
        display.writeTitleT4(titleT4)
    time.sleep(TICK)
    if titleT6 is not None:
        display.writeTitleT6(titleT6)
    time.sleep(TICK)
    if ERROR is None:
        if titleT5 is not None:
            display.writeTitleT5(titleT5)
        if titleT2 is not None:
            display.writeTitleT2(titleT2)
    else:
        display.writeTitleT5('Error:')
        display.writeTitleT2(ERROR)
    time.sleep(TICK)

    time.sleep(TICK)
    if refreshIndex is True:
        display.refreshIndex()
    time.sleep(TICK)
    if indexF0 is not None:
        display.writeIndexF0(indexF0)
    time.sleep(TICK)
    if indexF1 is not None:
        display.writeIndexF1(indexF1)
    time.sleep(TICK)
    if indexF2 is not None:
        display.writeIndexF2(indexF2)
    time.sleep(TICK)
    if indexF3 is not None:
        display.writeIndexF3(indexF3)
    time.sleep(TICK)
    if indexF4 is not None:
        display.writeIndexF4(indexF4)
    time.sleep(TICK)
    if indexF5 is not None:
        display.writeIndexF5(indexF5)
    time.sleep(TICK)
    if indexF6 is not None:
        display.writeIndexF6(indexF6)
    time.sleep(TICK)
    if indexF7 is not None:
        display.writeIndexF7(indexF7)
    time.sleep(TICK)
    if indexF8 is not None:
        display.writeIndexF8(indexF8)
    time.sleep(TICK)
    if indexF9 is not None:
        display.writeIndexF9(indexF9)
    time.sleep(TICK)


class DisplayIO(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

############################################################################

    def run(self):
        global ERROR
        global versionPB
        global display
        logging.info('Display thread initialized')

        while True:
            if menuLevel == 'homeMain':             # HOME
                displayF(
                    titleT0='BMW-MULTIMEDIA',
                    titleT1='',
                    titleT2='OK',
                    titleT3=versionPB,
                    titleT4='',
                    titleT5='Status:',
                    titleT6='<======>',

                    indexF0='Volumio',
                    indexF1='Bluetooth',
                    indexF2='AirPlay',
                    indexF3='',
                    indexF4='',
                    indexF5='Reboot',
                    indexF6='Shutdown',
                    indexF7='',
                    indexF8='',
                    indexF9=''
                    )

            elif menuLevel == 'btMain':                 # Bluetooth Main
                displayF(
                    titleT0='%s - %s' % (pB_audio.getTrackInfo().get('artist'), pB_audio.getTrackInfo().get('title')),
                    titleT1='',
                    titleT2='OK',
                    titleT3=versionPB,
                    titleT4='',
                    titleT5='%s' % pB_audio.getTrackInfo().get('status'),
                    titleT6='Bluetooth',

                    indexF0='<-- Back --',
                    indexF1='Select device',
                    indexF2='Add a new device',
                    indexF3='',
                    indexF4='',
                    indexF5='',
                    indexF6='',
                    indexF7='',
                    indexF8='',
                    indexF9=''
                    )

            elif menuLevel == 'btSelectDevice':         # Bluetooth -> Select device
                pass

            elif menuLevel == 'btSelectedDevice':       # Bluetooth -> Select device -> selected device
                pass

            elif menuLevel == 'btNewDevice':            # Bluetooth -> Add a new device
                pass

            elif menuLevel == 'vlmMain':                # Volumio Main
                pass

            elif menuLevel == 'apMain':                 # AirPlay Main
                pass

    def stop(self):
        logging.info('Display shutdown')
        self._Thread__stop()


############################################################################
# BUTTON CLASS
############################################################################

class ButtonIO:
    def infoP(self):
        pass

    def infoH(self):
        pass

    def infoR(self):
        pass

    def button1P(self):
        pass

    def button1H(self):
        pass

    def button1R(self):
        pass

    def button2P(self):
        pass

    def button2H(self):
        pass

    def button2R(self):
        pass

    def button3P(self):
        pass

    def button3H(self):
        pass

    def button3R(self):
        pass

    def button4P(self):
        pass

    def button4H(self):
        pass

    def button4R(self):
        pass

    def button5P(self):
        pass

    def button5H(self):
        pass

    def button5R(self):
        pass

    def button6P(self):
        pass

    def button6H(self):
        pass

    def button6R(self):
        pass

    def ArrowLP(self):
        pass

    def ArrowLH(self):
        pass

    def ArrowLR(self):
        pass

    def ArrowRP(self):
        pass

    def ArrowRH(self):
        pass

    def ArrowRR(self):
        pass

    def ArrowP(self):
        pass

    def ArrowH(self):
        pass

    def ArrowR(self):
        pass

    def modeP(self):
        pass

    def modeH(self):
        pass

    def modeR(self):
        pass

    def slctIndexF0(self):
        global updateIndex
        global menuLevel
        if menuLevel == 'homeMain':                             # Home
            if pB_audio.setClient('vlm') is True:               # Set client Volumio
                menuLevel = 'vlmMain'                           # Home -> Volumio Main
                logging.debug('Set menu level: %s' % menuLevel)
                updateIndex = True
            else:
                id = 01
                error(id)
                logging.error('ERROR: %s' % id)
        elif menuLevel == 'btMain':                             # <-- Back --
            if pB_audio.setClient('vlm') is True:               # Set client Volumio
                menuLevel = 'homeMain'                          # Bluetooth Main -> Home
                logging.debug('Set menu level: %s' % menuLevel)
                updateIndex = True
            else:
                id = 04
                error(id)
                logging.error('ERROR: %s' % id)
        elif menuLevel == 'btSelectDevice':                     # <-- Back --
            menuLevel = 'btMain'                                # Select device -> Bluetooth Main
            logging.debug('Set menu level: %s' % menuLevel)
            updateIndex = True
        elif menuLevel == 'btNewDevice':                        # <-- Back --
            menuLevel = 'btSelectDevice'                        # Add a new device -> Select device
            logging.debug('Set menu level: %s' % menuLevel)
            updateIndex = True

    def slctIndexF1(self):
        global updateIndex
        global menuLevel
        if menuLevel == 'homeMain':                             # Home
            if pB_audio.setClient('bt') is True:                # Set client Bluetooth
                menuLevel = 'btMain'
                logging.debug('Set menu level: %s' % menuLevel)
                updateIndex = True
            else:
                id = 02
                error(id)
                logging.error('ERROR: %s' % id)
        elif menuLevel == 'btSelectDevice':
            menuLevel = 'btSelectDevice'                        # Bluetooth -> Select device
            logging.debug('Set menu level: %s' % menuLevel)
            updateIndex = True
        elif menuLevel == 'btSelectDevice':
            updateIndex = True

    def slctIndexF2(self):
        global updateIndex
        global menuLevel
        if menuLevel == 'homeMain':                             # Home
            if pB_audio.setClient('ap') is True:                # Set client AirPlay
                menuLevel = 'apMain'                            # Home -> AirPlay Main
                logging.debug('Set menu level: %s' % menuLevel)
                updateIndex = True
            else:
                id = 03
                error(id)
                logging.error('ERROR: %s' % id)
        elif menuLevel == 'btMain':
            menuLevel = 'btNewDevice'                           # Bluetooth Main -> Add a new device
            logging.debug('Set menu level: %s' % menuLevel)
            updateIndex = True
        elif menuLevel == 'btNewDevice':
            updateIndex = True

    def slctIndexF3(self):
        pass

    def slctIndexF4(self):
        pass

    def slctIndexF5(self):
        if menuLevel == 'homeMain':
            pB_audio.Reboot()

    def slctIndexF6(self):
        if menuLevel == 'homeMain':
            pB_audio.Shutdown()

    def slctIndexF7(self):
        pass

    def slctIndexF8(self):
        pass

    def slctIndexF9(self):
        pass

    def wheelRT(self):
        bt.connect()

    def wheelVoiceP(self):
        pass

    def wheelVoiceH(self):
        pass

    def wheelVoiceR(self):
        pass

    def wheelArrowUP(self):
        pass

    def wheelArrowUH(self):
        pass

    def wheelArrowUR(self):
        pass

    def wheelArrowDP(self):
        pass

    def wheelArrowDH(self):
        pass

    def wheelArrowDR(self):
        pass

############################################################################
