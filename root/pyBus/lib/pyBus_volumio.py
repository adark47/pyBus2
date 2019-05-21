#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
import os
import sys
import time
import signal
import logging
import json
from socket import error as SocketError
sys.path.append('/root/pyBus/lib/')
from socketIO_client import SocketIO, LoggingNamespace


############################################################################
# GLOBALS
############################################################################
HOST = 'localhost'
PORT = '3000'
PASSWORD = False
VOLUME = 50
socketIO = None
dictTrack = None

logging.getLogger('socketIO-client').setLevel(logging.DEBUG)


############################################################################
# FUNCTIONS
############################################################################

def init():
    global socketIO
    logging.info('Initializing: Volumio player')
    socketIO = SocketIO(HOST, PORT)
    logging.info('Connected to Volumio player')
    getState()
    logging.debug('Get information from Volumio player')
    VolumeSet(VOLUME)
    logging.debug('The Volumio volume is set to: ', VOLUME)


def end():
    logging.info('End: module Volumio')


def _browseState(*args):
    global dictTrack
    dictTrack = {}
    dictTrack.clear()
    for key, value in args[0].items():
        print("%s: %s" % (key, value))
        dictTrack[key] = value


def getTrackInfo():
    getState()
    return dictTrack


def getState():
    socketIO.on('pushState', _browseState)
    socketIO.emit('getState', _browseState)
    socketIO.wait(seconds=0.1)


def _browseSources(*args):
    global dataSources
    dataSources = args
    print dataSources

    for plugin_type in dataSources[0]:
        print ('=========================')
        print plugin_type['plugin_type']
        print plugin_type['uri']
        print ('=========================')


def getBrowseSources(uri):
    socketIO.on('pushBrowseSources', _browseSources)
    socketIO.emit('getBrowseSources', {'uri': uri})
    socketIO.wait(seconds=1)


def _browseLibrary(*args):
    global dataLibrary
    dataLibrary = args
    print dataLibrary

    for library in dataLibrary[0]['navigation']['lists'][0]['items']:
        print ('=========================')
        print library['service']
        print library['title']
        print library['type']
        print library['uri']
        print ('=========================')


def browseLibrary(uri):
    socketIO.on('pushBrowseLibrary', _browseLibrary)
    socketIO.emit('browseLibrary', {'uri': uri})
    socketIO.wait(seconds=1)


def _browseQueue(*args):
    global dataQueue
    dataQueue = args
    print dataQueue

    for queue in dataQueue[0]:
        print ('=========================')
        print queue['artist']
        print queue['name']
        print queue['album']
        print queue['trackType']
        print queue['service']
        print queue['uri']
        print ('=========================')


def getQueue():
    socketIO.on('pushQueue', _browseQueue)
    socketIO.emit('getQueue', _browseQueue)
    socketIO.wait(seconds=1)


def clearQueue():
    socketIO.emit('clearQueue')


def addToQueue(uri):
    socketIO.emit('addToQueue', {'uri': uri})

############################################################################
# CONTROL
############################################################################

def Play():
    socketIO.emit('play')
    logging.debug('Through Volumio sent status: Play')


def PlayN(n):
    socketIO.emit('play', n)
#    socketIO.emit('play', {"value": n})


def Stop():
    socketIO.emit('stop')
    logging.debug('Volumio sent status: Stop')


def Pause():
    socketIO.emit('pause')
    logging.debug('Volumio sent status: Pause')


def Next():
    socketIO.emit('next')
    logging.debug('Volumio sent status: Next')


def Prev():
    socketIO.emit('prev')
    logging.debug('Volumio sent status: Prev')


def RewindPrev():
    socketIO.emit('getState', _browseState)
    socketIO.wait(seconds=0.1)
    socketIO.emit('seek', max(getTrackInfo()['seek'] / 1000 - 10, 0))
    logging.debug('Volumio sent status: RewindPrev')


def RewindNext():
    socketIO.emit('getState', _browseState)
    socketIO.wait(seconds=0.1)
    socketIO.emit('seek', getTrackInfo()['seek'] / 1000 + 10)
    logging.debug('Volumio sent status: RewindNext')


def Repeat():
    pass


def Random():
    if getTrackInfo()['random'] == True:
        socketIO.emit('setRandom', 'false')
        return True
    elif getTrackInfo()['random'] == False:
        socketIO.emit('setRandom', {'value': 'true'})
        return False
    else:
        logging.debug('not supported Random status:', getTrackInfo()['random'])


def VolumeSet(volume):
    socketIO.emit('volume', volume)
    logging.debug('Volumio sent status: Volume Set ', volume)


def VolumeUp():
    socketIO.emit('volume', '+')
    logging.debug('Volumio sent status: Volume Up')


def VolumeDown():
    socketIO.emit('volume', '-')
    logging.debug('Volumio sent status: Volume Down')

############################################################################
#
############################################################################

def Reboot():
    socketIO.emit('reboot')
    logging.info('Reboot command sent')


def Shutdown():
    socketIO.emit('shutdown')
    logging.info('Shutdown command sent')