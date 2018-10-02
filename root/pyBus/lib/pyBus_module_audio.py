#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
import os
import sys
import time
import signal
import logging
from socket import error as SocketError
sys.path.append('/root/pyBus/lib/')
import pyBus_bluetooth as bt
import pyBus_airplay as ap
import pyBus_volumio as vlm
import pyBus_mpd as mpd

############################################################################
# GLOBALS
############################################################################
HOST = 'localhost'
PORT = '3000'
PASSWORD = False

CLIENT = None
dictTrack = None

logging.getLogger('socketIO-client').setLevel(logging.DEBUG)


############################################################################
# FUNCTIONS
############################################################################

def init():
    global CLIENT
    logging.info('Initializing: module audio')
    bt.init()
    ap.init()
    vlm.init()
#    mpd.init()
    CLIENT = 'vlm'
    logging.info('Аudio client assigned: s%', CLIENT)



def end():
    bt.end()
    logging.info('End: module audio')

def getTrackInfo():
    if CLIENT == 'bluetooth':
       return bt.getTrackInfo()
    elif CLIENT == 'vlm':
        return vlm.getTrackInfo()
    elif CLIENT == 'airplay':
        return ap.getTrackInfo()
#    elif CLIENT == 'mpd':
#        return mpd.getTrackInfo()
    else:
        pass


def getClient():
    return CLIENT


def setClient(client):
    global CLIENT

    if CLIENT == 'bluetooth':
        bt.Stop()
        bt.disconnect()
        time.sleep(1)
        CLIENT = client
        logging.debug('Control the player assigned: s%', CLIENT)

    elif client == 'vlm':
        vlm.Stop()
        time.sleep(1)
        CLIENT = client
        logging.debug('Control the player assigned: s%', CLIENT)

    elif client == 'airplay':
        ap.Stop()
        time.sleep(1)
        CLIENT = client
        logging.debug('Control the player assigned: s%', CLIENT)

    elif client == 'mpd':
        mpd.Stop()
        time.sleep(1)
        CLIENT = client
        logging.debug('Control the player assigned: s%', CLIENT)

    else:
        CLIENT = None
        logging.error('Control the player is not assigned')

############################################################################
# CONTROL
############################################################################

def Play():
    if CLIENT == 'vlm':
        vlm.Play()
    elif CLIENT == 'airplay':
        ap.Play()
    elif CLIENT == 'bluetooth':
        bt.Play()
#    elif CLIENT == 'mpd':
#        mpd.Play()
    else:
        logging.debug('not supported service: s%', CLIENT)


def PlayN(n):
    if CLIENT == 'vlm':
        vlm.PlayN(n)
#        socketIO.emit('play', {"value": n})
    else:
        logging.debug('not supported service: s%', CLIENT)


def Stop():
    if CLIENT == 'vlm':
        vlm.Stop()
    elif CLIENT == 'airplay':
        ap.Stop()
    elif CLIENT == 'bluetooth':
        bt.Stop()
#    elif CLIENT == 'mpd':
#        mpd.Stop()
    else:
        logging.debug('not supported service: s%', CLIENT)


def Pause():
    if CLIENT == 'vlm':
        vlm.Pause()
    elif CLIENT == 'airplay':
        ap.Pause()
    elif CLIENT == 'bluetooth':
        bt.Pause()
#    elif CLIENT == 'mpd':
#        mpd.Pause()
    else:
        logging.debug('not supported service: s%', CLIENT)


def Next():
    if CLIENT == 'vlm':
        vlm.Next()
    elif CLIENT == 'airplay':
        ap.Next()
    elif CLIENT == 'bluetooth':
        bt.Next()
#    elif CLIENT == 'mpd':
#        mpd.Next()
    else:
        logging.debug('not supported service: s%', CLIENT)


def Prev():
    if CLIENT == 'vlm':
        vlm.Prev()
    elif CLIENT == 'airplay':
        ap.Prev()
    elif CLIENT == 'bluetooth':
        bt.Prev()
#    elif CLIENT == 'mpd':
#        mpd.Prev()
    else:
        logging.debug('not supported service: s%', CLIENT)


def RewindPrev():
    if CLIENT == 'vlm':
        vlm.RewindPrev()
    elif CLIENT == 'airplay':
        ap.RewindPrev()
    elif CLIENT == 'bluetooth':
        bt.RewindPrev()
#    elif CLIENT == 'mpd':
#        pass
    else:
        logging.debug('not supported service: s%', CLIENT)


def RewindNext():
    if CLIENT == 'vlm':
        vlm.RewindNext()
    elif CLIENT == 'airplay':
        ap.RewindNext()
    elif CLIENT == 'bluetooth':
        bt.RewindNext()
#    elif CLIENT == 'mpd':
#        pass
    else:
        logging.debug('not supported service: s%', CLIENT)


def RewindPlayResume():
    if CLIENT == 'airplay':
        ap.RewindPlayResume()
    else:
        logging.debug('not supported service: s%', CLIENT)


def Repeat():
    pass


def Random():
    if CLIENT == 'vlm':
        vlm.Random()
    elif CLIENT == 'airplay':
        ap.Random()
#    elif CLIENT == 'mpd':
#        pass
    else:
        logging.debug('not supported service: s%', CLIENT)


############################################################################