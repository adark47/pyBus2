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
#    displayThread.isAlive()


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
             clearScreen=False, updateScreen=False, refreshIndex=False):

    time.sleep(TICK)
    if clearScreen is True:
        display.clearScreen()
    if updateScreen is True:
        display.updateScreen()
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
        display.clearScreen()
        display.radioMenuDisable()

        while True:
            if menuLevel == 'homeMain':             # HOME
                displayF(
                    titleT0='BMW-MULTIMEDIA',
                    titleT1='',
                    titleT3=versionPB,
                    titleT4='',
                    titleT5='Status:',
                    titleT6='          ',

                    indexF0='Volumio',
                    indexF1='Bluetooth',
                    indexF2='AirPlay',
                    indexF3='',
                    indexF4='',
                    indexF5='Reboot',
                    indexF6='Shutdown',
                    indexF7='',
                    indexF8='',
                    indexF9='',
                    )

            elif menuLevel == 'btMain':                 # Bluetooth Main
                displayF(
                    titleT0=('%s - %s', pB_audio.getTrackInfo().get('artist'), pB_audio.getTrackInfo().get('title')),
                    titleT1='',
                    titleT3=versionPB,
                    titleT4='',
                    titleT5=('%s', pB_audio.getTrackInfo().get('status')),
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
                    indexF9='',
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
        display.clearScreen()
        display.radioMenuEnable()
        self._Thread__stop()


############################################################################
# BUTTON CLASS
############################################################################

class ButtonIO:
# Info #####################################################################
    def infoP(self):
        pass

    def infoH(self):
        pass

    def infoR(self):
        pass


# Button 1 #################################################################
    def button1P(self):
        pass

    def button1H(self):
        pass

    def button1R(self):
        pass


# Button 2 #################################################################
    def button2P(self):
        pass

    def button2H(self):
        pass

    def button2R(self):
        pass


# Button 3 #################################################################
    def button3P(self):
        pass

    def button3H(self):
        pass

    def button3R(self):
        pass


# Button 4 #################################################################
    def button4P(self):
        pass

    def button4H(self):
        pass

    def button4R(self):
        pass


# Button 5 #################################################################
    def button5P(self):
        pass

    def button5H(self):
        pass

    def button5R(self):
        pass


# Button 6 #################################################################
    def button6P(self):
        pass

    def button6H(self):
        pass

    def button6R(self):
        pass


# "<" Arrow Left ###########################################################
    def arrowLP(self):
        pass

    def arrowLH(self):
        pass

    def arrowLR(self):
        pass


# ">" Arrow Left ###########################################################
    def arrowRP(self):
        pass

    def arrowRH(self):
        pass

    def arrowRR(self):
        pass


# "<>" Arrow Left ##########################################################
    def arrowP(self):
        pass

    def arrowH(self):
        pass

    def arrowR(self):
        pass


# MODE #####################################################################
    def modeP(self):
        pass

    def modeH(self):
        pass

    def modeR(self):
        pass


# IndexF0 ##################################################################
    def indexF0P(self):
        global menuLevel
        if menuLevel == 'homeMain':                             # Home
            display.clearScreen()
            if pB_audio.setClient('vlm') is True:               # Set client Volumio
                menuLevel = 'vlmMain'                           # Home -> Volumio Main
                logging.debug('Set menu level: %s', menuLevel)
            else:
                id = 01
                error(id)
                logging.error('ERROR: %s', id)
        elif menuLevel == 'btMain':                             # <-- Back --
            display.clearScreen()
            if pB_audio.setClient('vlm') is True:               # Set client Volumio
                menuLevel = 'homeMain'                          # Bluetooth Main -> Home
                logging.debug('Set menu level: %s', menuLevel)
            else:
                id = 04
                error(id)
                logging.error('ERROR: %s', id)
        elif menuLevel == 'btSelectDevice':                     # <-- Back --
            display.clearScreen()
            menuLevel = 'btMain'                                # Select device -> Bluetooth Main
            logging.debug('Set menu level: %s', menuLevel)
        elif menuLevel == 'btNewDevice':                        # <-- Back --
            display.clearScreen()
            menuLevel = 'btSelectDevice'                        # Add a new device -> Select device
            logging.debug('Set menu level: %s', menuLevel)

    def indexF0H(self):
        pass

    def indexF0R(self):
        pass


# IndexF1 ##################################################################
    def indexF1P(self):
        global menuLevel
        if menuLevel == 'homeMain':                             # Home
            display.clearScreen()
            if pB_audio.setClient('bt') is True:                # Set client Bluetooth
                menuLevel = 'btMain'
                logging.debug('Set menu level: %s', menuLevel)
            else:
                id = 02
                error(id)
                logging.error('ERROR: %s', id)
        elif menuLevel == 'btSelectDevice':
            display.clearScreen()
            menuLevel = 'btSelectDevice'                        # Bluetooth -> Select device
            logging.debug('Set menu level: %s', menuLevel)
        elif menuLevel == 'btSelectDevice':
            display.clearScreen()

    def indexF1H(self):
        pass

    def indexF1R(self):
        pass


# IndexF2 ##################################################################
    def indexF2P(self):
        global updateIndex
        global menuLevel
        if menuLevel == 'homeMain':                             # Home
            display.clearScreen()
            if pB_audio.setClient('ap') is True:                # Set client AirPlay
                menuLevel = 'apMain'                            # Home -> AirPlay Main
                logging.debug('Set menu level: %s', menuLevel)
            else:
                id = 03
                error(id)
                logging.error('ERROR: %s', id)
        elif menuLevel == 'btMain':
            display.clearScreen()
            menuLevel = 'btNewDevice'                           # Bluetooth Main -> Add a new device
            logging.debug('Set menu level: %s', menuLevel)
        elif menuLevel == 'btNewDevice':
            display.clearScreen()

    def indexF2H(self):
        pass

    def indexF2R(self):
        pass


# IndexF3 ##################################################################
    def indexF3P(self):
        pass

    def indexF3H(self):
        pass

    def indexF3R(self):
        pass


# IndexF4 ##################################################################
    def indexF4P(self):
        pass

    def indexF4H(self):
        pass

    def indexF4R(self):
        pass


# IndexF5 ##################################################################
    def indexF5P(self):
        if menuLevel == 'homeMain':
            pB_audio.Reboot()

    def indexF5H(self):
        pass

    def indexF5R(self):
        pass


# IndexF6 ##################################################################
    def indexF6P(self):
        if menuLevel == 'homeMain':
            pB_audio.Shutdown()

    def indexF6H(self):
        pass

    def indexF6R(self):
        pass


# IndexF7 ##################################################################
    def indexF7P(self):
        pass

    def indexF7H(self):
        pass

    def indexF7R(self):
        pass


# IndexF8 ##################################################################
    def indexF8P(self):
        pass

    def indexF8H(self):
        pass

    def indexF8R(self):
        pass


# IndexF9 ##################################################################
    def indexF9P(self):
        pass

    def indexF9H(self):
        pass

    def indexF9R(self):
        pass


# Wheel R/T ################################################################
    def wheelRT(self):
        bt.connect()


# Wheel voice ##############################################################
    def wheelVoiceP(self):
        pass

    def wheelVoiceH(self):
        pass

    def wheelVoiceR(self):
        pass


# Wheel ">" ################################################################
    def wheelArrowUP(self):
        pass

    def wheelArrowUH(self):
        pass

    def wheelArrowUR(self):
        pass


# Wheel "<" ################################################################
    def wheelArrowDP(self):
        pass

    def wheelArrowDH(self):
        pass

    def wheelArrowDR(self):
        pass

############################################################################
