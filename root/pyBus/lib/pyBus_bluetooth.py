#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from subprocess import Popen, PIPE
sys.path.append('/root/pyBus/lib')
#from __future__ import absolute_import, print_function, unicode_literals
import dbus
import dbus.service
import dbus.mainloop.glib
import bluezutils
import bluetool
import logging
import time
import threading

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject


dictTrack = {}
BLUETOOTH = False       # systemctl disable bluetooth-agent
btMp = None
btMo = None
btMacLast = None
listDevices = None      # def scanDevices()
# print listDevices[1].get('name')
# print listDevices[1].get('mac_address')

# Temp file for mac addr
btMacAddr = '/root/pyBus/lib/bt_mac'

btCtl = bluetool.Bluetooth()

BUS_NAME = 'org.bluez'
MEDIA_PLAYER_INTERFACE = 'org.bluez.MediaPlayer1'


def find_media_player():
    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager')
    mo = manager.GetManagedObjects()

    for path, ifaces in mo.iteritems():
        mp = ifaces.get(MEDIA_PLAYER_INTERFACE)
        if mp is None:
            continue
        obj = bus.get_object('org.bluez', path)
        return dbus.Interface(obj, MEDIA_PLAYER_INTERFACE)
    raise Exception("Bluetooth MediaPlayer no found")

############################################################################
# FUNCTIONS CONNECTION BLUETOOTH
############################################################################

def init():
    btReadMac()
    disconnect()
    logging.info('Initialized: Bluetooth')


def end():
    logging.info('End: Bluetooth')
    btCtl.disconnect()


def connect():
    global btMp
    global btMo
    global btMacLast

    btCtl.get_available_devices()
    if btCtl.connect(btMacLast) == True:
        time.sleep(1)
        btMp = find_media_player()
        btMo = bluezutils.get_managed_objects()
        logging.info('Connection to the Bluetooth device: Connected - %s', btMacLast)

        return True
    elif btCtl.connect(btMacLast) == False:
        logging.info('Connection to the Bluetooth device: Device is disabled - %s', btMacLast)
        return False
    else:
        logging.error('Connection to the Bluetooth device: Unknown error')


def updateDictTrack():
    enableFunc('trackInfo', 10)
    logging.info('Update via Bluetooth track information: Running')


def stopUpdateDictTrack():
    disableFunc('trackInfo')
    logging.info('Update via Bluetooth track information: Stopped')


def disconnect():
    global btMacLast
    btReadMac()
    btCtl.disconnect(btMacLast)
    logging.debug('Disabled bluetooth device: %s', btMacLast)


def disconnectMacAddr(mac):
    btCtl.disconnect(mac)
    logging.debug('Disabled Bluetooth device: %s', mac)


def newConnect(mac):
    global btMacLast
    disconnect()
    btCtl.get_available_devices()
    if btCtl.connect(mac) == True:
        time.sleep(1)
        btWriteMac(mac)
        logging.info('Connect to a new Bluetooth device: Connected - %s', mac)
        return True
    elif btCtl.connect(mac) == False:
        logging.info('Connect to a new Bluetooth device: Device is disabled - %s', mac)
        return False
    else:
        logging.error('Connect to a new Bluetooth device: Unknown error')


def btReadMac():
    global btMacLast
    btMac = open(btMacAddr, 'r+')
    btMacLast = btMac.read()
    logging.debug('Read the bluetooth address of the last connected device from the temporary file: %s', btMacLast)
    btMac.close()


def btWriteMac(mac):
    btMac = open(btMacAddr, 'r+')
    btMac.write(mac)
    logging.debug('Write the Bluetooth address of the last connected device to a temporary file', mac)
    btMac.close()


def pairedDevices():     # Trust devices
    return btCtl.get_paired_devices()


def connectedDevices():
    return btCtl.get_connected_devices()


def scanDevices():
    global listDevices
    listDevices = []
    btCtl.scan()
    #btCtl.start_scanning(30)
    listDevices = btCtl.get_available_devices()[:]


def removeMac(mac):
    btCtl.remove(mac)
    logging.debug('Removed Bluetooth device: %s', mac)

############################################################################
# FUNCTIONS PLAYER
############################################################################

def Play():
    btMp.Play()
    logging.debug('Bluetooth sent status: Play')
    trackInfo()


def Pause():
    btMp.Pause()
    logging.debug('Bluetooth sent status: Pause')
    trackInfo()


def Stop():
    btMp.Stop()
    logging.debug('Bluetooth sent status: Stop')


def Next():
    btMp.Next()
    logging.debug('Bluetooth sent status: Next')
    trackInfo()


def Prev():
    btMp.Previous()
    logging.debug('Bluetooth sent status: Prev')
    trackInfo()


def RewindPrev():
    btMp.Rewind()
    logging.debug('Bluetooth sent status: Rewind Prev')


def RewindNext():
    btMp.FastFoward()
    logging.debug('Bluetooth sent status: Rewind Next')


def trackInfo():
    global dictTrack
    for path, ifaces in btMo.iteritems():
        if MEDIA_PLAYER_INTERFACE not in ifaces:
            continue
        props = ifaces[MEDIA_PLAYER_INTERFACE]
        for key, value in props.items():
            if key == 'Track':
                for k, v in value.items():
                    dictTrack[k] = v
            else:
                dictTrack[key] = value
    logging.info('Update via Bluetooth track information: Get')


def getTrackInfo():
    global dictTrack

    dictTrack.setdefault('status').append(str(bt.getTrackInfo().get('Status')))
    dictTrack.setdefault('album', []).append(str(bt.getTrackInfo().get('Album')))
    dictTrack.setdefault('artist', []).append(str(bt.getTrackInfo().get('Artist')))
    dictTrack.setdefault('title', []).append(str(bt.getTrackInfo().get('Title')))
    dictTrack.setdefault('repeat', []).append(str(bt.getTrackInfo().get('Repeat')))
    dictTrack.setdefault('random', []).append(str(bt.getTrackInfo().get('Shuffle')))
    dictTrack.setdefault('trackType', []).append(str(bt.getTrackInfo().get('Type')))
    dictTrack.setdefault('uri', []).append(str(bt.getTrackInfo().get('Device')))
    dictTrack.setdefault('numberOfTracks', []).append(str(bt.getTrackInfo().get('NumberOfTracks')))
    dictTrack.setdefault('position', []).append(str(bt.getTrackInfo().get('TrackNumber')))
    logging.debug('Bluetooth: Track information conversion')
    return dictTrack

############################################################################
# SERVICE MANAGEMENT BLUETOOTH-AGENT
############################################################################

def serviceBluetoothStatus():
    p = Popen(['ps', '-A'], stdout=PIPE)    # ps -A for TEST
    stdout, stderr = p.communicate()
    if 'bluetooth-agent' in str(stdout):
        logging.info('Service bluetooth-agent started')
        return True
    else:
        logging.info('Service bluetooth-agent not started')
        return False


def serviceBluetooth():
    service = 'bluetooth-agent'
    global BLUETOOTH

    if not BLUETOOTH:
        logging.info('Starting bluetooth-agent process...')
        p = Popen(['sudo', 'systemctl', 'start', service], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        errcode = p.returncode

        if errcode != 0:
            logging.error('Error while starting bluetooth-agent')
            logging.error(' - stderr : %s' %stderr)
            logging.error(' - stdout : %s' %stdout)

        logging.info('Starting bluetooth-agent process... OK')
        BLUETOOTH = True
        return True

    else:
        logging.info('Stopping bluetooth-agent process...')
        p = Popen(['sudo', 'systemctl', 'stop', service], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        errcode = p.returncode

        if errcode != 0:
            logging.error('Error while stopping bluetooth-agent')
            logging.error(' - stderr : %s' %stderr)
            logging.error(' - stdout : %s' %stdout)

        logging.info('Stopping bluetooth-agent process... OK')
        BLUETOOTH = False
        return False

############################################################################
# FUNCTIONS THREADING
############################################################################

def enableFunc(funcName, interval, count=0):
    global FUNC_STACK

    # Cancel Thread if it already exists.
    if FUNC_STACK.get(funcName) and FUNC_STACK.get(funcName).get('THREAD'):
        FUNC_STACK[funcName]['THREAD'].cancel()

    # Dont worry about checking if a function is already enabled, as the thread would have died. Rather than updating the spec, just run a new thread.
    if getattr(sys.modules[__name__], funcName):
        FUNC_STACK[funcName] = {
            'COUNT': count,
            'INTERVAL': interval,
            'THREAD': threading.Timer(
                interval,
                revive, [funcName]
            )
        }
        logging.debug('Enabling New Thread: %s %s', funcName, FUNC_STACK[funcName])
        worker_func = getattr(sys.modules[__name__], funcName)
        worker_func()
        FUNC_STACK[funcName]['THREAD'].start()
    else:
        logging.warning('No function found (%s)', funcName)


def disableFunc(funcName):
    global FUNC_STACK
    if funcName in FUNC_STACK.keys():
        thread = FUNC_STACK[funcName].get('THREAD')
        if thread: thread.cancel()
        del FUNC_STACK[funcName]


def disableAllFunc():
    global FUNC_STACK
    for funcName in FUNC_STACK:
        thread = FUNC_STACK[funcName].get('THREAD')
        if thread: thread.cancel()
    FUNC_STACK = {}

############################################################################
# THREAD FOR TICKING AND CHECKING EVENTS
# Calls itself again
############################################################################

def revive(funcName):
    global FUNC_STACK
    funcSpec = FUNC_STACK.get(funcName, None)
    if funcSpec:
        count = funcSpec['COUNT']
        if count != 1:
            FUNC_STACK[funcName]['COUNT'] = count - 1
            funcSpec['THREAD'].cancel()  # Kill off this thread just in case..
            enableFunc(funcName, funcSpec['INTERVAL'])  # REVIVE!