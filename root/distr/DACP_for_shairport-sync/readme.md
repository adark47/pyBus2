# DACP for shairport-sync

Original: https://www.sugrsugr.com/index.php/airplay-prev-next/

## [main.c](https://gist.github.com/unnmd/b64c3a98076a57717aeeaa5bebd3eef7#file-main-c) - DACP Client

compile: 
```
gcc main.c -o dacp_client -L/usr/lib/x86_64-linux-gnu/ -lavahi-client -lavahi-common
```

previous song:
```
echo -ne previtem | nc -u -4 localhost 3391 -q 1
```
next song:
```
echo -ne nextitem | nc -u -4 localhost 3391 -q 1
```
toggle between play and pause:
```
echo -ne playpause | nc -u -4 localhost 3391 -q 1
```
Acording to [Unofficial AirPlay Protocol Specification](http://nto.github.io/AirPlay.html#audio-remotecontrol). Airplay protocol includes a subset of DACP. 

## [rtsp.c.diff](https://gist.github.com/unnmd/b64c3a98076a57717aeeaa5bebd3eef7#file-rtsp-c-diff) - patch shairport-sync

[shairport-sync version](https://github.com/mikebrady/shairport-sync/tree/ce6dd2102488c181aab4301129e12ad2e5af910c)

apply patch:
```
patch -p1 rtsp.c < rtsp.c.diff
```
