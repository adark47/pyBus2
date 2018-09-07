#!/bin/sh

########################################################################################################################
sudo systemctl enable ssh
sudo systemctl start ssh

########################################################################################################################
# runeaudio
# http://www.runeaudio.com/forum/pifi-dac-v2-0-not-working-on-rspberry-pi-3-solved-t3647.html
# user: root
# password: rune

########################################################################################################################
locale-gen "en_US.UTF-8" && sudo dpkg-reconfigure locales

########################################################################################################################
echo "deb http://archive.raspbian.org/raspbian jessie main contrib non-free" | sudo tee -a /etc/apt/sources.list
echo "deb-src http://archive.raspbian.org/raspbian jessie main contrib non-free" | sudo tee -a /etc/apt/sources.list
wget https://archive.raspbian.org/raspbian.public.key -O - | sudo apt-key add -

apt update
apt -y upgrade # !!!! NOT UPGRADE VOLUMIO !!!!
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
apt -y install libasound2-dev libpulse-dev libssl-dev
apt -y install avahi-daemon libavahi-client-dev
apt -y install libssl-dev libsoxr-dev libmbedtls-dev
apt -y install libsoxr*

git clone https://github.com/mikebrady/shairport-sync.git
cd ./shairport-sync-master/
git clone https://gist.github.com/unnmd/b64c3a98076a57717aeeaa5bebd3eef7#file-rtsp-c-diff
patch -p1 rtsp.c < rtsp.c.diff
autoreconf -i -f
./configure --sysconfdir=/etc --with-alsa --with-avahi --with-ssl=openssl --with-metadata --with-soxr --with-systemd
make && make install

systemctl enable shairport-sync
systemctl start shairport-sync

# shairport-sync dacp
git clone https://gist.github.com/unnmd/b64c3a98076a57717aeeaa5bebd3eef7#file-main-c
gcc main.c -o dacp_client -L /usr/lib/x86_64-linux-gnu/ -lavahi-client -lavahi-common

cp ./dacp_client /usr/bin/dacp_client
cp ./dacp_client.service /lib/systemd/system/dacp_client.service
cd ..

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
cd ..

########################################################################################################################
# VOLUMIO + BLUEZ-ALSA (A2DP BLUETOOTH SUPPORT)
# https://volumio.org/forum/volumio-bluetooth-receiver-t8937.html

apt-cache search libasound
apt -y install dh-autoreconf libortp-dev pi-bluetooth
apt -y install libasound2-dev
apt -y install libusb-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev libsbc1 libsbc-dev
apt -y install python-dbus python-gobject
apt -y install gawk

git clone git://git.kernel.org/pub/scm/bluetooth/bluez.git
cd bluez
git checkout 5.48
./bootstrap
./configure --enable-library --enable-experimental --enable-tools
make && make install
cd ..

sudo ln -s /usr/local/lib/libbluetooth.so.3.18.16 /usr/lib/arm-linux-gnueabihf/libbluetooth.so
sudo ln -s /usr/local/lib/libbluetooth.so.3.18.16 /usr/lib/arm-linux-gnueabihf/libbluetooth.so.3
sudo ln -s /usr/local/lib/libbluetooth.so.3.18.16 /usr/lib/arm-linux-gnueabihf/libbluetooth.so.3.18.16

systemctl daemon-reload
systemctl enable bluetooth.service
systemctl start bluetooth.service

git clone https://github.com/Arkq/bluez-alsa.git # !!!! v1.3.0 NOT WORKED, only 1.2.0 !!!!
cd bluez-alsa
autoreconf --install
mkdir build && cd build
#../configure --enable-debug --disable-hcitop --with-alsaplugindir=/usr/lib/arm-linux-gnueabihf/alsa-lib --disable-thread-safety
../configure --enable-debug --disable-hcitop --with-alsaplugindir=/usr/lib/arm-linux-gnueabihf/alsa-lib
make && make install
cd ..

systemctl daemon-reload
systemctl enable bluealsa.service
systemctl start bluealsa.service

chmod a+rwx /root/bin/a2dp-autoconnect
touch /var/log/a2dp-autoconnect
chmod a+rw /var/log/a2dp-autoconnect

########################################################################################################################
# pyBus2

git clone https://github.com/adark47/pyBus2.git

apt -y install python python-setuptools mpc ncmpc python-pip python-dev mpd
pip install python-mpd2 tinytag termcolor web.py python-mpd pyserial tornado argparse requests
pip install socketIO-client websocket-client pexpect pybluez bluetool

systemctl enable pyBus.service
systemctl start pyBus.service

########################################################################################################################
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
# pair C0:D0:12:AA:2F:97
# trust C0:D0:12:AA:2F:97
# exit

bluealsa-aplay C0:D0:12:AA:2F:97
alsamixer -D bluealsa