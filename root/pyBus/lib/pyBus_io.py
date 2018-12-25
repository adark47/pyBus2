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
#import pyBus_dia as pB_dia
#import pyBus_cdc as pB_cdc
#import pyBus_tel as pB_tel
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
#        display.clearScreen()
        display.radioMenuDisable()

        while True:
            if menuLevel == 'homeMain':                             # HOME
                displayF(
                    titleT0='BMW-MULTIMEDIA',
                    titleT1='',
                    titleT3=versionPB,
                    titleT4='',
                    titleT5='Status:',
                    titleT6='',

                    indexF0='Volumio',
                    indexF1='Bluetooth',
                    indexF2='AirPlay',
                    indexF3='_test_',
                    indexF4='_test_',
                    indexF5='Reboot',
                    indexF6='Shutdown',
                    indexF7='_test_',
                    indexF8='_test_',
                    indexF9='_test_',
                    )

            elif menuLevel == 'btMain':                             # Bluetooth Main
                displayF(
                    titleT0=('%s - %s', pB_audio.getTrackInfo().get('artist'), pB_audio.getTrackInfo().get('title')),
                    titleT1='',
                    titleT3=versionPB,
                    titleT4='',
                    titleT5=('%s', pB_audio.getTrackInfo().get('status')),
                    titleT6='Bluetooth',

                    indexF0='<< Back',
                    indexF1='Сonnect to the last device',
                    indexF2='Disconnect the connected device',
                    indexF3='Choose from the list of devices',
                    indexF4='Add a new device',
                    indexF5='Bluetooth service',
                    indexF6='',
                    indexF7='',
                    indexF8='',
                    indexF9='',
                    )

            elif menuLevel == 'btConnectLastDeviceTrue':            # Bluetooth -> Сonnect to the last device - True
                displayF(
                    titleT0=('Сonnect to the last device'),
                    titleT1='',
                    titleT3=versionPB,
                    titleT4='',
                    titleT5='',
                    titleT6='Bluetooth',

                    indexF0='Mac addr',
                    indexF1='CONNECTED',
                    indexF2='',
                    indexF3='',
                    indexF4='',
                    indexF5='',
                    indexF6='',
                    indexF7='',
                    indexF8='',
                    indexF9='',
                    )

            elif menuLevel == 'btConnectLastDeviceFalse':           # Bluetooth -> Сonnect to the last device - False
                displayF(
                    titleT0=('Сonnect to the last device'),
                    titleT1='',
                    titleT3=versionPB,
                    titleT4='',
                    titleT5='',
                    titleT6='Bluetooth',

                    indexF0='Mac addr',
                    indexF1='NOT CONNECTED',
                    indexF2='',
                    indexF3='',
                    indexF4='',
                    indexF5='',
                    indexF6='',
                    indexF7='',
                    indexF8='',
                    indexF9='',
                    )

            elif menuLevel == 'btDisconnectDevice':            #  Bluetooth Main -> Disconnect the connected device
                displayF(
                    titleT0=('Disconnect the connected device'),
                    titleT1='',
                    titleT3=versionPB,
                    titleT4='',
                    titleT5='',
                    titleT6='Bluetooth',

                    indexF0='Mac addr',
                    indexF1='DISCONNECTED',
                    indexF2='',
                    indexF3='',
                    indexF4='',
                    indexF5='',
                    indexF6='',
                    indexF7='',
                    indexF8='',
                    indexF9='',
                    )

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

    def selectButton(self, button):
        global menuLevel
        global ERROR

        # Info #####################################################################
        if button == 'infoP':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'infoH':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'infoR':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # Button 1 #################################################################
        elif button == 'button1P':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button1H':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button1R':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # Button 2 #################################################################
        elif button == 'button2P':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button2H':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button2R':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # Button 3 #################################################################
        elif button == 'button3P':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button3H':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button3R':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # Button 4 #################################################################
        elif button == 'button4P':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button4H':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button4R':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # Button 5 #################################################################
        elif button == 'button5P':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button5H':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button5R':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # Button 6 #################################################################
        elif button == 'button6P':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button6H':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'button6R':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # "<" Arrow Left ###########################################################
        elif button == 'arrowLP':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'arrowLH':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'arrowLR':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # ">" Arrow Left ###########################################################
        elif button == 'arrowRP':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'arrowRH':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'arrowRR':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # "<>" Arrow Left ##########################################################
        elif button == 'arrowP':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'arrowH':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'arrowR':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # MODE #####################################################################
        elif button == 'modeP':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'modeH':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'modeR':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        ############################################################################
        else:
            logging.error('BMBT - Unknown button: %s, menu level: %s', button, menuLevel)


    def selectWheelButton(self, button):
        global menuLevel
        global ERROR

        # Wheel R/T ################################################################
        if button == 'wheelRT':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
            if bt.connect() is True:
                pass
            else:
                time.sleep(5)
                bt.connect()

        # Wheel voice ##############################################################
        elif button == 'wheelVoiceP':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'wheelVoiceH':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'wheelVoiceR':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # Wheel ">" ################################################################
        elif button == 'wheelArrowUP':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'wheelArrowUH':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'wheelArrowUR':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        # Wheel "<" ################################################################
        elif button == 'wheelArrowDP':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'wheelArrowDH':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        elif button == 'wheelArrowDR':
            logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

        ############################################################################
        else:
            logging.error('BMBT - Unknown button: %s, menu level: %s', button, menuLevel)


    def selectIndex(self, button):
        global menuLevel
        global ERROR

        if menuLevel == 'homeMain':     # Home
            # IndexF0 ##################################################################
            if button == 'indexF0P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
                if pB_audio.setClient('vlm') is True:       # Set client Volumio
                    menuLevel = 'vlmMain'                   # Home -> Volumio Main
                    logging.debug('Set menu level: %s', menuLevel)

            elif button == 'indexF0H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF0R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF1 ##################################################################
            elif button == 'indexF1P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
                if pB_audio.setClient('bluetooth') is True:     # Set client Bluetooth
                    menuLevel = 'btMain'
                    logging.debug('Set menu level: %s', menuLevel)

            elif button == 'indexF1H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF1R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF2 ##################################################################
            elif button == 'indexF2P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF2H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF2R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF3 ##################################################################
            elif button == 'indexF3P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
                if pB_audio.setClient('airplay') is True:       # Set client AirPlay
                    menuLevel = 'apMain'                        # Home -> AirPlay Main
                    logging.debug('Set menu level: %s', menuLevel)

            elif button == 'indexF3H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF3R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF4 ##################################################################
            elif button == 'indexF4P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF4H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF4R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF5 ##################################################################
            elif button == 'indexF5P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
                pB_audio.Reboot()

            elif button == 'indexF5H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF5R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF6 ##################################################################
            elif button == 'indexF6P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
                pB_audio.Shutdown()

            elif button == 'indexF6H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF6R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF7 ##################################################################
            elif button == 'indexF7P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF7H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF7R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF8 ##################################################################
            elif button == 'indexF8P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF8H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF8R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF9 ##################################################################
            elif button == 'indexF9P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF9H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF9R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            ############################################################################
            else:
                logging.error('BMBT - Unknown button: %s, menu level: %s', button, menuLevel)


        elif menuLevel == 'vlmMain':     # Home
            # IndexF0 ##################################################################
            if button == 'indexF0P':                                 # << Back
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
                if pB_audio.setClient('vlm') is True:               # Set client Volumio
                    menuLevel = 'homeMain'                          # Volumio Main -> Home
                    logging.debug('Set menu level: %s', menuLevel)

            elif button == 'indexF0H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF0R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF1 ##################################################################
            elif button == 'indexF1P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF1H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF1R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF2 ##################################################################
            elif button == 'indexF2P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF2H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF2R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF3 ##################################################################
            elif button == 'indexF3P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF3H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF3R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF4 ##################################################################
            elif button == 'indexF4P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF4H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF4R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF5 ##################################################################
            elif button == 'indexF5P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF5H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF5R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF6 ##################################################################
            elif button == 'indexF6P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF6H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF6R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF7 ##################################################################
            elif button == 'indexF7P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF7H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF7R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF8 ##################################################################
            elif button == 'indexF8P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF8H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF8R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF9 ##################################################################
            elif button == 'indexF9P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF9H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF9R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            ############################################################################
            else:
                logging.error('BMBT - Unknown button: %s, menu level: %s', button, menuLevel)


        elif menuLevel == 'btMain':     # Home
            # IndexF0 ##################################################################
            if button == 'indexF0P':                                # << Back
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
                if pB_audio.setClient('vlm') is True:               # Set client Volumio
                    menuLevel = 'homeMain'                          # Bluetooth Main -> Home
                    logging.debug('Set menu level: %s', menuLevel)

            elif button == 'indexF0H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF0R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF1 ##################################################################
            elif button == 'indexF1P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
                if bt.connect() is True:
                    menuLevel == 'btConnectLastDeviceTrue'          # Bluetooth -> Сonnect to the last device - True
                    logging.debug('Set menu level: %s', menuLevel)
                else:
                    menuLevel == 'btConnectLastDeviceFalse'         # Bluetooth -> Сonnect to the last device - False
                    logging.debug('Set menu level: %s', menuLevel)
                time.sleep(5)
                menuLevel = 'btMain'                                # Сonnect to the last device -> Bluetooth Main
                logging.debug('Set menu level: %s', menuLevel)

            elif button == 'indexF1H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF1R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF2 ##################################################################
            elif button == 'indexF2P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
                bt.disconnect()
                menuLevel = 'btDisconnectDevice'                    # Bluetooth Main -> Disconnect the connected device
                logging.debug('Set menu level: %s', menuLevel)
                time.sleep(5)
                menuLevel = 'btMain'                                # Сonnect to the last device -> Bluetooth Main
                logging.debug('Set menu level: %s', menuLevel)

            elif button == 'indexF2H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF2R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF3 ##################################################################
            elif button == 'indexF3P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF3H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF3R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF4 ##################################################################
            elif button == 'indexF4P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF4H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF4R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF5 ##################################################################
            elif button == 'indexF5P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF5H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF5R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF6 ##################################################################
            elif button == 'indexF6P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF6H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF6R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF7 ##################################################################
            elif button == 'indexF7P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF7H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF7R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF8 ##################################################################
            elif button == 'indexF8P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF8H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF8R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF9 ##################################################################
            elif button == 'indexF9P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF9H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF9R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            ############################################################################
            else:
                logging.error('BMBT - Unknown button: %s, menu level: %s', button, menuLevel)


        elif menuLevel == 'apMain':     # Home
            # IndexF0 ##################################################################
            if button == 'indexF0P':                                # << Back
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)
                if pB_audio.setClient('vlm') is True:               # Set client Volumio
                    menuLevel = 'homeMain'                          # AirPlay Main -> Home
                    logging.debug('Set menu level: %s', menuLevel)

            elif button == 'indexF0H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF0R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF1 ##################################################################
            elif button == 'indexF1P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF1H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF1R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF2 ##################################################################
            elif button == 'indexF2P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF2H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF2R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF3 ##################################################################
            elif button == 'indexF3P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF3H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF3R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF4 ##################################################################
            elif button == 'indexF4P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF4H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF4R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF5 ##################################################################
            elif button == 'indexF5P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF5H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF5R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF6 ##################################################################
            elif button == 'indexF6P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF6H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF6R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF7 ##################################################################
            elif button == 'indexF7P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF7H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF7R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF8 ##################################################################
            elif button == 'indexF8P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF8H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF8R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            # IndexF9 ##################################################################
            elif button == 'indexF9P':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF9H':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            elif button == 'indexF9R':
                logging.debug('BMBT - Select button: %s, menu level: %s', button, menuLevel)

            ############################################################################
            else:
                logging.error('BMBT - Unknown button: %s, menu level: %s', button, menuLevel)

############################################################################
