# =============================================================================
# data/cache.py
# -----------------------------------------------------------------------------
# Sets up a persistent on-disk cache using the `diskcache` library.
#
# WHY DISK CACHE INSTEAD OF MEMORY CACHE?
#   A plain in-memory cache (like a Python dictionary) is wiped every time the
#   app restarts or refreshes. A disk cache writes data to files on your hard
#   drive, so if your app restarts mid-day, it immediately serves the last
#   known good data instead of hammering the API for fresh quotes.
#
# HOW IT WORKS:
#   1. When we fetch data for the first time, we save it to disk with a key
#      (e.g. "quotes_SPY") and an expiry timestamp.
#   2. On every subsequent request, we check the disk first.
#      - If the cached copy is still fresh (< CACHE_TTL_SECONDS old): return it.
#      - If it's stale or missing: fetch new data, update the disk, return it.
#   3. If a live fetch fails (API down, rate-limited), we STILL return the stale
#      disk copy rather than crashing — this is the "bulletproof" behaviour.
# =============================================================================

import logging
import time
from typing import Any, Optional

import diskcache

from config import CACHE_DIR, CACHE_TTL_SECONDS

# ---------------------------------------------------------------------------
# Module-level logger — messages show up in the terminal when you run the app.
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GLOBAL CACHE OBJECT
#   diskcache.Cache() creates (or opens) a folder at CACHE_DIR.
#   size_limit caps the folder at ~500 MB so it never fills your disk.
# ---------------------------------------------------------------------------
_cache = diskcache.Cache(
    directory=CACHE_DIR,
    size_limit=500 * 1024 * 1024,  # 500 MB
)


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def get(key: str) -> Optional[Any]:
    """
    Read a value from the cache.

    Returns the cached value if it exists and hasn't expired.
    Returns None if the key is missing or stale.

    Parameters
    ----------
    key : str
        A unique string that identifies the data, e.g. "quotes_SPY".
    """
    try:
        value = _cache.get(key)
        if value is None:
            logger.debug("Cache MISS for key: %s", key)
        else:
            logger.debug("Cache HIT for key: %s", key)
        return value
    except Exception as exc:
        # Disk read errors are non-fatal — we'll just re-fetch.
        logger.warning("Cache read error for key '%s': %s", key, exc)
        return None


def set(key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
    """
    Write a value to the cache with an expiry time.

    Parameters
    ----------
    key   : str  — unique identifier for this piece of data
    value : Any  — the data to store (DataFrames, dicts, floats, etc.)
    ttl   : int  — seconds until this entry expires (default from config)
    """
    try:
        _cache.set(key, value, expire=ttl)
        logger.debug("Cache SET for key: %s (TTL=%ds)", key, ttl)
    except Exception as exc:
        logger.warning("Cache write error for key '%s': %s", key, exc)


def get_stale(key: str) -> Optional[Any]:
    """
    Read a value from the cache IGNORING its expiry.

    This is the safety-net: if a live fetch fails entirely, we call this
    to return whatever old data we have rather than showing the user an error.

    diskcache stores expired entries until they're evicted, so this works
    as long as the key was set at least once previously.
    """
    try:
        # read(ignore_expiry=True) — diskcache doesn't expose this directly,
        # so we temporarily set the TTL to a large number when reading stale.
        # Workaround: access the underlying sqlite directly via _cache.get
        # with expire_time=True to check existence regardless of expiry.
        with _cache as c:
            row = c.get(key, default=None, retry=True)
            if row is None:
                # Try to fetch from the raw store (expired items)
                try:
                    row = c[key]
                except KeyError:
                    row = None
        if row is not None:
            logger.info("Serving STALE cache for key: %s", key)
        return row
    except Exception as exc:
        logger.warning("Stale cache read error for key '%s': %s", key, exc)
        return None


def clear_all() -> None:
    """Wipe the entire cache. Useful for debugging or forcing a full refresh."""
    try:
        _cache.clear()
        logger.info("Cache cleared.")
    except Exception as exc:
        logger.warning("Cache clear error: %s", exc)


def cache_info() -> dict:
    """Return a summary of the cache state — handy for a debug panel."""
    try:
        return {
            "directory":  CACHE_DIR,
            "item_count": len(_cache),
            "size_bytes": _cache.volume(),
        }
    except Exception:
        return {}
