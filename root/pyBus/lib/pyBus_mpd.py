#!/usr/bin/python

# The MPD module has practically no documentation as far as I know.. so a lot of this is guess-work, albeit educated guess-work
import pprint
import os
import sys
import time
import signal
import logging
from mpd import (MPDClient, CommandError)
from socket import error as SocketError

# import pyBus_core as core

#####################################
# GLOBALS
#####################################
HOST = 'localhost'
PORT = '6600'
PASSWORD = False
CON_ID = {'host': HOST, 'port': PORT}
VOLUME = 90

MPD = None
PLAYLIST = None
LIBRARY = None
T_STATUS = None
VOLUME = 85
ROOT_DIR = '/media'

#####################################
# FUNCTIONS
#####################################
def mpdConnect(client, con_id):
    try:
        client.connect(**con_id)
    except SocketError:
        return False
    return True


def init():
    global MPD, PLAYLIST, LIBRARY
    ## MPD object instance
    MPD = MPDClient()
    if mpdConnect(MPD, CON_ID):
        logging.info('Connected to MPD server')
        MPD.setvol(VOLUME)
        logging.debug('The MPD volume is set to: ', VOLUME)
        PLAYLIST = MPD.playlistinfo()
        LIBRARY = MPD.listallinfo()

        Repeat(True)  # Repeat all tracks
    else:
        logging.critical('Failed to connect to MPD server')
        logging.critical("Sleeping 1 second and retrying")
        time.sleep(1)
        init()


# Updates MPD library
def update():
    logging.info('Updating MPD Library')
    MPD.update()
    LIBRARY = MPD.listallinfo()
    PLAYLIST = MPD.playlistinfo()


def addAll():
    MPD.clear()  # Clear current playlist
    MPD.add('/')  # Add all songs in library (TEMP)


def end():
    if MPD:
        MPD.disconnect()

############################################################################
# FUNCTIONS PLAYER
############################################################################

def Play():
    MPD.play()
    logging.debug('Bluetooth sent status: Play')


def Stop():
    if MPD:
        MPD.stop()
        logging.debug('Bluetooth sent status: Stop')


def Pause():
    MPD.pause()
    logging.debug('Bluetooth sent status: Pause')


def Next():
    MPD.next()
    logging.debug('Bluetooth sent status: Next')


def Prev():
    MPD.previous()
    logging.debug('Bluetooth sent status: Previous')


def Repeat(repeat, toggle=False):
    if toggle:
        current = int(MPD.status()['repeat'])
        repeat = (not current)  # Love this
    MPD.repeat(int(repeat))
    logging.debug('Bluetooth sent status: Repeat')
    return repeat


def Random(random, toggle=False):
    if toggle:
        current = int(MPD.status()['random'])
        random = (not current)  # Love this
    MPD.random(int(random))
    logging.debug('Bluetooth sent status: Random')
    return random


def Seek(delta):
    try:
        seekDest = int(float(MPD.status()['elapsed']) + delta)
        playListID = int(MPD.status()['song'])
        MPD.seek(playListID, seekDest)
    except Exception, e:
        logging.warning("Issue seeking - elapsed key missing")


def getTrackInfo():
    global T_STATUS
    currentTID = getTrackID()
    for song in PLAYLIST:
        trackID = song["id"]
        if trackID == currentTID:
            T_STATUS = song


def getInfo(lastID=-1):
    global MPD
    if MPD == None:
        init()
    state = None
    while not state:
        try:
            state = MPD.status()
        except Exception, e:
            logging.warning("MPD lost connection while reading status")
            time.sleep(.5)
            MPD == None

    if (state['state'] != "stop"):
        if ("songid" in state):
            songID = state['songid']
            if (songID != lastID):
                getTrackInfo()
        if (T_STATUS == None):
            getTrackInfo()
    status = {"status": state, "track": T_STATUS}
    logging.debug("Player Status Requested. Returning:")
    logging.debug(status)
    return status


def getInfoByPath(filePath):
    for song in PLAYLIST:
        path = song["file"]
        if path == filePath:
            return song


def addSong(filepath):
    global PLAYLIST
    if (getInfoByPath(filepath) == None):
        MPD.add(filepath)
        PLAYLIST = MPD.playlistinfo()


def removeSong(filepath):
    global PLAYLIST
    song = getInfoByPath(filepath)
    MPD.deleteid(song['id'])
    PLAYLIST = MPD.playlistinfo()


def playSong(filepath):
    song = getInfoByPath(filepath)
    MPD.playid(song['id'])


def getPlaylist():
    return PLAYLIST


def getLibrary():
    return LIBRARY


def getTrackID():
    if ("songid" not in MPD.status()):
        logging.warning("MPD status does not contain songID. Please investigate following status:")
        logging.warning(MPD.status())
    try:
        currentTID = MPD.status()['songid']
        return currentTID
    except e:
        logging.warning("Unexpected Exception occured:")
        logging.warning(traceback.format_exc())
        return 0