import logging
import signal
import sys
from os import environ
from flask import Flask, request, jsonify
import mido

#Suppress the hello message from PyGame
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
mido.set_backend('mido.backends.pygame')

HOST = "localhost"
PORT = 5000
DEFAULT_PORT = "VirtualMidiPort1"

print("=== Lumia Midi Bridge (Ctrl+C to Quit) ===")
print("Available Midi Output Devices:")

# Get list of midi output devices
midi_ports = {}
ports_names = mido.get_output_names()
for p in ports_names:
    midi_ports[p] = None
    if p == DEFAULT_PORT:
        print(f"\t{p} (default)")
    else:
        print(f"\t{p}")

# Flask App Object
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# API Endpoint to send arbitry MIDI note_on messages
@app.route('/midi', methods=["POST"])
def midi_send():
    data = request.json
    port_name = data.get("midi_device", DEFAULT_PORT)
    channel = data.get("channel", 1)
    note = data.get("note", 127)

    #Check if port is valid
    if port_name not in midi_ports.keys():
        msg = {"success": False, "msg": f"Unknown device name {port_name}. Aborting Request"}
        app.logger.info(msg["msg"])
        return jsonify(msg, 400)
    
    #If port is not open, open it
    if midi_ports[port_name] is None:
        midi_ports[port_name] = mido.open_output(port_name)
    
    #Check is open port worked
    if midi_ports[port_name].closed:
        msg = {"success": False, "msg": f"Open Midi Port {port_name} failed for an unknown reason. Aborting Request"}
        app.logger.info(msg["msg"])
        return jsonify(msg), 500
    
    #Check if channel and note are ints
    if not isinstance(channel, int) or not isinstance(note, int):
        msg = {"success": False, "msg": "Invalid data - Channel and Note should be integers: channel 0-15 and note 0-127. Aborting Request"}
        app.logger.info(msg["msg"])
        return jsonify(msg), 400
    
    #Check if channel is 0-15
    if channel < 0 or channel > 15:
        msg = {"success": False, "msg": f"Invalid channel: {channel} -  Channel should be an int 0-15. Aborting Request"}
        app.logger.info(msg["msg"])
        return jsonify(msg), 400
    
    #Check if note is 0-127
    if note < 0 or note > 127:
        msg = {"success": False, "msg": f"Invalid note: {note} -  Note should be an int 0-127. Aborting Request"}
        app.logger.info(msg["msg"])
        return jsonify(msg), 400
    
    msg_on = mido.Message('note_on', channel=channel, note=note)
    msg_off = mido.Message('note_off', channel=channel, note=note)
    print(f"Sending Midi - Device:{port_name} Ch:{channel} Note:{note}")
    midi_ports[port_name].send(msg_on)
    midi_ports[port_name].send(msg_off)

    msg = {
        "msg": "Successfully sent MIDI message",
        "device": port_name,
        "channel": channel,
        "note": note
    }
    return jsonify(msg), 200

@app.route('/devices', methods=["GET"])
def devices():
    ports_names = mido.get_output_names()
    return jsonify(ports_names), 200

@app.route('/teapot')
def teapot():
    return "418 I'm a teapot", 418

@app.route('/')
def index():
    return "Lumia Midi Bridge API Running"

def on_close(signalNumber, frame):
    print("Keyboard Interrupt - Stopping Lumia Midi Bridge")
    print("Closing all Open Midi Ports")
    for name, port in midi_ports.items():
        if port is not None:
            port.close()
            print(f"\tClosed Midi Port [{name}]")
    print("=== Lumia Midi Bridge Stopped ===")
    sys.exit(0)

signal.signal(signal.SIGINT, on_close)
signal.signal(signal.SIGTERM, on_close)
