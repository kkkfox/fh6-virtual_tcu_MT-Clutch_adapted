from __future__ import annotations

import ipaddress
import re
import socket
import threading
from dataclasses import dataclass

from virtual_tcu.config.constants import Cfg

_TARGET_SPLIT_RE = re.compile(r"[\s,;]+")


@dataclass(frozen=True)
class UdpHubTarget:
    label: str
    address: tuple[str, int]


def _local_ipv4_addresses() -> set[str]:
    ips = {"127.0.0.1", "0.0.0.0"}
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_DGRAM):
            ips.add(info[4][0])
    except OSError:
        pass
    return ips


def _parse_target_entry(entry: str) -> tuple[str, int]:
    item = entry.strip()
    if not item:
        raise ValueError("empty target")

    if ":" not in item:
        host, port_text = "127.0.0.1", item
    else:
        host, port_text = item.rsplit(":", 1)
        host = host.strip() or "127.0.0.1"

    try:
        port = int(float(port_text.strip()))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid UDP hub target port: {entry!r}") from exc

    if port < 1 or port > 65535:
        raise ValueError(f"UDP hub target port out of range: {entry!r}")

    return host, port


def _is_self_target(host: str, port: int, listen_port: int) -> bool:
    if port != listen_port:
        return False

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False

    return ip.is_loopback or ip.is_unspecified or str(ip) in _local_ipv4_addresses()


def parse_udp_hub_targets(raw_targets, listen_port: int) -> tuple[UdpHubTarget, ...]:
    if raw_targets is None:
        return ()

    targets: list[UdpHubTarget] = []
    seen: set[tuple[str, int]] = set()
    for entry in _TARGET_SPLIT_RE.split(str(raw_targets)):
        if not entry:
            continue
        host, port = _parse_target_entry(entry)
        try:
            info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_DGRAM)
        except socket.gaierror as exc:
            raise ValueError(f"invalid UDP hub target host: {entry!r}") from exc

        address = info[0][4]
        if _is_self_target(address[0], address[1], listen_port):
            raise ValueError(f"UDP hub target loops back to the telemetry input: {entry!r}")
        if address in seen:
            continue
        seen.add(address)
        targets.append(UdpHubTarget(label=f"{host}:{port}", address=address))

    return tuple(targets)


class UdpTelemetryHub:
    def __init__(self, config=None):
        self._config = config
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()
        self._settings: tuple[bool, str, int] | None = None
        self._targets: tuple[UdpHubTarget, ...] = ()
        self.packets_forwarded = 0
        self.last_error = ""

    def _enabled(self) -> bool:
        if self._config is None:
            return False
        return bool(self._config.get("udp_hub_enabled", False))

    def _raw_targets(self) -> str:
        if self._config is None:
            return ""
        return str(self._config.get("udp_hub_targets", "")).strip()

    def _ensure_socket(self) -> socket.socket:
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return self._sock

    def _refresh_targets_if_needed(self, listen_port: int) -> tuple[UdpHubTarget, ...]:
        enabled = self._enabled()
        raw_targets = self._raw_targets()
        settings = (enabled, raw_targets, listen_port)
        if settings == self._settings:
            return self._targets

        with self._lock:
            if settings == self._settings:
                return self._targets

            self._settings = settings
            self.last_error = ""
            if not enabled or not raw_targets:
                self._targets = ()
                return self._targets

            try:
                self._targets = parse_udp_hub_targets(raw_targets, listen_port)
            except ValueError as exc:
                self._targets = ()
                self.last_error = str(exc)
        return self._targets

    def forward(self, raw: bytes, listen_port: int = Cfg.UDP_PORT):
        targets = self._refresh_targets_if_needed(listen_port)
        if not targets:
            return

        sock = self._ensure_socket()
        sent = 0
        for target in targets:
            try:
                sock.sendto(raw, target.address)
                sent += 1
            except OSError as exc:
                self.last_error = str(exc)
        if sent:
            with self._lock:
                self.packets_forwarded += sent

    def close(self):
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
