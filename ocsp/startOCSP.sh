#/bin/bash

openssl ocsp -index ../CA/index.txt -port 8888 -rsigner ocsp.crt -rkey key.pem -CA ocsp-chain.pem -text
