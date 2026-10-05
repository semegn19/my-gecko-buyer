"""Project 03: is a URL safe for the check server to fetch?

A server that fetches a URL it was handed can be pointed at things only it can reach:
the loopback interface, the cloud metadata address, services on a private network. This
guard answers one question before anything is fetched, using the standard library only.

The rule: `https`, and a host that is (or resolves only to) a public address. Everything
else is refused. A name that does not resolve is refused too: a host we cannot check is
not a host we may fetch from.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit


def _public_literal(host: str) -> bool | None:
    """`True`/`False` for a literal IP, or `None` when `host` is not an IP at all."""
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return None
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def is_public_url(url: str) -> bool:
    """`True` only for an https URL whose host is, or resolves to, a public address."""
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        return False
    if parts.scheme != "https" or not host:
        return False

    literal = _public_literal(host)
    if literal is not None:
        return literal

    # `.localhost` and `localhost` never leave the machine, whatever they resolve to.
    if host == "localhost" or host.endswith(".localhost"):
        return False
    try:
        answers = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except OSError:
        # Does not resolve: refuse. We cannot prove it is public.
        return False
    if not answers:
        return False
    # Every address the name resolves to must be public: one private answer is enough to
    # make the fetch a request into a network we cannot see.
    return all(_public_literal(address) is True for address in answers)
