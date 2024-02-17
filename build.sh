#!/bin/bash

echo
echo "+================================"
echo "| START: Meshtastic Bot"
echo "+================================"
echo

source .env

datehash=`date | md5sum | cut -d" " -f1`
abbrvhash=${datehash: -8}

echo 
echo "Building container using tag ${abbrvhash}"
echo
docker build -t graboskyc/meshtasticbot:latest -t graboskyc/meshtasticbot:${abbrvhash} .

echo 
echo "Starting container"
echo
docker stop meshtasticbot
docker rm meshtasticbot
docker run -t -i -d --name meshtasticbot -e "MDBURI=${MDBURI}" -e "EMAIL=${EMAIL}" -e "LOCLAT=${LOCLAT}" -e "LOCLONG=${LOCLONG}" -e "CHANIND=${CHANIND}" -e "INTERFACE=${INTERFACE}" -e "SUMBOTURI=${SUMBOTURI}" --restart unless-stopped graboskyc/meshtasticbot:latest

echo
echo "+================================"
echo "| END:  Meshtastic Bot"
echo "+================================"
echo