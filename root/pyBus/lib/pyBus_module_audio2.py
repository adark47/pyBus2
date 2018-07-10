#!/usr/bin/python

import pprint, os, sys, time, signal, logging
from socket import error as SocketError
sys.path.append('/root/pyBus/lib/')
from socketIO_client import SocketIO, LoggingNamespace
import pyBus_bluetooth as bt

############################################################################
# GLOBALS
############################################################################
HOST = 'localhost'
PORT = '3000'
PASSWORD = False
VOLUME = 85
CLIENT = None
socketIO = None
dictTrack = None

logging.getLogger('socketIO-client').setLevel(logging.DEBUG)


############################################################################
# FUNCTIONS
############################################################################

def init():
    global socketIO
    socketIO = SocketIO(HOST, PORT)
    bt.init()
    setClient('vlm')
    logging.info('Connected to Volumio player')
    getState()
    logging.debug('Get information from Volumio player')
    VolumeSet()
    logging.debug('Setting the volume of Volumio player to: ', CLIENT)


def _browseState(*args):
    global dictTrack
    dictTrack = {}
    dictTrack.clear()
    for key, value in args[0].items():
        print("%s: %s" % (key, value))
        dictTrack[key] = value


def getTrackInfo():
    if CLIENT == 'bluetooth':

        btDictTrack = {}
        btDictTrack.setdefault('status').append(str(bt.getTrackInfo().get('Status')))
        btDictTrack.setdefault('album', []).append(str(bt.getTrackInfo().get('Album')))
        btDictTrack.setdefault('artist', []).append(str(bt.getTrackInfo().get('Artist')))
        btDictTrack.setdefault('title', []).append(str(bt.getTrackInfo().get('Title')))
        btDictTrack.setdefault('repeat', []).append(str(bt.getTrackInfo().get('Repeat')))
        btDictTrack.setdefault('random', []).append(str(bt.getTrackInfo().get('Shuffle')))
        btDictTrack.setdefault('trackType', []).append(str(bt.getTrackInfo().get('Type')))
#        btDictTrack.setdefault('service', []).append(bt.getTrackInfo().get('Name'))
        btDictTrack.setdefault('uri', []).append(str(bt.getTrackInfo().get('Device')))
        btDictTrack.setdefault('numberOfTracks', []).append(str(bt.getTrackInfo().get('NumberOfTracks')))
        btDictTrack.setdefault('trackNumber', []).append(str(bt.getTrackInfo().get('TrackNumber')))

        return btDictTrack
    else:
        return dictTrack


def getState():
    socketIO.on('pushState', _browseState)
    socketIO.emit('getState', _browseState)
    socketIO.wait(seconds=0.1)


def setClient(client):
    global CLIENT

    if client == 'vlm':
        if CLIENT == 'bluetooth':
            bt.Stop()
            bt.disconnect()
            time.sleep(1)
            CLIENT = 'vlm'
            logging.debug('Control the player assigned: ', CLIENT)
        else:
            Stop()
            time.sleep(1)
            CLIENT = 'vlm'
            logging.debug('Control the player assigned: ', CLIENT)

    elif client == 'airplay':
        if CLIENT == 'bluetooth':
            bt.Stop()
            bt.disconnect()
            time.sleep(1)
            CLIENT = 'airplay'
            logging.debug('Control the player assigned: ', CLIENT)
        else:
            Stop()
            time.sleep(1)
            CLIENT = 'airplay'
            logging.debug('Control the player assigned: ', CLIENT)

    elif client == 'bluetooth':
        Stop()
        time.sleep(1)
        if bt.connect() == True:
            CLIENT = 'bluetooth'
            logging.debug('Control the player assigned: ', CLIENT)
        elif bt.connect() == False:
            CLIENT = 'vlm'  # default client
            logging.debug('Control the player assigned: ', CLIENT)
        else:
            logging.error('Control the player is not assigned')


    else:
        CLIENT = None
        logging.error('Control the player is not assigned')


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
    if CLIENT == 'vlm':
        socketIO.emit('play')
        logging.debug('Through Volumio sent status: Play')
    elif CLIENT == 'airplay':
        os.system('/bin/echo -ne play | /bin/nc -u localhost 3391 -q 1')
        logging.debug('Through AirPlay sent status: Play')
    elif CLIENT == 'bluetooth':
        bt.Play()
        logging.debug('Through Bluetooth sent status: Play')
    else:
        logging.debug('not supported service:', CLIENT)


def PlayN(n):
    if CLIENT == 'vlm':
        socketIO.emit('play', n)
#        socketIO.emit('play', {"value": n})
    else:
        logging.debug('not supported service:', CLIENT)

def Stop():
    if CLIENT == 'vlm':
        socketIO.emit('stop')
        logging.debug('Through Volumio sent status: Stop')
    elif CLIENT == 'airplay':
        os.system('/bin/echo -ne stop | /bin/nc -u localhost 3391 -q 1')
        logging.debug('Through AirPlay sent status: Stop')
    elif CLIENT == 'bluetooth':
        bt.Stop()
        logging.debug('Through Bluetooth sent status: Stop')
    else:
        logging.debug('not supported service:', CLIENT)


def Pause():
    if CLIENT == 'vlm':
        socketIO.emit('pause')
        logging.debug('Through Volumio sent status: Pause')
    elif CLIENT == 'airplay':
        os.system('/bin/echo -ne pause | /bin/nc -u localhost 3391 -q 1')
        logging.debug('Through AirPlay sent status: Pause')
    elif CLIENT == 'bluetooth':
        bt.Pause()
        logging.debug('Through Bluetooth sent status: Pause')
    else:
        logging.debug('not supported service:', CLIENT)


def Next():
    if CLIENT == 'vlm':
        socketIO.emit('next')
        logging.debug('Through Volumio sent status: Next')
    elif CLIENT == 'airplay':
        os.system('/bin/echo -ne nextitem | /bin/nc -u localhost 3391 -q 1')
        logging.debug('Through AirPlay sent status: Next')
    elif CLIENT == 'bluetooth':
        bt.Next()
        logging.debug('Through Bluetooth sent status: Next')
    else:
        logging.debug('not supported service:', CLIENT)


def Prev():
    if CLIENT == 'vlm':
        socketIO.emit('prev')
        logging.debug('Through Volumio sent status: Prev')
    elif CLIENT == 'airplay':
        os.system('/bin/echo -ne previtem | /bin/nc -u localhost 3391 -q 1')
        logging.debug('Through AirPlay sent status: Prev')
    elif CLIENT == 'bluetooth':
        bt.Prev()
        logging.debug('Through Bluetooth sent status: Prev')
    else:
        logging.debug('not supported service:', CLIENT)


def RewindPrev():
    if CLIENT == 'vlm':
        socketIO.emit('getState', _browseState)
        socketIO.wait(seconds=0.1)
        socketIO.emit('seek', max(getTrackInfo()['seek'] / 1000 - 10, 0))
        logging.debug('Through Volumio sent status: RewindPrev')
    elif CLIENT == 'airplay':
        os.system('/bin/echo -ne beginrew | /bin/nc -u localhost 3391 -q 1')
        logging.debug('Through AirPlay sent status: RewindPrev')
    elif CLIENT == 'bluetooth':
        bt.RewindPrev()
        logging.debug('Through Bluetooth sent status: RewindPrev')
    else:
        logging.debug('not supported service:', CLIENT)


def RewindNext():
    if CLIENT == 'vlm':
        socketIO.emit('getState', _browseState)
        socketIO.wait(seconds=0.1)
        socketIO.emit('seek', getTrackInfo()['seek'] / 1000 + 10)
        logging.debug('Through Volumio sent status: RewindNext')
    elif CLIENT == 'airplay':
        os.system('/bin/echo -ne beginff | /bin/nc -u localhost 3391 -q 1')
        logging.debug('Through AirPlay sent status: RewindNext')
    elif CLIENT == 'bluetooth':
        bt.RewindNext()
        logging.debug('Through Bluetooth sent status: RewindNext')
    else:
        logging.debug('not supported service:', CLIENT)


def RewindPlayResume():
    if CLIENT == 'airplay':
        os.system('/bin/echo -ne playresume | /bin/nc -u localhost 3391 -q 1')
        logging.debug('Through AirPlay sent status: PlayResume')
    else:
        logging.debug('not supported service:', CLIENT)


def Repeat():
    pass


def Random():
    if CLIENT == 'vlm':
        if getTrackInfo()['random'] == True:
            socketIO.emit('setRandom', 'false')
            return True
        elif getTrackInfo()['random'] == False:
            socketIO.emit('setRandom', {'value': 'true'})
            return False
        else:
            logging.debug('not supported Random status:', getTrackInfo()['random'])
    elif CLIENT == 'airplay':
        os.system('/bin/echo -ne shuffle_songs | /bin/nc -u localhost 3391 -q 1')
    else:
        logging.debug('not supported service:', CLIENT)


def VolumeSet():
    if CLIENT == 'vlm':
        print 'play service:', CLIENT
        socketIO.emit('volume', VOLUME)
    else:
        logging.debug('not supported service:', CLIENT)


def VolumeUp():
    if CLIENT == 'vlm':
        print 'play service:', CLIENT
        socketIO.emit('volume', '+')
    elif CLIENT == 'airplay':
        os.system('/bin/echo -ne volumeup | /bin/nc -u localhost 3391 -q 1')
    else:
        logging.debug('not supported service:', CLIENT)


def VolumeDown():
    if CLIENT == 'vlm':
        print 'play service:', CLIENT
        socketIO.emit('volume', '-')
    elif CLIENT == 'airplay':
        os.system('/bin/echo -ne volumedown | /bin/nc -u localhost 3391 -q 1')
    else:
        logging.debug('not supported service:', CLIENT)

############################################################################
#
############################################################################

def Reboot():
    socketIO.emit('reboot')


def Shutdown():
    socketIO.emit('shutdown')