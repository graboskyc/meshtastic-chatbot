import meshtastic
import meshtastic.serial_interface
import meshtastic.tcp_interface
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
import wikipedia

# +------------------------------------------------------------
# | Configuration section
# +------------------------------------------------------------
interface = None
if ("INTERFACE" in os.environ):
    if(os.environ["INTERFACE"] != ""):
        interface = meshtastic.tcp_interface.TCPInterface(hostname=os.environ["INTERFACE"])
    else:
        interface = meshtastic.serial_interface.SerialInterface()
else:
    interface = meshtastic.serial_interface.SerialInterface()

_uri = os.environ["MDBURI"]
_conn = pymongo.MongoClient(_uri)
_location = (float(os.environ["LOCLAT"]), float(os.environ["LOCLONG"]))
_email = os.environ["EMAIL"]
_firstRun = False
_watchChan = int(os.environ["CHANIND"])

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

def CtoF(degC):
    degF = (degC * 1.8) + 32
    return "{:.2f}".format(degF)

# +------------------------------------------------------------
# | External functions
# +------------------------------------------------------------
async def asyncweather():
    async with aiohttp.ClientSession() as session:
        nws = pynws.SimpleNWS(*_location, _email, session)
        await nws.set_station()
        await nws.update_observation()
        await nws.update_forecast()
        #print(nws.observation)
        #print(nws.forecast[0])

        doc = {}
        doc["insertTime"] = datetime.datetime.utcnow()
        doc["weatherObservation"] = nws.observation
        doc["responseMsg"] = "Current temp is " + str(CtoF(nws.observation["temperature"])) + " and wind is " + str(nws.observation["windSpeed"]) + " and weather is " + str(nws.observation["textDescription"]) +". Today forecasting " +  str(nws.forecast[0]["probabilityOfPrecipitation"]) + " percent chance of precip. It will be "  + nws.forecast[0]["detailedForecast"]
        _conn["meshtastic"]["outbound"].insert_one(doc)

        ch = interface.localNode.getChannelByChannelIndex(_watchChan)
        print("SENDING: " + doc["responseMsg"] + " TO: {ch}")
        interface.sendText(doc["responseMsg"], wantAck=True, channelIndex=_watchChan)

def weather():
    loop.run_until_complete(asyncweather())

def wiki(msg):
    doc = {}
    doc["insertTime"] = datetime.datetime.utcnow()
    doc["responseMsg"] = wikipedia.summary(msg[5:])
    _conn["meshtastic"]["outbound"].insert_one(doc)

    ch = interface.localNode.getChannelByChannelIndex(_watchChan)
    print("SENDING: " + doc["responseMsg"] + " TO: {ch}")
    n=150
    chunks = [doc["responseMsg"][i:i+n] for i in range(0, len(doc["responseMsg"]), n)]
    for c in chunks:
        interface.sendText(c, wantAck=True, channelIndex=_watchChan)

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
    
    if("decoded" in doc):
        if("text" in doc["decoded"]):
            if(doc["decoded"]["text"].lower().strip() == "weather"):
                weather()
            if(doc["decoded"]["text"].lower().strip().startswith("wiki")):
                wiki(doc["decoded"]["text"].lower().strip())   

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