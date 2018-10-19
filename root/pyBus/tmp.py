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

# tail -f /root/pyBus.log | grep READ | grep "'3B', '06', '68'"

# Index fields 0 press      # 3B 06 68 31 60 00 00 04
# Index fields 0 hold       #
# Index fields 0 released   # 3B 06 68 31 60 00 40 44

# Index fields 1 press      # 3B 06 68 31 60 00 01 05
# Index fields 1 hold       #
# Index fields 1 released   # 3B 06 68 31 60 00 41 45

# Index fields 2 press      #
# Index fields 2 hold       #
# Index fields 2 released   #

# Index fields 3 press      #
# Index fields 3 hold       #
# Index fields 3 released   #

# Index fields 4 press      #
# Index fields 4 hold       #
# Index fields 4 released   #

# Index fields 5 press      #
# Index fields 5 hold       #
# Index fields 5 released   #

# Index fields 6 press      #
# Index fields 6 hold       #
# Index fields 6 released   #

# Index fields 7 press      #
# Index fields 7 hold       #
# Index fields 7 released   #

# Index fields 8 press      #
# Index fields 8 hold       #
# Index fields 8 released   #

# Index fields 9 press      #
# Index fields 9 hold       #
# Index fields 9 released   #
