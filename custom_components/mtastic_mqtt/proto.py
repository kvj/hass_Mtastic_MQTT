from meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2, telemetry_pb2

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

import base64


import logging

_LOGGER = logging.getLogger(__name__)


def _as_position(obj, envelope):
    return ("position", {
        "latitude_i": obj.latitude_i,
        "longitude_i": obj.longitude_i,
        "altitude": obj.altitude,
        "ground_speed": obj.ground_speed,
        "sats_in_view": obj.sats_in_view,
    })

def _as_telemetry(obj, envelope):
    type_ = obj.WhichOneof("variant")
    _LOGGER.debug(f"_as_telemetry: {type_}")
    if type_ == "device_metrics":
        return ("device_metrics", {
            "battery_level": obj.device_metrics.battery_level,
            "voltage": obj.device_metrics.voltage,
            "channel_utilization": obj.device_metrics.channel_utilization,
            "air_util_tx": obj.device_metrics.air_util_tx,
        })
    elif type_ == "environment_metrics":
        return ("environment_metrics", {
            "temperature": obj.environment_metrics.temperature,
            "relative_humidity": obj.environment_metrics.relative_humidity,
            "barometric_pressure": obj.environment_metrics.barometric_pressure,
            "gas_resistance": obj.environment_metrics.gas_resistance,
        })
    return (None, {})

def _as_node_info(obj, envelope):
    return ("nodeinfo", {
        "id": obj.id,
        "shortname": obj.short_name,
        "longname": obj.long_name,
    })

def _as_neighbor_info(obj, envelope):
    payload = {
        "neighbors": [{ "node_id": n.node_id, "snr": n.snr} for n in obj.neighbors],
    }
    payload["neighbors_count"] = len(obj.neighbors)
    return ("neighborinfo", payload)

def _as_text_message(obj, envelope):
    return ("text_message", {
        "text": obj,
        "rx_time": envelope.packet.rx_time,
    })

_converters = {
    portnums_pb2.POSITION_APP: (mesh_pb2.Position, _as_position),
    portnums_pb2.TELEMETRY_APP: (telemetry_pb2.Telemetry, _as_telemetry),
    portnums_pb2.NODEINFO_APP: (mesh_pb2.User, _as_node_info),
    portnums_pb2.NEIGHBORINFO_APP: (mesh_pb2.NeighborInfo, _as_neighbor_info),
    portnums_pb2.TEXT_MESSAGE_APP: (None, _as_text_message)
}

def convert_envelope_to_json(envelope) -> dict:
    result = {
        "from": getattr(envelope.packet, "from"),
        "sender": envelope.gateway_id,
    }
    if config := _converters.get(envelope.packet.decoded.portnum):
        if config[0]:
            obj = config[0]()
            obj.ParseFromString(envelope.packet.decoded.payload)
            _LOGGER.debug(f"convert_packet_to_json(): proto = {obj}")
        else:
            obj = envelope.packet.decoded.payload.decode("utf8")

        type_, payload = config[1](obj, envelope)
        _LOGGER.debug(f"convert_packet_to_json(): result = {type_}, {payload}")
        if type_ and payload:
            result = {
                **result,
                "type": type_,
                "payload": payload
            }
    else:
        _LOGGER.debug(f"convert_packet_to_json(): unsupported portnum = {envelope.packet.decoded.portnum}")
    return result

DEFAULT_ENC_KEY = "1PG7OiApB1nwvP+rz05pAQ=="

def try_encrypt_envelope(envelope, key_b64):

    key_bytes = base64.b64decode(key_b64.replace("_", "/").replace("-", "+").encode("ascii"))
    if len(key_bytes) == 1 and key_bytes[0] == 0x01:
        # Use default key
        key_bytes = base64.b64decode(DEFAULT_ENC_KEY.encode("ascii"))
    
    nonce_packet_id = getattr(envelope.packet, "id").to_bytes(8, "little")
    nonce_from_node = getattr(envelope.packet, "from").to_bytes(8, "little")
    nonce = nonce_packet_id + nonce_from_node

    cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_bytes = decryptor.update(getattr(envelope.packet, "encrypted")) + decryptor.finalize()

    data = mesh_pb2.Data()
    data.ParseFromString(decrypted_bytes)
    envelope.packet.decoded.CopyFrom(data)

