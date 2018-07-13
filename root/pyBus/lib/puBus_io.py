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
import pyBus_module_audio2 as pB_audio
import pyBus_utilities as pB_util
import pyBus_cdc as pB_cdc

############################################################################
# CONFIG
############################################################################

WRITER = None
MENU = None

############################################################################
# FUNCTIONS
############################################################################

def init(writer):
    global WRITER, SESSION_DATA
    WRITER = writer

    display = pB_display.busWriter(WRITER)
    pB_audio.init()
    MENU = IO()
    MENU.start()

def end():
    if MENU:
        MENU.stop()

    pB_audio.end()
    logging.debug("Quitting Audio CLIENT")
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
# Scroll text
############################################################################

class IO(threading.Thread):
    def __init__(self, ibus):
        self.IBUS = ibus

        threading.Thread.__init__(self)

def test():
    pass

############################################################################

    def run(self):
        logging.info('Display thread initialized')
        while True:
            pass


    def stop(self):
        logging.info('Display shutdown')
        self.IBUS = None
        self._Thread__stop()








infoP
infoH
infoR

button1P
button1H
button1R

button2P
button2H
button2R

button3P
button3H
button3R

button4P
button4H
button4R

button5P
button5H
button5R

button6P
button6H
button6R

ArrowLP
ArrowLH
ArrowLR
ArrowRP
ArrowRH
ArrowRR

ArrowP
ArrowH
ArrowR

modeP
modeH
modeR

slctIndexF0
slctIndexF1
slctIndexF2
slctIndexF3
slctIndexF4
slctIndexF5
slctIndexF6
slctIndexF7
slctIndexF8
slctIndexF9

