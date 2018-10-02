#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
sys.path.append('/root/pyBus/lib')

import pyBus_module_display as pB_display
from pyBus_interface import *

DEVPATH = '/dev/ttyUSB0'
IBUS = None

while IBUS is None:
    if os.path.exists(DEVPATH):
        IBUS = ibusFace(DEVPATH)
    else:
        logging.warning('USB interface not found at (%s). Waiting 1 seconds.', DEVPATH)
        time.sleep(2)
IBUS.waitClearBus()

display = pB_display.busWriter(IBUS)

############################################################################
# TEST #####################################################################
############################################################################

display.clearScreen()
display.refreshIndex()
display.updateScreen()
display.radioMenuDisable()
display.radioMenuEnable()
display.screenSwitchedNav()
display.screenSwitchedRadio()
