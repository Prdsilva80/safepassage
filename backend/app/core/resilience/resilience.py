"""
SafePassage — Resilience Layer

Patterns implemented:
  1. Circuit Breaker       → Stops cascade failures when DB/Redis/AI is down
  2. Retry with backoff    → Transient failure recovery (tenacity)
  3. Graceful Degradation  → App stays functional when components fail
  4. Health Checks         → Deep health probes for each dependency
  5. Connection Pool Guard → Protects DB pool from exhaustion
  6. Fallback Cache        → Serves stale data during outages
  7. Bulkhead              → Isolates AI calls from core safety features
  8. Timeout Enforcement   → No request hangs forever
"""
import asyncio
import time
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


# ── 1. Circuit Breaker ────────────────────────────────────────────────────────

class CircuitState(str, Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing — reject requests fast
    HALF_OPEN = "half_open" # Testing recovery


class CircuitBreaker:
    """
    Circuit Breaker pattern.

    CLOSED  → tracks failures
    OPEN    → immediately raises CircuitOpenError (fast-fail)
    HALF_OPEN → allows one probe request through to test recovery

    Tuned conservatively for safety-critical context:
    - Opens quickly (3 failures)
    - Recovers slowly (60s minimum)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0,
        half_open_max_calls: int = 1,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.timeout_seconds:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("circuit_half_open", circuit=self.name)
        return self._state

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute function through circuit breaker."""
        if self.state == CircuitState.OPEN:
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN — fast-failing")

        if self.state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self.half_open_max_calls:
                raise CircuitOpenError(f"Circuit '{self.name}' HALF_OPEN — max probe calls reached")
            self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except CircuitOpenError:
            raise
        except Exception as exc:
            self._on_failure(exc)
            raise

    def _on_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                logger.info("circuit_closed", circuit=self.name)
        else:
            self._failure_count = 0

    def _on_failure(self, exc: Exception) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.error(
                "circuit_opened",
                circuit=self.name,
                failures=self._failure_count,
                error=str(exc),
            )

    def get_status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "last_failure": (
                datetime.fromtimestamp(self._last_failure_time, tz=timezone.utc).isoformat()
                if self._last_failure_time else None
            ),
        }


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is open."""


# Circuit breakers for each external dependency
circuits = {
    "database": CircuitBreaker("database", failure_threshold=3, timeout_seconds=30),
    "redis": CircuitBreaker("redis", failure_threshold=5, timeout_seconds=20),
    "ai": CircuitBreaker("ai", failure_threshold=3, timeout_seconds=60),
    "external_api": CircuitBreaker("external_api", failure_threshold=3, timeout_seconds=45),
}


# ── 2. Retry Decorator ────────────────────────────────────────────────────────

async def with_retry(
    func: Callable,
    *args: Any,
    max_attempts: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError, OSError),
    **kwargs: Any,
) -> Any:
    """
    Async retry with exponential backoff + jitter.
    Only retries on transient errors — not on validation errors or auth failures.
    """
    delay = initial_delay
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as exc:
            last_exc = exc
            if attempt == max_attempts:
                break
            # Add jitter to avoid thundering herd
            import random
            jittered = delay * (0.5 + random.random())
            logger.warning(
                "retry_attempt",
                func=getattr(func, "__name__", str(func)),
                attempt=attempt,
                delay_s=round(jittered, 2),
                error=str(exc),
            )
            await asyncio.sleep(jittered)
            delay = min(delay * backoff_factor, max_delay)

    raise last_exc  # type: ignore


# ── 3. Graceful Degradation ───────────────────────────────────────────────────

class DegradedModeState:
    """
    Tracks which components are degraded and what fallbacks to use.
    The system MUST remain operational for core safety features even if:
    - Redis is down (alerts go direct over WebSocket only)
    - AI is down (fallback assessment used)
    - Database read replica fails (use primary)
    - Non-critical services fail (log and continue)
    """

    def __init__(self) -> None:
        self._degraded: dict[str, str] = {}  # {component: reason}

    def mark_degraded(self, component: str, reason: str) -> None:
        if component not in self._degraded:
            logger.error("component_degraded", component=component, reason=reason)
        self._degraded[component] = reason

    def mark_recovered(self, component: str) -> None:
        if component in self._degraded:
            logger.info("component_recovered", component=component)
            del self._degraded[component]

    def is_degraded(self, component: str) -> bool:
        return component in self._degraded

    def get_status(self) -> dict[str, Any]:
        return {
            "fully_operational": len(self._degraded) == 0,
            "degraded_components": self._degraded,
        }


degraded_state = DegradedModeState()


# ── 4. Stale Cache (Fallback Cache) ───────────────────────────────────────────

class StaleWhileRevalidateCache:
    """
    Simple in-memory cache with stale-while-revalidate semantics.
    Serves cached data during DB/Redis outages.
    Used for: nearby reports, shelter lists, route lists (read-heavy, safety-critical).
    """

    def __init__(self, max_age_seconds: int = 60, stale_ttl_seconds: int = 300) -> None:
        self.max_age = max_age_seconds
        self.stale_ttl = stale_ttl_seconds
        self._cache: dict[str, tuple[Any, float]] = {}  # {key: (value, timestamp)}

    def get(self, key: str) -> tuple[Any | None, bool]:
        """Returns (value, is_stale). value=None if expired beyond stale TTL."""
        if key not in self._cache:
            return None, False
        value, stored_at = self._cache[key]
        age = time.time() - stored_at
        if age < self.max_age:
            return value, False
        if age < self.stale_ttl:
            return value, True  # stale but usable
        del self._cache[key]
        return None, False

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = (value, time.time())

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        keys_to_del = [k for k in self._cache if k.startswith(prefix)]
        for k in keys_to_del:
            del self._cache[k]


# Separate caches per resource type with appropriate TTLs
nearby_reports_cache = StaleWhileRevalidateCache(max_age_seconds=30, stale_ttl_seconds=120)
shelter_cache = StaleWhileRevalidateCache(max_age_seconds=60, stale_ttl_seconds=600)
route_cache = StaleWhileRevalidateCache(max_age_seconds=120, stale_ttl_seconds=900)


# ── 5. Timeout Enforcer ───────────────────────────────────────────────────────

async def with_timeout(coro: Any, timeout_seconds: float, fallback: Any = None) -> Any:
    """
    Execute a coroutine with a timeout.
    Returns fallback value if timeout exceeded (instead of raising).
    Critical for AI calls and external services.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning("operation_timeout", timeout_s=timeout_seconds)
        return fallback


# ── 6. Deep Health Checks ─────────────────────────────────────────────────────

async def check_database_health(db_engine: Any) -> dict[str, Any]:
    """Execute a lightweight DB health query."""
    start = time.perf_counter()
    try:
        async with db_engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        circuits["database"].mark_recovered if hasattr(circuits["database"], 'mark_recovered') else None  # type: ignore
        degraded_state.mark_recovered("database")
        return {"status": "ok", "latency_ms": round(latency_ms, 2)}
    except Exception as exc:
        degraded_state.mark_degraded("database", str(exc))
        return {"status": "error", "error": str(exc)}


async def check_redis_health(redis_client: Any) -> dict[str, Any]:
    """Ping Redis."""
    start = time.perf_counter()
    try:
        await redis_client.ping()
        latency_ms = (time.perf_counter() - start) * 1000
        degraded_state.mark_recovered("redis")
        return {"status": "ok", "latency_ms": round(latency_ms, 2)}
    except Exception as exc:
        degraded_state.mark_degraded("redis", str(exc))
        return {"status": "error", "error": str(exc)}


async def check_ai_health() -> dict[str, Any]:
    """Check AI service availability with a minimal test call."""
    try:
        from app.core.config import settings
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        # Minimal call — just checks connectivity
        msg = await asyncio.wait_for(
            client.messages.create(
                model=settings.AI_MODEL,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            ),
            timeout=10.0,
        )
        degraded_state.mark_recovered("ai")
        return {"status": "ok", "model": settings.AI_MODEL}
    except Exception as exc:
        degraded_state.mark_degraded("ai", str(exc))
        return {"status": "error", "error": str(exc)[:100]}


async def full_health_check(db_engine: Any, redis_client: Any | None) -> dict[str, Any]:
    """
    Run all health checks concurrently.
    Returns structured status suitable for Kubernetes probes and monitoring.
    """
    checks = [check_database_health(db_engine)]
    if redis_client:
        checks.append(check_redis_health(redis_client))
    else:
        checks.append(asyncio.coroutine(lambda: {"status": "not_configured"})())  # type: ignore

    results = await asyncio.gather(*checks, return_exceptions=True)

    db_status = results[0] if not isinstance(results[0], Exception) else {"status": "error", "error": str(results[0])}
    redis_status = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else {"status": "error"}

    all_ok = all(
        r.get("status") == "ok"
        for r in [db_status, redis_status]
        if isinstance(r, dict)
    )

    return {
        "status": "ok" if all_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": db_status,
            "redis": redis_status,
            "circuits": {name: cb.get_status() for name, cb in circuits.items()},
        },
        **degraded_state.get_status(),
    }


# ── 7. Bulkhead — AI call isolation ──────────────────────────────────────────

class Bulkhead:
    """
    Limits concurrent calls to a resource (e.g. AI API).
    Prevents one slow external service from consuming all worker threads.
    Core safety features (reports, SOS, shelters) are NEVER gated by this.
    """

    def __init__(self, name: str, max_concurrent: int = 5, queue_size: int = 10) -> None:
        self.name = name
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._queue_size = queue_size
        self._waiting = 0

    async def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        if self._waiting >= self._queue_size:
            raise BulkheadFullError(f"Bulkhead '{self.name}' queue full — request rejected")
        self._waiting += 1
        try:
            async with self._semaphore:
                self._waiting -= 1
                return await func(*args, **kwargs)
        except BulkheadFullError:
            self._waiting -= 1
            raise


class BulkheadFullError(Exception):
    """Raised when bulkhead queue is full."""


# AI calls are bulkheaded — max 5 concurrent, queue 10
ai_bulkhead = Bulkhead("ai_assessment", max_concurrent=5, queue_size=10)


# ── 8. Connection Pool Monitor ────────────────────────────────────────────────

class PoolMonitor:
    """
    Monitors DB connection pool health.
    Alerts when pool is near exhaustion (>80% used).
    """

    ALERT_THRESHOLD = 0.8

    def check(self, pool: Any) -> dict[str, Any]:
        try:
            size = pool.size()
            checked_out = pool.checkedout()
            overflow = pool.overflow()
            utilization = checked_out / max(size, 1)

            if utilization >= self.ALERT_THRESHOLD:
                logger.warning(
                    "db_pool_near_exhaustion",
                    size=size,
                    checked_out=checked_out,
                    utilization=f"{utilization:.0%}",
                )

            return {
                "pool_size": size,
                "checked_out": checked_out,
                "overflow": overflow,
                "utilization": round(utilization, 3),
                "status": "warning" if utilization >= self.ALERT_THRESHOLD else "ok",
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}


pool_monitor = PoolMonitor()