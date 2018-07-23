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

############################################################################
# CONFIG
############################################################################

versionPB = 'v1.1'
WRITER = None
menuLevel = 'homeMain'
display = None
displayThread = None
ERROR = None
TrackInfo = None
TICK = 0.2  # sleep interval in seconds used after displaying a string (default 1)


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
# DISPLAY CLASS
############################################################################
def displayF(titleT0, titleT1, titleT2, titleT3, titleT4, titleT5, titleT6,
             indexF0, indexF1, indexF2, indexF3, indexF4, indexF5, indexF6, indexF7, indexF8, indexF9,
             updateIndex=False):

    display.writeTitleT0(titleT0)   # Title field T0 - 11 characters
    time.sleep(TICK)
    display.writeTitleT1(titleT1)   # Title field T1 - 4 characters
    time.sleep(TICK)
    display.writeTitleT3(titleT3)   # Title field T3 - 4 characters
    time.sleep(TICK)
    display.writeTitleT4(titleT4)   # Title field T4 - 2 characters
    time.sleep(TICK)
    display.writeTitleT6(titleT6)   # Title field T6 - 11 characters
    time.sleep(TICK)
    if ERROR is None:
        display.writeTitleT5(titleT5)   # Title field T5 - 7 characters
        time.sleep(TICK)
        display.writeTitleT2(titleT2)   # Title field T2 - 2 characters
        time.sleep(TICK)
    else:
        display.writeTitleT5('Error:')
        time.sleep(TICK)
        display.writeTitleT2(ERROR)
        time.sleep(TICK)

    if updateIndex is True:
        display.refreshIndex()

    time.sleep(TICK)
    display.writeIndexF0(indexF0)
    time.sleep(TICK)
    display.writeIndexF1(indexF1)
    time.sleep(TICK)
    display.writeIndexF2(indexF2)
    time.sleep(TICK)
    display.writeIndexF3(indexF3)
    time.sleep(TICK)
    display.writeIndexF4(indexF4)
    time.sleep(TICK)
    display.writeIndexF5(indexF5)
    time.sleep(TICK)
    display.writeIndexF6(indexF6)
    time.sleep(TICK)
    display.writeIndexF7(indexF7)
    time.sleep(TICK)
    display.writeIndexF8(indexF8)
    time.sleep(TICK)
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
            if menuLevel == 'homeMain':  # HOME
                displayF(
                    titleT0='BMW-MUSIC',
                    titleT1='_',
                    titleT2='OK',
                    titleT3=versionPB,
                    titleT4='_',
                    titleT5='Status:',
                    titleT6='<======>',

                    indexF0='Volumio',
                    indexF1='Bluetooth',
                    indexF2='AirPlay',
                    indexF3='_',
                    indexF4='_',
                    indexF5='Reboot',
                    indexF6='Shutdown',
                    indexF7='_',
                    indexF8='_',
                    indexF9='_'
                    )

            elif menuLevel == 'btMain':     # Bluetooth Main
                displayF(
                    titleT0='%s - %s' % (pB_audio.getTrackInfo().get('artist'), pB_audio.getTrackInfo().get('title')),
                    titleT1='_',
                    titleT2='OK',
                    titleT3=versionPB,
                    titleT4='_',
                    titleT5='%s' % pB_audio.getTrackInfo().get('status'),
                    titleT6='Bluetooth',

                    indexF0='<-- Back --',
                    indexF1='Select device',
                    indexF2='Add a new device',
                    indexF3='_',
                    indexF4='_',
                    indexF5='_',
                    indexF6='_',
                    indexF7='',
                    indexF8='_',
                    indexF9='_'
                    )

            elif menuLevel == 'btSelectDevice':  # Bluetooth -> Select device
                pass

            elif menuLevel == 'btSelectedDevice':  # Bluetooth -> Select device -> selected device
                pass

            elif menuLevel == 'btNewDevice':  # Bluetooth -> Add a new device
                pass

            elif menuLevel == 'vlmMain':  # Volumio Main
                pass

            elif menuLevel == 'apMain':  # AirPlay Main
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
        if menuLevel == 'homeMain':  # Home
            if pB_audio.setClient('vlm') is True:  # Set client Volumio
                menuLevel = 'vlmMain'  # Home -> Volumio Main
                logging.debug('Set menu level: %s' % menuLevel)
                updateIndex = True
            else:
                id = 01
                error(id)
                logging.error('ERROR: %s' % id)
        elif menuLevel == 'btMain':  # <-- Back --
            if pB_audio.setClient('vlm') is True:  # Set client Volumio
                menuLevel = 'homeMain'  # Bluetooth Main -> Home
                logging.debug('Set menu level: %s' % menuLevel)
                updateIndex = True
            else:
                id = 04
                error(id)
                logging.error('ERROR: %s' % id)
        elif menuLevel == 'btSelectDevice':  # <-- Back --
            menuLevel = 'btMain'  # Select device -> Bluetooth Main
            logging.debug('Set menu level: %s' % menuLevel)
            updateIndex = True
        elif menuLevel == 'btNewDevice':  # <-- Back --
            menuLevel = 'btSelectDevice'  # Add a new device -> Select device
            logging.debug('Set menu level: %s' % menuLevel)
            updateIndex = True

    def slctIndexF1(self):
        global updateIndex
        global menuLevel
        if menuLevel == 'homeMain':  # Home
            if pB_audio.setClient('bt') is True:  # Set client Bluetooth
                menuLevel = 'btMain'
                logging.debug('Set menu level: %s' % menuLevel)
                updateIndex = True
            else:
                id = 02
                error(id)
                logging.error('ERROR: %s' % id)
        elif menuLevel == 'btSelectDevice':
            menuLevel = 'btSelectDevice'  # Bluetooth -> Select device
            logging.debug('Set menu level: %s' % menuLevel)
            updateIndex = True
        elif menuLevel == 'btSelectDevice':
            updateIndex = True

    def slctIndexF2(self):
        global updateIndex
        global menuLevel
        if menuLevel == 'homeMain':  # Home
            if pB_audio.setClient('ap') is True:  # Set client AirPlay
                menuLevel = 'apMain'  # Home -> AirPlay Main
                logging.debug('Set menu level: %s' % menuLevel)
                updateIndex = True
            else:
                id = 03
                error(id)
                logging.error('ERROR: %s' % id)
        elif menuLevel == 'btMain':
            menuLevel = 'btNewDevice'  # Bluetooth Main -> Add a new device
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
        pass

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
