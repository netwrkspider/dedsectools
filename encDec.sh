#!/bin/bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

apt-get install make cmake bison
wget http://www.datsi.fi.upm.es/~frosal/sources/shc-3.8.7.tgz
tar xvfz shc-3.8.7.tgz
cd shc-3.8.7
make
make install 
shc -v
