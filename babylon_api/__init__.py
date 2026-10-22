"""Babylon API: an HTTP layer on top of Babylon.core (apply / destroy).

Kept outside the `Babylon` package on purpose: the CLI must not depend on FastAPI.
Install with `pip install cosmotech-babylon[api]`, run with `uvicorn babylon_api.app:app`.
"""
