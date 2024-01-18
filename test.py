import meshtastic
import meshtastic.serial_interface
from pubsub import pub
import time
import pymongo
import json
import datetime
import pickle
import json
import base64
import asyncio
import aiohttp
import pynws
import os

# +------------------------------------------------------------
# | Configuration section
# +------------------------------------------------------------
interface = meshtastic.serial_interface.SerialInterface()

_uri = os.environ["MDBURI"]
_conn = pymongo.MongoClient(_uri)
_location = (float(os.environ["LOCLAT"]), float(os.environ["LOCLONG"]))
_email = os.environ["EMAIL"]
_firstRun = True

# +------------------------------------------------------------
# | Functions to clean the crappy message format
# | Thanks, https://github.com/geoffwhittington/meshtastic-matrix-relay
# +------------------------------------------------------------

def normalize(dict_obj):
    """
    Packets are either a dict, string dict or string
    """
    if type(dict_obj) is not dict:
        try:
            dict_obj = json.loads(dict_obj)
        except:
            dict_obj = {"decoded": {"text": dict_obj}}

    return strip_raw(dict_obj)

def process(packet):
    packet = normalize(packet)

    if "decoded" in packet and "payload" in packet["decoded"]:
        if type(packet["decoded"]["payload"]) is bytes:
            text = packet["decoded"]["payload"]
            packet["decoded"]["payload"] = base64.b64encode(
                packet["decoded"]["payload"]
            ).decode("utf-8")

    return packet

def strip_raw(data):
    if type(data) is not dict:
        return data

    if "raw" in data:
        del data["raw"]

    for k, v in data.items():
        data[k] = strip_raw(v)

    return data

# +------------------------------------------------------------
# | External functions
# +------------------------------------------------------------
async def asyncweather():
    async with aiohttp.ClientSession() as session:
        nws = pynws.SimpleNWS(*_location, _email, session)
        await nws.set_station()
        await nws.update_observation()
        print(nws.observation)

def weather():
    loop.run_until_complete(asyncweather())

# +------------------------------------------------------------
# | Message handling
# +------------------------------------------------------------

def onReceive(packet, interface): # called when a packet arrives
    print("==========================")
    doc = process(packet)
    doc["insertTime"] = datetime.datetime.utcnow()
    print(doc)
    _conn["meshtastic"]["inbound"].insert_one(doc)
    print("==========================")
    weather()    

def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
    # defaults to broadcast, specify a destination ID if you wish
    #interface.sendText("hello mesh")
    print("-------------------------------")
    print("Connected")
    global _firstRun
    if _firstRun == True:
        print("Setting location")
        localConfig = interface.localNode.localConfig
        localConfig.position.fixed_position = True
        interface.sendPosition(float(os.environ["LOCLAT"]), float(os.environ["LOCLONG"]), 0)
        interface.localNode.writeConfig("position")
        print("Location set")
        _firstRun = False
    print("-------------------------------")

# +------------------------------------------------------------
# | Main
# +------------------------------------------------------------

pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")
loop = asyncio.get_event_loop()

while True:
    time.sleep(1000)
interface.close()