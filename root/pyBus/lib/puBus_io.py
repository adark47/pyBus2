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
menuLevel = None
threadDisplay = None

############################################################################
# FUNCTIONS
############################################################################

def init(writer):
    global WRITER
    WRITER = writer

    display = pB_display.busWriter(WRITER)
    pB_audio.init()
    threadDisplay = displayIO()
    threadDisplay.start()

def end():
    if threadDisplay:
        threadDisplay.stop()

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

class displayIO(threading.Thread):
    def __init__(self):
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
        self._Thread__stop()


class buttonIO(object):

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
        pass
    def slctIndexF1(self):
        pass
    def slctIndexF2(self):
        pass
    def slctIndexF3(self):
        pass
    def slctIndexF4(self):
        pass
    def slctIndexF5(self):
        pass
    def slctIndexF6(self):
        pass
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
