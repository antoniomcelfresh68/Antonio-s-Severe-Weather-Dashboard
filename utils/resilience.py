from __future__ import annotations

import copy
import logging
import os
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

import requests


LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = (
    float(os.getenv("UPSTREAM_CONNECT_TIMEOUT_SECONDS", "2.5")),
    float(os.getenv("UPSTREAM_READ_TIMEOUT_SECONDS", "6.0")),
)
DEFAULT_ATTEMPTS = int(os.getenv("UPSTREAM_RETRY_ATTEMPTS", "3"))
TRANSIENT_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}

_STALE_CACHE_LOCK = threading.Lock()
_STALE_CACHE: dict[str, dict[str, Any]] = {}

_METRICS_LOCK = threading.Lock()
_METRICS: dict[str, dict[str, Any]] = defaultdict(
    lambda: {
        "success_count": 0,
        "failure_count": 0,
        "stale_fallback_count": 0,
        "last_latency_ms": None,
        "last_success_at": None,
        "last_failure_at": None,
        "last_error": None,
    }
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _copy_value(value: Any) -> Any:
    try:
        return copy.deepcopy(value)
    except Exception:
        return value


def _normalize_timeout(timeout: float | tuple[float, float] | None) -> tuple[float, float]:
    if timeout is None:
        return DEFAULT_TIMEOUT
    if isinstance(timeout, tuple):
        connect, read = timeout
        return float(connect), float(read)
    return float(timeout), float(timeout)


def _is_transient_error(exc: Exception) -> bool:
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    if isinstance(exc, requests.HTTPError):
        status_code = exc.response.status_code if exc.response is not None else None
        return status_code in TRANSIENT_STATUS_CODES
    if isinstance(exc, requests.RequestException):
        return True
    return False


def _friendly_error_message(exc: Exception) -> str:
    if isinstance(exc, requests.Timeout):
        return "Upstream service timed out."
    if isinstance(exc, requests.ConnectionError):
        return "Could not reach the upstream service."
    if isinstance(exc, requests.HTTPError):
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code == 429:
            return "Upstream service is rate limiting requests."
        if status_code is not None and status_code >= 500:
            return "Upstream service returned a server error."
        if status_code is not None:
            return f"Upstream service returned HTTP {status_code}."
    return "Upstream data is unavailable right now."


def _record_metric(endpoint: str, *, ok: bool, latency_ms: float, error: str | None = None, used_stale: bool = False) -> None:
    with _METRICS_LOCK:
        metric = _METRICS[endpoint]
        metric["last_latency_ms"] = round(latency_ms, 1)
        if ok:
            metric["success_count"] += 1
            metric["last_success_at"] = utc_now_iso()
        else:
            metric["failure_count"] += 1
            metric["last_failure_at"] = utc_now_iso()
            metric["last_error"] = error
        if used_stale:
            metric["stale_fallback_count"] += 1


def get_metrics_snapshot() -> dict[str, dict[str, Any]]:
    with _METRICS_LOCK:
        return {name: dict(values) for name, values in _METRICS.items()}


def get_stale_cache_snapshot() -> dict[str, dict[str, Any]]:
    with _STALE_CACHE_LOCK:
        return {key: dict(value) for key, value in _STALE_CACHE.items()}


def _cache_get(cache_key: str | None) -> dict[str, Any] | None:
    if not cache_key:
        return None
    with _STALE_CACHE_LOCK:
        entry = _STALE_CACHE.get(cache_key)
        return dict(entry) if entry else None


def _cache_set(cache_key: str | None, value: Any) -> None:
    if not cache_key:
        return
    with _STALE_CACHE_LOCK:
        _STALE_CACHE[cache_key] = {
            "value": _copy_value(value),
            "cached_at": utc_now_iso(),
        }


def build_data_status(
    *,
    source: str,
    endpoint: str,
    status: str,
    summary: str,
    error_message: str | None = None,
    cached_at: str | None = None,
    source_timestamp: str | None = None,
    latency_ms: float | None = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "endpoint": endpoint,
        "status": status,
        "summary": summary,
        "error_message": error_message,
        "cached_at": cached_at,
        "source_timestamp": source_timestamp,
        "latency_ms": round(latency_ms, 1) if latency_ms is not None else None,
        "checked_at": utc_now_iso(),
        "degraded": status != "live",
    }


def execute_with_stale_fallback(
    *,
    endpoint: str,
    source: str,
    cache_key: str | None,
    loader: Callable[[], Any],
    default_factory: Callable[[], Any],
    validator: Callable[[Any], Any] | None = None,
    attempts: int = DEFAULT_ATTEMPTS,
) -> tuple[Any, dict[str, Any]]:
    start_time = time.perf_counter()
    last_error: Exception | None = None

    for attempt in range(1, max(attempts, 1) + 1):
        try:
            value = loader()
            if validator is not None:
                value = validator(value)
            latency_ms = (time.perf_counter() - start_time) * 1000
            _cache_set(cache_key, value)
            _record_metric(endpoint, ok=True, latency_ms=latency_ms)
            LOGGER.info("upstream_ok endpoint=%s latency_ms=%.1f attempt=%s", endpoint, latency_ms, attempt)
            return _copy_value(value), build_data_status(
                source=source,
                endpoint=endpoint,
                status="live",
                summary="Live data loaded successfully.",
                latency_ms=latency_ms,
            )
        except Exception as exc:
            last_error = exc
            transient = _is_transient_error(exc)
            if attempt >= max(attempts, 1) or not transient:
                break
            time.sleep(min(0.35 * (2 ** (attempt - 1)), 1.2))

    latency_ms = (time.perf_counter() - start_time) * 1000
    stale_entry = _cache_get(cache_key)
    error_message = _friendly_error_message(last_error or RuntimeError("Unknown upstream failure"))

    if stale_entry is not None:
        _record_metric(endpoint, ok=False, latency_ms=latency_ms, error=error_message, used_stale=True)
        LOGGER.warning(
            "upstream_stale_fallback endpoint=%s latency_ms=%.1f error=%s",
            endpoint,
            latency_ms,
            error_message,
        )
        return _copy_value(stale_entry["value"]), build_data_status(
            source=source,
            endpoint=endpoint,
            status="stale",
            summary="Showing the last successful update because live data could not be refreshed.",
            error_message=error_message,
            cached_at=stale_entry.get("cached_at"),
            latency_ms=latency_ms,
        )

    _record_metric(endpoint, ok=False, latency_ms=latency_ms, error=error_message)
    LOGGER.warning(
        "upstream_unavailable endpoint=%s latency_ms=%.1f error=%s",
        endpoint,
        latency_ms,
        error_message,
    )
    return default_factory(), build_data_status(
        source=source,
        endpoint=endpoint,
        status="unavailable",
        summary="Live data could not be loaded.",
        error_message=error_message,
        latency_ms=latency_ms,
    )


def request_json(
    *,
    url: str,
    headers: Mapping[str, str],
    endpoint: str,
    source: str,
    params: Mapping[str, Any] | None = None,
    timeout: float | tuple[float, float] | None = None,
    cache_key: str | None = None,
    default_factory: Callable[[], Any] = dict,
    validator: Callable[[Any], Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    normalized_timeout = _normalize_timeout(timeout)

    def loader() -> Any:
        response = requests.get(url, params=params, headers=dict(headers), timeout=normalized_timeout)
        response.raise_for_status()
        return response.json()

    return execute_with_stale_fallback(
        endpoint=endpoint,
        source=source,
        cache_key=cache_key,
        loader=loader,
        default_factory=default_factory,
        validator=validator,
    )


def request_text(
    *,
    url: str,
    headers: Mapping[str, str],
    endpoint: str,
    source: str,
    params: Mapping[str, Any] | None = None,
    timeout: float | tuple[float, float] | None = None,
    cache_key: str | None = None,
    default_factory: Callable[[], str] | None = None,
    validator: Callable[[str], str] | None = None,
) -> tuple[str, dict[str, Any]]:
    normalized_timeout = _normalize_timeout(timeout)

    def loader() -> str:
        response = requests.get(url, params=params, headers=dict(headers), timeout=normalized_timeout)
        response.raise_for_status()
        return response.text

    return execute_with_stale_fallback(
        endpoint=endpoint,
        source=source,
        cache_key=cache_key,
        loader=loader,
        default_factory=default_factory or (lambda: ""),
        validator=validator,
    )


def probe_url(
    *,
    url: str,
    headers: Mapping[str, str],
    endpoint: str,
    source: str,
    timeout: float | tuple[float, float] | None = None,
    cache_key: str | None = None,
    validator: Callable[[requests.Response], bool] | None = None,
) -> tuple[bool, dict[str, Any]]:
    normalized_timeout = _normalize_timeout(timeout)

    def loader() -> bool:
        response = requests.get(url, headers=dict(headers), timeout=normalized_timeout, stream=True)
        try:
            response.raise_for_status()
            if validator is not None:
                return validator(response)
            return True
        finally:
            response.close()

    return execute_with_stale_fallback(
        endpoint=endpoint,
        source=source,
        cache_key=cache_key,
        loader=loader,
        default_factory=lambda: False,
    )
