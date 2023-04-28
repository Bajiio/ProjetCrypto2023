#!/bin/bash

configFile='../CA/caVF.cnf';
openssl ca -batch -config $configFile -revoke $1;   # Revoke the certificate
rm $1;

return 1;