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

############################################################################
# FUNCTIONS
############################################################################

def init(writer):
    global WRITER, SESSION_DATA
    WRITER = writer

    pB_display.init(WRITER)
    pB_audio.init()


class MENU(object):
    pass