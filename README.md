# lumia-midi-bridge
Web API to relay messages from LumiaStream to midi devices

# Web API 
```
git clone https://github.com/chillfactor032/lumia-midi-bridge.git
cd lumia-midi-bridge
py -m pip install -r requirements
flask --app lumia_midi_bridge_webapi run
```

## Example JSON Object

```JSON
{"midi_device": "VirtualMidiPort1", "channel": 9, "note": 91}
```
