import asyncio
import json
from os import environ

import websockets
import mido

#Suppress the hello message from PyGame
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
mido.set_backend('mido.backends.pygame')

#Host and Port
HOST = "localhost"
PORT = 5000
DEFAULT_PORT = None

# Get list of midi output devices
midi_ports = {}
ports_names = mido.get_output_names()

print("=== Lumia Midi Bridge (Ctrl+C to Quit) ===")
print("Available Midi Output Devices:")

if DEFAULT_PORT is None:
    DEFAULT_PORT = ports_names[0]

for p in ports_names:
    midi_ports[p] = None
    if p == DEFAULT_PORT:
        print(f"\t{p} (default)")
    else:
        print(f"\t{p}")

async def connection_handler(websocket):

    msg_on = mido.Message('note_on', channel=0, note=0)
    msg_off = mido.Message('note_off', channel=0, note=0)

    async for message in websocket:
        print(f"Client Connected - Host[{websocket.remote_address[0]}] Port[{websocket.remote_address[1]}]")
        try:
            data = json.loads(message)
            port_name = data.get("midi_device", DEFAULT_PORT)
            channel = data.get("channel", 1)
            note = data.get("note", 127)

            #Check if port is valid
            if port_name not in midi_ports.keys():
                print(f"Unknown device name {port_name}. Aborting this message")
                continue
            
            #If port is not open, open it
            if midi_ports[port_name] is None:
                midi_ports[port_name] = mido.open_output(port_name)
            
            #Check is open port worked
            if midi_ports[port_name].closed:
                print(f"Open Port {port_name} failed for an unknown reason. Aborting this message")
                continue
            
            #Check if channel and notes are ints
            if not isinstance(channel, int) or not isinstance(note, int):
                print("Invalid data - Channel and Note should be integers: channel 0-15 and note 0-127. Aborting")
                continue
            
            #Check if channel is 0-15
            if channel < 0 or channel > 15:
                print(f"Invalid channel: {channel} -  Channel should be an int 0-15. Aborting this message")
                continue

            #Check if note is 0-127
            if note < 0 or note > 127:
                print(f"Invalid note: {note} -  Note should be an int 0-127. Aborting this message")
                continue

            msg_on = mido.Message('note_on', channel=channel, note=note)
            msg_off = mido.Message('note_off', channel=channel, note=note)
            print(f"Sending Midi - Device:{port_name} Ch:{channel} Note:{note}")
            midi_ports[port_name].send(msg_on)
            midi_ports[port_name].send(msg_off)
        except json.JSONDecodeError:
            print(f"Could not parse msg as json: {message}")

async def main():
    async with websockets.serve(connection_handler, HOST, PORT):
        print(f"=== WS Server Started ws://{HOST}:{PORT} ===")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard Interrupt - Stopping Lumia Midi Bridge")
        print("Closing all Open Midi Ports")
        for name, port in midi_ports.items():
            if port is not None:
                port.close()
                print(f"\tClosed Midi Port [{name}]")
        print("=== Lumia Midi Bridge Stopped ===")

