#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
sys.path.append('/root/pyBus/lib')
from pyBus_interface import *

DEVPATH = '/dev/ttyUSB0'
IBUS = None

while IBUS is None:
    if os.path.exists(DEVPATH):
        IBUS = ibusFace(DEVPATH)
    else:
        print 'USB interface not found at (%s). Waiting 1 seconds.', DEVPATH
        time.sleep(2)
IBUS.waitClearBus()

############################################################################
# TEST #####################################################################
############################################################################
IBUS.writeBusPacket('18', 'FF', ['02', '01'])

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

# tail -f /root/pyBus.log | grep READ | grep "'41', '55', '58'"
# tail -f /root/pyBus.log | grep READ | grep "'3B', '06', '68'"


# bit_0 = 0x01;
# bit_1 = 0x02;
# bit_2 = 0x04;
# bit_3 = 0x08;
# bit_4 = 0x10;
# bit_5 = 0x20;
# bit_6 = 0x40;
# bit_7 = 0x80;

