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
updateIndex = True
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
    displayThread = displayIO()
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

class displayIO(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

############################################################################

    def run(self):
        global updateIndex
        global ERROR
        global versionPB
        global display
        logging.info('Display thread initialized')

        while True:
            if menuLevel == 'homeMain':  # HOME
                display.writeTitleT0('BMW-MUSIC')
                time.sleep(TICK)
                display.writeTitleT1(' ')
                time.sleep(TICK)
                display.writeTitleT3(versionPB)
                time.sleep(TICK)
                display.writeTitleT4(' ')
                time.sleep(TICK)
                display.writeTitleT6('Not chosen')
                time.sleep(TICK)
                if ERROR is None:
                    display.writeTitleT5('Status:')
                    time.sleep(TICK)
                    display.writeTitleT2('OK')
                    time.sleep(TICK)
                else:
                    display.writeTitleT5('Error:')
                    time.sleep(TICK)
                    display.writeTitleT2(ERROR)
                    time.sleep(TICK)

                if updateIndex is True:
                    display.refreshIndex()
                    time.sleep(TICK)
                    display.writeIndexF0('Volumio')
                    time.sleep(TICK)
                    display.writeIndexF1('Bluetooth')
                    time.sleep(TICK)
                    display.writeIndexF2('AirPlay')
                    time.sleep(TICK)
                    display.writeIndexF3('')
                    time.sleep(TICK)
                    display.writeIndexF4('')
                    time.sleep(TICK)
                    display.writeIndexF5('Reboot')
                    time.sleep(TICK)
                    display.writeIndexF6('Shutdown')
                    time.sleep(TICK)
                    display.writeIndexF7('')
                    time.sleep(TICK)
                    display.writeIndexF8('')
                    time.sleep(TICK)
                    display.writeIndexF9('')
                    time.sleep(TICK)
                    updateIndex = False

            elif menuLevel == 'btMain':     # Bluetooth Main
                display.writeTitleT0('%s - %s' % (pB_audio.getTrackInfo().get('artist'),
                                                  pB_audio.getTrackInfo().get('title')))
                time.sleep(TICK)
                display.writeTitleT1(' ')
                time.sleep(TICK)
                display.writeTitleT3(' ')
                time.sleep(TICK)
                display.writeTitleT4(' ')
                time.sleep(TICK)
                display.writeTitleT6('Bluetooth')
                time.sleep(TICK)
                if ERROR is None:
                    display.writeTitleT5('%s' % pB_audio.getTrackInfo().get('status'))
                    time.sleep(TICK)
                    display.writeTitleT2(' ')
                    time.sleep(TICK)
                else:
                    display.writeTitleT5('Error:')
                    time.sleep(TICK)
                    display.writeTitleT2(ERROR)
                    time.sleep(TICK)

                if updateIndex is True:
                    display.refreshIndex()
                    time.sleep(TICK)
                    display.writeIndexF0('<-- Back --')
                    time.sleep(TICK)
                    display.writeIndexF1('Select device')
                    time.sleep(TICK)
                    display.writeIndexF2('Add a new device')
                    time.sleep(TICK)
                    display.writeIndexF3('')
                    time.sleep(TICK)
                    display.writeIndexF4('')
                    time.sleep(TICK)
                    display.writeIndexF5('')
                    time.sleep(TICK)
                    display.writeIndexF6('')
                    time.sleep(TICK)
                    display.writeIndexF7('')
                    time.sleep(TICK)
                    display.writeIndexF8(' ')
                    time.sleep(TICK)
                    display.writeIndexF9('')
                    time.sleep(TICK)
                    updateIndex = False

            elif menuLevel == 'btSelectDevice':  # Bluetooth -> Select device
                pass

            elif menuLevel == 'btSelectedDevice':  # Bluetooth -> Select device -> selected device
                pass

            elif menuLevel == 'btNewDevice':  # Bluetooth -> Add a new device
                pass

            elif menuLevel == 'vlmMain':  # Volumio Main
                display.writeTitleT0('%s - %s' % (pB_audio.getTrackInfo().get('artist'),
                                                  pB_audio.getTrackInfo().get('title')))
                time.sleep(TICK)
                display.writeTitleT1(' ')
                time.sleep(TICK)
                display.writeTitleT3(' ')
                time.sleep(TICK)
                display.writeTitleT4(' ')
                time.sleep(TICK)
                display.writeTitleT6('Volumio')
                time.sleep(TICK)
                if ERROR is None:
                    display.writeTitleT5('%s' % pB_audio.getTrackInfo().get('status'))
                    time.sleep(TICK)
                    display.writeTitleT2(' ')
                    time.sleep(TICK)
                else:
                    display.writeTitleT5('Error:')
                    time.sleep(TICK)
                    display.writeTitleT2(ERROR)
                    time.sleep(TICK)

                if updateIndex is True:
                    display.refreshIndex()
                    time.sleep(TICK)
                    display.writeIndexF0('')
                    time.sleep(TICK)
                    display.writeIndexF1('')
                    time.sleep(TICK)
                    display.writeIndexF2('')
                    time.sleep(TICK)
                    display.writeIndexF3('')
                    time.sleep(TICK)
                    display.writeIndexF4('')
                    time.sleep(TICK)
                    display.writeIndexF5('')
                    time.sleep(TICK)
                    display.writeIndexF6('')
                    time.sleep(TICK)
                    display.writeIndexF7('')
                    time.sleep(TICK)
                    display.writeIndexF8(' ')
                    time.sleep(TICK)
                    display.writeIndexF9('')
                    time.sleep(TICK)
                    updateIndex = False

            elif menuLevel == 'apMain':  # AirPlay Main
                display.writeTitleT0('%s - %s' % (pB_audio.getTrackInfo().get('artist'),
                                                  pB_audio.getTrackInfo().get('title')))
                time.sleep(TICK)
                display.writeTitleT1(' ')
                time.sleep(TICK)
                display.writeTitleT3(' ')
                time.sleep(TICK)
                display.writeTitleT4(' ')
                time.sleep(TICK)
                display.writeTitleT6('AirPlay')
                time.sleep(TICK)
                if ERROR is None:
                    display.writeTitleT5('%s' % pB_audio.getTrackInfo().get('status'))
                    time.sleep(TICK)
                    display.writeTitleT2(' ')
                    time.sleep(TICK)
                else:
                    display.writeTitleT5('Error:')
                    time.sleep(TICK)
                    display.writeTitleT2(ERROR)
                    time.sleep(TICK)

                if updateIndex is True:
                    display.refreshIndex()
                    time.sleep(TICK)
                    display.writeIndexF0('')
                    time.sleep(TICK)
                    display.writeIndexF1('')
                    time.sleep(TICK)
                    display.writeIndexF2('')
                    time.sleep(TICK)
                    display.writeIndexF3('')
                    time.sleep(TICK)
                    display.writeIndexF4('')
                    time.sleep(TICK)
                    display.writeIndexF5('')
                    time.sleep(TICK)
                    display.writeIndexF6('')
                    time.sleep(TICK)
                    display.writeIndexF7('')
                    time.sleep(TICK)
                    display.writeIndexF8(' ')
                    time.sleep(TICK)
                    display.writeIndexF9('')
                    time.sleep(TICK)
                    updateIndex = False

    def stop(self):
        logging.info('Display shutdown')
        self._Thread__stop()


############################################################################
# BUTTON CLASS
############################################################################

class buttonIO:
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
