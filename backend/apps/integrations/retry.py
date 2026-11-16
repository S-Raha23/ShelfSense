import logging
import random
import time

from .clients.base import TransientMarketplaceError

logger = logging.getLogger(__name__)


def call_with_retry(fn, *, attempts: int = 4, base_delay: float = 0.5, max_delay: float = 8.0, sleep=time.sleep):
    """Call `fn`, retrying transient third-party failures with exponential backoff + jitter.

    Delays: ~0.5s, 1s, 2s ... capped at `max_delay`. Jitter spreads retries out so many
    clients don't hammer a throttled API in lock-step. Non-transient errors are raised
    immediately — retrying a bad request just wastes quota.
    """
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except TransientMarketplaceError as exc:
            if attempt == attempts:
                raise
            delay = min(max_delay, base_delay * 2 ** (attempt - 1)) * random.uniform(0.8, 1.2)
            logger.warning("Transient marketplace error (%s); retry %d/%d in %.2fs", exc, attempt, attempts - 1, delay)
            sleep(delay)
