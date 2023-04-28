#!/bin/bash

# This script is used to verify the email field in the CSR file 

# Usage: ./verifMailCSR.sh <CSR file> <emailToVerify>
if [ $# -ne 2 ]; then
    echo "Usage: $0 <CSR file> <emailToVerify>"
    exit 1
else
confFile="../CA/caVF.cnf"
CSRemail=$(openssl req -in $1 -noout -subject -nameopt multiline | awk -F= '/email/ {gsub(/^[ \t]+/,"",$2); print $2}')
if [ "$CSRemail" == "$2" ]; then
    result=$(openssl ca -batch -config $confFile -in $1 -days 90 -extensions smime 2>&1 >/dev/null)
    echo -n "1"
else
    echo -n "-1"
fi
fi
