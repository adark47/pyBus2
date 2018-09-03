#!/bin/sh

########################################################################################################################
sudo raspi-config
# 1. Enter
# sudo raspi-config in a terminal window
# 2. Select Interfacing Options
# 3. Navigate to and select SSH
# 4. Choose Yes
# 5. Select Ok
# 6. Choose Finish
sudo systemctl enable ssh
sudo systemctl start ssh

########################################################################################################################
# runeaudio
# http://www.runeaudio.com/forum/pifi-dac-v2-0-not-working-on-rspberry-pi-3-solved-t3647.html
# user: root
# password: rune

########################################################################################################################
locale-gen "en_US.UTF-8"
sudo dpkg-reconfigure locales

########################################################################################################################

apt update
apt upgrade # !!!! NOT UPGRADE VOLUMIO !!!!
apt -y install aptitude mc iotop htop iftop usbutils smartmontools alsa-utils alsa-tools
apt -y install bash-completion
apt -y install bc sysstat logrotate
# apt -y install hostapd
# apt -y install samba smbclient
# apt -y install exfat-fuse exfat-utils
apt -y install netcat

########################################################################################################################
# Shairport-sync

apt -y install build-essential git xmltoman
apt -y install autoconf automake libtool libdaemon-dev libpopt-dev libconfig-dev
apt -y install libasound2-dev libpulse-dev
apt -y install avahi-daemon libavahi-client-dev
apt -y install libssl-dev libsoxr-dev libmbedtls-dev

git clone https://github.com/mikebrady/shairport-sync.git
cd ./shairport-sync-master/
git clone https://gist.github.com/unnmd/b64c3a98076a57717aeeaa5bebd3eef7#file-rtsp-c-diff
patch -p1 rtsp.c < rtsp.c.diff
autoreconf -i -f
./configure --sysconfdir=/etc --with-alsa --with-avahi --with-ssl=openssl --with-metadata --with-soxr --with-systemd
make && make install

systemctl start shairport-sync
systemctl enable shairport-sync

# shairport-sync dacp
git clone https://gist.github.com/unnmd/b64c3a98076a57717aeeaa5bebd3eef7#file-main-c
gcc main.c -o dacp_client -L /usr/lib/x86_64-linux-gnu/ -lavahi-client -lavahi-common

chmod +x ./dacp_client
cp ./dacp_client /usr/bin/dacp_client
cp ./dacp_client.service /lib/systemd/system/dacp_client.service

chmod 644 /lib/systemd/system/dacp_client.service
chmod 744 /usr/bin/dacp_client
systemctl daemon-reload
systemctl enable dacp_client.service
systemctl start dacp_client.service

########################################################################################################################
# Shairport-sync-metadata-reader

git clone https://github.com/mikebrady/shairport-sync-metadata-reader
cd shairport-sync-metadata-reader-master
autoreconf -i -f
./configure
make && make install

########################################################################################################################
# Install motd

git clone https://github.com/fedya/omv_motd.git
cp -v motd_hello_gen /usr/bin/
cp motd.service motd.timer /etc/systemd/system/
systemctl enable motd.timer
systemctl start motd.timer

########################################################################################################################
# VOLUMIO + BLUEZ-ALSA (A2DP BLUETOOTH SUPPORT)
# https://volumio.org/forum/volumio-bluetooth-receiver-t8937.html

apt-cache search libasound
apt -y install dh-autoreconf libasound2-dev libortp-dev pi-bluetooth
apt -y install libusb-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev libsbc1 libsbc-dev
apt -y install python-dbus python-gobject
apt -y install gawk

git clone git://git.kernel.org/pub/scm/bluetooth/bluez.git
cd bluez
git checkout 5.48
./bootstrap
./configure --enable-library --enable-experimental --enable-tools
make && make install

sudo ln -s /usr/local/lib/libbluetooth.so.3.18.16 /usr/lib/arm-linux-gnueabihf/libbluetooth.so
sudo ln -s /usr/local/lib/libbluetooth.so.3.18.16 /usr/lib/arm-linux-gnueabihf/libbluetooth.so.3
sudo ln -s /usr/local/lib/libbluetooth.so.3.18.16 /usr/lib/arm-linux-gnueabihf/libbluetooth.so.3.18.16

git clone https://github.com/Arkq/bluez-alsa.git # !!!! v1.3.0 NOT WORKED, only 1.2.0 !!!!
cd bluez-alsa
autoreconf --install
mkdir build && cd build
../configure --disable-hcitop --with-alsaplugindir=/usr/lib/arm-linux-gnueabihf/alsa-lib
make && make install

systemctl daemon-reload

systemctl enable bluetooth.service
systemctl start bluetooth.service

systemctl enable bluealsa.service
systemctl start bluealsa.service

chmod a+rwx /root/bin/a2dp-autoconnect
touch /var/log/a2dp-autoconnect
chmod a+rw /var/log/a2dp-autoconnect

# test
bluealsa-aplay E0:C7:67:AB:C7:9F

########################################################################################################################
# pyBus2

git clone https://github.com/adark47/pyBus2.git

apt -y install python python-setuptools mpc ncmpc git python-pip python-dev build-essential mpd
apt -y install libao-dev libssl-dev libcrypt-openssl-rsa-perl libio-socket-inet6-perl libwww-perl avahi-utils libmodule-build-perl
pip install python-mpd2 tinytag termcolor web.py python-mpd pyserial tornado argparse requests
pip install socketIO-client websocket-client pexpect pybluez bluetool

# shairport-decoder
pip install luckydonald-utils
pip install python-magic
git clone https://github.com/luckydonald/shairport-decoder.git
cd ./shairport-decoder/
python ./setup.py install

systemctl enable pyBus.service
systemctl start pyBus.service


systemctl status shairport-sync
systemctl status dacp_client.service
systemctl status bluetooth.service
systemctl status bluealsa.service
systemctl status pyBus.service

# bluetoothctl
# power on
# agent on
# default-agent
# scan on => xx:xx of your device
# pair xx:xx
# trust xx:xx
# exit