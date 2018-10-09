#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
sys.path.append('/root/pyBus/lib')
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

############################################################################
# TEST #####################################################################
############################################################################

#clearScreen
IBUS.writeBusPacket('68', '3B', ['46', '0C'])

#refreshIndex
IBUS.writeBusPacket('68', '3B', ['A5', '60', '01', '00'])

#updateScreen
IBUS.writeBusPacket('68', '3B', ['A5', '62', '01'])

#radioMenuDisable
IBUS.writeBusPacket('3B', '68', ['45', '02'])

#radioMenuEnable
IBUS.writeBusPacket('3B', '68', ['45', '00'])

#screenSwitchedNav
IBUS.writeBusPacket('68', '3B', ['46', '01'])

#screenSwitchedRadio
IBUS.writeBusPacket('68', '3B', ['46', '02'])