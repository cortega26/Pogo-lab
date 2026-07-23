"""Función de key para rate limiting basada en IP confiable.

Solo extrae la IP del header X-Real-IP cuando REMOTE_ADDR pertenece al
proxy conocido (nginx en la red Docker). En otro caso usa REMOTE_ADDR.
Cubre IPv4/IPv6, listas, spoof y ausencia.
"""

import contextlib
import ipaddress
import os

_RAW_NETWORKS = os.environ.get(
    "RATELIMIT_PROXY_NETWORKS", "172.16.0.0/12,10.0.0.0/8,192.168.0.0/16"
).split(",")

_PROXY_NETS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
for _net in _RAW_NETWORKS:
    _net = _net.strip()
    if not _net:
        continue
    with contextlib.suppress(ValueError):
        _PROXY_NETS.append(ipaddress.ip_network(_net))


def _is_proxy_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(ip in net for net in _PROXY_NETS)


def client_ip_key(group: str, request):  # noqa: ARG001
    """Función de key para django-ratelimit.

    Usa X-Real-IP solo cuando REMOTE_ADDR es del proxy; si no, REMOTE_ADDR.
    """
    remote_addr = request.META.get("REMOTE_ADDR", "").strip()
    if _is_proxy_ip(remote_addr):
        real_ip = request.META.get("HTTP_X_REAL_IP", "").strip()
        if real_ip:
            return real_ip
    return remote_addr or "0.0.0.0"
