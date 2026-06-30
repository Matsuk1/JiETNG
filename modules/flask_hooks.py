"""Shared Flask request/response hooks."""

import gc


DEMO_CORS_ORIGIN = "https://jietng.matsuk1.com"


def apply_security_headers(response):
    """Apply baseline browser security headers and run light GC."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:;"
    )

    gc.collect(0)
    return response


def demo_cors(response):
    response.headers["Access-Control-Allow-Origin"] = DEMO_CORS_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response
