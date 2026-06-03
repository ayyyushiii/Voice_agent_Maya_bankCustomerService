"""Configure SSL CA bundle for macOS Python (required for LiveKit HTTPS API calls)."""

from __future__ import annotations

import os


def configure_ssl_certs() -> None:
    try:
        import certifi

        ca_bundle = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", ca_bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_bundle)
    except ImportError:
        pass
