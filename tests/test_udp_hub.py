import socket
import struct
import time

from virtual_tcu.config.store import ConfigStore
from virtual_tcu.telemetry.logger import TelemetryLogger
from virtual_tcu.telemetry.receiver import TelemetryReceiver
from virtual_tcu.telemetry.udp_hub import UdpTelemetryHub


def _free_udp_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
    finally:
        sock.close()


def _udp_listener() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    sock.settimeout(2.0)
    return sock


def _fh6_packet() -> bytes:
    data = bytearray(324)
    struct.pack_into("<iIfff", data, 0, 1, 12345, 8000.0, 900.0, 3500.0)
    struct.pack_into("<iiiii", data, 212, 100, 5, 800, 1, 6)
    struct.pack_into("<fff", data, 256, 42.0, 100000.0, 450.0)
    data[315] = 80
    data[316] = 0
    data[317] = 0
    data[319] = 3
    return bytes(data)


def test_udp_hub_forwards_receiver_packets(tmp_path):
    listener = _udp_listener()
    input_port = _free_udp_port()
    cfg = ConfigStore(path=tmp_path / "cfg.json")
    cfg.data["udp_port"] = input_port
    cfg.data["udp_hub_enabled"] = True
    cfg.data["udp_hub_targets"] = f"127.0.0.1:{listener.getsockname()[1]}"

    receiver = TelemetryReceiver(TelemetryLogger(), config=cfg)
    assert receiver.start()

    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = _fh6_packet()
    try:
        sender.sendto(packet, ("127.0.0.1", input_port))
        forwarded, _ = listener.recvfrom(1024)
        assert forwarded == packet

        deadline = time.time() + 2.0
        while receiver.latest() is None and time.time() < deadline:
            time.sleep(0.01)
        assert receiver.latest() is not None
    finally:
        sender.close()
        receiver.stop()
        listener.close()


def test_udp_hub_forwards_to_multiple_targets(tmp_path):
    listeners = [_udp_listener(), _udp_listener()]
    cfg = ConfigStore(path=tmp_path / "cfg.json")
    cfg.data["udp_hub_enabled"] = True
    cfg.data["udp_hub_targets"] = ",".join(
        f"127.0.0.1:{listener.getsockname()[1]}" for listener in listeners
    )

    hub = UdpTelemetryHub(cfg)
    packet = b"raw-fh6-packet"
    try:
        hub.forward(packet, listen_port=5555)
        assert [listener.recvfrom(1024)[0] for listener in listeners] == [packet, packet]
        assert hub.packets_forwarded == 2
        assert hub.last_error == ""
    finally:
        hub.close()
        for listener in listeners:
            listener.close()


def test_udp_hub_rejects_local_feedback_loop(tmp_path):
    cfg = ConfigStore(path=tmp_path / "cfg.json")
    cfg.data["udp_hub_enabled"] = True
    cfg.data["udp_hub_targets"] = "127.0.0.1:5555"

    hub = UdpTelemetryHub(cfg)
    try:
        hub.forward(b"loop", listen_port=5555)
        assert hub.packets_forwarded == 0
        assert "loops back" in hub.last_error
    finally:
        hub.close()
