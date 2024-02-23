### Meshtastic MQTT Client

  * Integration uses Protobuf MQTT outputs, available through the HA MQTT Server. No JSON outputs are needed
  * Supports encrypted outputs
  * Exposes various sensor values available from Meshtastic nodes
  * Implements Device Tracker showing latest reported position

![Screenshot from 2024-02-22 14-57-40](https://github.com/kvj/hass_Mtastic_MQTT/assets/159124/51051405-f700-41d0-b6f5-02000cabeef1)


### Installation

  * Install this repo via HACS (custom integration repository)

### Configuration

![Screenshot from 2024-02-22 14-58-00](https://github.com/kvj/hass_Mtastic_MQTT/assets/159124/487498d2-381c-44da-81ef-62edcb6b2934)


  * In order to register new node in your Home Assistant, you need 2-3 things:
    * Node ID: e.g. `!aabbccdd`
    * Protobuf MQTT topic: e.g. `msh/EU_868/2/c/LongFast/!aabbccdd`
    * Optionally, Base64 encoded encryption key as it appears in the mobile app (copy/paste)
    * Optionally, stat MQTT topic: e.g. `msh/EU_868/2/stat/!aabbccdd`

#### How to make Meshtastic public MQTT server data available in your local MQTT server?

  * You can utilize MQTT Bridge functionality
  * I'm using Mosquitto, and I have the following lines in my configuration file (with real node IDs):
    
```
connection meshtastic
address mqtt.meshtastic.org

topic +/+/!e2e2xxxx in 0 meshtastic/ msh/EU_868/2/
topic +/+/!3032yyyy in 0 meshtastic/ msh/EU_868/2/

topic !3032xxxx in 0 meshtastic/stat/ msh/EU_868/2/stat/
topic !e2e2yyyy in 0 meshtastic/stat/ msh/EU_868/2/stat/

```
  * Using that, all topics are available in my local MQTT server under `meshtastic/` root topic
