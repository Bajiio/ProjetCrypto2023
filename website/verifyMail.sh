#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <CSR file> <emailToVerify>"
    exit 1
else
ICA="../CA/private/new/ica.pem"
RCA="../RCA/rootCA1.crt"
CSRemail=$(openssl x509 -in $1 -subject -noout -nameopt multiline | awk -F= '/email/ {gsub(/^[ \t]+/,"",$2); print $2}')
if [ "$CSRemail" == "$2" ]; then
    openssl x509 -in $1 -outform pem -out $1
    cat $ICA $RCA >> $1
    echo -n "1"
else
    echo -n "-1"
fi
fi