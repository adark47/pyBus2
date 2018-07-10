#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import logging
import sys
import time
from threading import Lock, Thread
from Queue import Empty, PriorityQueue, Queue

import serial

TEXT_HIGHLIGHT_COLOR = ['\033[94m', '\033[0m', '\033[1;33;40m']

__author__ = 'harryberlin'
__version__ = '0.5'


#
# TODO Use `logging` framework in a more idiomatic way.
# 
class Logger(object):
    def __init__(self):
        self.enable_logfile = False
        self.logger = None

    def set_file(self, filefullpath):
        self.logger = logging
        self.logger.basicConfig(filename=filefullpath, level=logging.INFO, filemode='w',
                                format='%(asctime)-15s: %(message)s')

    def log(self, message):
        if not self.enable_logfile:
            return
        self.logger.info('%s' % message)


LOGGER = Logger()


def log(string):
    print(' IBUS:', string)

    for color in TEXT_HIGHLIGHT_COLOR:
        string = string.replace(color, '')

    LOGGER.log('IBUS: %s' % string.decode('utf-8').encode('iso-8859-1'))


class IBusHandler(object):
    def __init__(self):

        self.serial_port = serial.Serial()
        self.serial_port.baudrate = 9600
        self.serial_port.parity = serial.PARITY_EVEN
        self.serial_port.stopbits = serial.STOPBITS_ONE
        self.serial_port.timeout = 0.001
        self.rts_state = False

        self.read_buffer = []
        self.read_lock = Lock()
        self.read_error_counter = 0
        self.read_error_container = []
        self.cancel_read_thread = False
        self.read_thread = Thread(target=self._reading)
        self.read_thread.daemon = True
        self.packet_buffer = Queue()

        self.cts_counter = 0.0
        self.cts_thread = Thread(target=self._cts_watcher)
        self.cts_thread.daemon = True

        self.write_buffer = PriorityQueue()
        self.write_counter = 0

        self.cancel_write_thread = False
        self.write_thread = Thread(target=self._writing)
        self.write_thread.daemon = True

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_args):
        self.disconnect()

    @property
    def ntsc(self):
        return self.rts_state

    @ntsc.setter
    def ntsc(self, value):
        if self.rts_state == value:
            return
        self.serial_port.setRTS(value)
        self.rts_state = value

    @staticmethod
    def _calculate_checksum(packet):
        result = 0
        for value in packet:
            result ^= value
        return result

    def _cut_read_buffer(self, offset=1):
        with self.read_lock:
            self.read_buffer = self.read_buffer[offset:]

    def _wait_free_bus(self, waiting=17, timeout=1000):
        # 
        # FIXME Log message doesn't match ``if`` condition.
        # 
        if waiting >= timeout:
            log(
                'Error: Waiting Time (%sms) is bigger than Timeout Time (%sms)'
                % (waiting, timeout)
            )
            return False

        for _ in xrange(timeout):
            if self.cts_counter >= waiting:
                return True
            time.sleep(0.001)

        return False

    def _reading(self):
        while not self.cancel_read_thread:
            data = self.serial_port.read(50)
            if data:
                with self.read_lock:
                    self.read_buffer.extend(ord(x) for x in data)
            self._read_bus_packet()

        log('Read/Write Thread finished')

    def _writing(self):
        while not self.cancel_read_thread:
            try:
                prio, write_counter, data = self.write_buffer.get(timeout=1)
                try:
                    while self.cts_counter < 7.0:
                        time.sleep(0.001)

                    self.serial_port.write(data)
                    self.cts_counter = 0.0
                    self.serial_port.flush()
                    self.cts_counter = 0.0
                    log(
                        '\033[1;33;40mWRITE:\033[0m %s'
                        % ' '.join('%02X' % i for i in data)
                    )
                except serial.SerialException:
                    self.write_buffer.put((prio, write_counter, data))
            except Empty:
                pass

    def _cts_watcher(self):
        while not self.cancel_read_thread:
            if self.serial_port.getCTS():
                self.cts_counter += 0.1
                time.sleep(0.0001)
            else:
                self.cts_counter = 0.0
                # 
                # TODO Maybe sleeping a little or move the `sleep()`
                #   in the ``if`` branch after the ``if``/``else``?
                # 

        log('CTS Thread finished')

    def set_port(self, device_path):
        self.serial_port.port = device_path

    def connect(self):
        self.serial_port.open()
        self.serial_port.setRTS(0)
        self.cts_thread.start()

        if not self._wait_free_bus(120, 3000):
            log('Error: Can not locate free Bus')
            raise RuntimeError('can not locate free bus')

        self.serial_port.flushInput()

        self.read_thread.start()
        self.write_thread.start()

    def disconnect(self):
        self.cancel_write_thread = True
        self.cancel_read_thread = True
        self.ntsc = False
        time.sleep(0.6)
        self.serial_port.close()
        log('disconnected')

    def read_bus_packet(self):
        try:
            return self.packet_buffer.get(timeout=1)
        except Empty:
            return None

    def _read_bus_packet(self):
        if self.cancel_read_thread:
            return None

        try:
            data_length = self.read_buffer[1]
        except IndexError:
            return None

        if not 3 <= data_length <= 37:
            self.read_error_container.append(self.read_buffer[0])
            self._cut_read_buffer()
            return None

        buffer_len = len(self.read_buffer)
        if buffer_len < 5 or buffer_len < data_length + 2:
            return None

        message = self.read_buffer[:data_length + 2]

        if self._calculate_checksum(message) == 0:
            if self.read_error_container:
                error_hex_string = ' '.join(
                    '%02X' % i for i in self.read_error_container
                )
                log('READ-ERR: %s' % error_hex_string)
                self.read_error_counter += len(self.read_error_container)
                self.read_error_container = []

            self._cut_read_buffer(data_length + 2)

            self.packet_buffer.put_nowait({'src': message[0],
                                           'len': data_length,
                                           'dst': message[2],
                                           'data': message[3:data_length + 1],
                                           'xor': message[-1]})
        else:
            self.read_error_container.append(self.read_buffer[0])
            self._cut_read_buffer()
            return None

    def write_bus_packet(
            self, src, dst, data, highprio=False, veryhighprio=False, repeat=1
    ):
        # 
        # FIXME The ``except`` needs explicit exceptions because it is
        #   unclear under what circumstances the ``except`` is a proper
        #   handling of the exception.
        # 
        try:
            packet = [src, len(data) + 2, dst]
            packet.extend(data)
        except:
            packet = [int(src, 16), len(data) + 2, int(dst, 16)]
            packet.extend([int(s, 16) for s in data])

        packet.append(self._calculate_checksum(packet))
        for _ in xrange(repeat):
            self.write_buffer.put_nowait(
                (
                    0 if highprio or veryhighprio else 1,
                    0 if veryhighprio else self.write_counter,
                    bytearray(packet)
                )
            )
            self.write_counter += 1

    def write_hex_message(self, hexstring):
        hexstring_tmp = hexstring.upper().split(' ')
        src = int(hexstring_tmp[0], 16)
        dst = int(hexstring_tmp[2], 16)
        data = [int(s, 16) for s in hexstring_tmp[3:-1]]
        self.write_bus_packet(src, dst, data)


class InputThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.finished = False
        self.write = False

    def run(self):
        try:
            while not self.finished:

                time.sleep(0.5)
                input = raw_input()

                if input == "q":
                    log('wait for disconnecting IBUS')
                    self.finished = True
                elif input == "w":
                    self.write = True
                    log(
                        "\033[1;33;40mType Message for writing to IBus (example:F0 LL 68 01 CK) <- type 'LL' or 'CK' if unknown:\033[0m")
                    while self.write:
                        input = raw_input()
                        if input == '\x1b':
                            pass
                        elif input == 'r':
                            self.write = False
                        elif input == 'q':
                            log('wait for disconnecting IBUS')
                            self.finished = True
                        else:
                            IBUS.write_hex_message(input)

        except (KeyboardInterrupt, SystemExit):
            sys.exit()


def help():
    print('\n')
    print(' -h,           show this information')
    print(' -dev,         set device (default:/dev/ttyUSB0)')
    print(' -log,         enables logfile')
    print(' --- when Script is running ---')
    print(' w + enter,    switches to write mode')
    print(' r + enter,    switches back from write to read mode')
    print(' q + enter,    stops the script')


IBUS = IBusHandler()
INPUTTHREAD = InputThread()


def start_ibus(device='/dev/ttyUSB0'):
    def read_ibus_packages():
        while not INPUTTHREAD.finished:
            packet = IBUS.read_bus_packet()
            if packet:
                while INPUTTHREAD.write:
                    time.sleep(1)
                log('\033[94mREAD:\033[0m %02X %02X %02X %s %02X' % (
                packet['src'], packet['len'], packet['dst'], ' '.join(['%02X' % i for i in packet['data']]),
                packet['xor']))

        log('READ PACKAGES CLOSED')

    log('IBusTesterVersion: %s' % __version__)
    log('SerialModulVersion: %s' % serial.VERSION)
    log('SerialDevice: %s' % device)

    IBUS.set_port(device)

    log('Connecting')
    # 
    # TODO Narrow exception handling so the `IBusHandler` instance can be
    #   used with the ``with`` keyword instead of using
    #   ``try``/``finally``.
    # 
    try:
        IBUS.connect()
    except:
        log('Error: Can not open serial device')
        return
    try:
        ibus_st = Thread(target=read_ibus_packages)
        ibus_st.daemon = True
        ibus_st.start()
        log('Connected')

        INPUTTHREAD.start()

        while not INPUTTHREAD.finished:
            try:
                # print("..Script's Thread..")
                time.sleep(2)
            except (KeyboardInterrupt, SystemExit):
                INPUTTHREAD.finished = True
    finally:
        IBUS.disconnect()


def main():
    count = len(sys.argv) - 1

    given_args = sys.argv

    if '-h' in given_args:
        help()
        sys.exit(0)

    if "-log" in given_args:
        LOGGER.enable_logfile = True
        LOGGER.set_file('ibustester.log')
        count -= 1

    if count > 0:
        if "-dev" in given_args:
            start_ibus(given_args[given_args.index('-dev') + 1])
        else:
            print('\n Unknown Arguments given!', sys.argv[1:])
            help()
            sys.exit(0)
    else:
        start_ibus()

    log('SERVICE COMPLETELY CLOSED')
    sys.exit(0)


if __name__ == '__main__':
    main()