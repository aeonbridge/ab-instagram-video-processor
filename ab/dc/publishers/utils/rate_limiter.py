"""
Rate Limiter Utility
Implements rate limiting for API calls to prevent quota exhaustion
"""

import time
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(
        self,
        max_requests: int,
        time_window: float,
        burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
            burst_size: Maximum burst size (defaults to max_requests)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_size = burst_size or max_requests
        self.tokens = self.burst_size
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens: int = 1, blocking: bool = True) -> bool:
        """
        Acquire tokens from bucket

        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait until tokens available

        Returns:
            True if tokens acquired, False otherwise
        """
        while True:
            with self.lock:
                self._refill()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                if not blocking:
                    return False

                # Calculate wait time
                wait_time = self._calculate_wait_time(tokens)

            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
            else:
                time.sleep(0.1)  # Small delay before retry

    def _refill(self):
        """Refill token bucket based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_update

        # Calculate tokens to add
        tokens_to_add = (elapsed / self.time_window) * self.max_requests
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_update = now

    def _calculate_wait_time(self, tokens: int) -> float:
        """Calculate time to wait for tokens to be available"""
        if self.tokens >= tokens:
            return 0

        tokens_needed = tokens - self.tokens
        return (tokens_needed / self.max_requests) * self.time_window

    def get_available_tokens(self) -> int:
        """Get number of available tokens"""
        with self.lock:
            self._refill()
            return int(self.tokens)


class QuotaTracker:
    """Track API quota usage across different resources"""

    def __init__(self):
        """Initialize quota tracker"""
        self.quotas: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def set_quota(
        self,
        resource: str,
        daily_limit: int,
        reset_hour: int = 0
    ):
        """
        Set quota for a resource

        Args:
            resource: Resource identifier (e.g., 'youtube_upload')
            daily_limit: Daily quota limit
            reset_hour: Hour (0-23) when quota resets
        """
        with self.lock:
            self.quotas[resource] = {
                'daily_limit': daily_limit,
                'reset_hour': reset_hour,
                'used': 0,
                'last_reset': datetime.now()
            }

    def consume(self, resource: str, cost: int = 1) -> bool:
        """
        Consume quota for a resource

        Args:
            resource: Resource identifier
            cost: Quota cost of operation

        Returns:
            True if quota available, False otherwise
        """
        with self.lock:
            if resource not in self.quotas:
                logger.warning(f"Unknown resource: {resource}")
                return True  # Allow if quota not configured

            quota = self.quotas[resource]
            self._check_reset(resource)

            if quota['used'] + cost > quota['daily_limit']:
                logger.warning(
                    f"Quota exceeded for {resource}: "
                    f"{quota['used']}/{quota['daily_limit']} used"
                )
                return False

            quota['used'] += cost
            logger.debug(
                f"Quota consumed for {resource}: "
                f"{quota['used']}/{quota['daily_limit']} "
                f"(cost: {cost})"
            )
            return True

    def get_remaining(self, resource: str) -> int:
        """Get remaining quota for resource"""
        with self.lock:
            if resource not in self.quotas:
                return -1  # Unknown

            quota = self.quotas[resource]
            self._check_reset(resource)
            return quota['daily_limit'] - quota['used']

    def get_reset_time(self, resource: str) -> Optional[datetime]:
        """Get next reset time for resource"""
        with self.lock:
            if resource not in self.quotas:
                return None

            quota = self.quotas[resource]
            now = datetime.now()
            reset_time = now.replace(
                hour=quota['reset_hour'],
                minute=0,
                second=0,
                microsecond=0
            )

            # If reset time has passed today, set to tomorrow
            if reset_time <= now:
                reset_time += timedelta(days=1)

            return reset_time

    def _check_reset(self, resource: str):
        """Check if quota should be reset"""
        quota = self.quotas[resource]
        now = datetime.now()

        # Check if we've passed the reset hour since last reset
        last_reset = quota['last_reset']
        reset_hour = quota['reset_hour']

        # Create reset time for today
        today_reset = now.replace(
            hour=reset_hour,
            minute=0,
            second=0,
            microsecond=0
        )

        # If current time is past today's reset and last reset was before today's reset
        if now >= today_reset and last_reset < today_reset:
            quota['used'] = 0
            quota['last_reset'] = now
            logger.info(f"Quota reset for {resource}")


class SlidingWindowLimiter:
    """Sliding window rate limiter for more precise control"""

    def __init__(self, max_requests: int, window_seconds: float):
        """
        Initialize sliding window limiter

        Args:
            max_requests: Maximum requests in window
            window_seconds: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self.lock = threading.Lock()

    def acquire(self, blocking: bool = True) -> bool:
        """
        Acquire permission to make request

        Args:
            blocking: If True, wait until request allowed

        Returns:
            True if request allowed
        """
        while True:
            with self.lock:
                now = time.time()
                cutoff = now - self.window_seconds

                # Remove old requests outside window
                while self.requests and self.requests[0] < cutoff:
                    self.requests.popleft()

                if len(self.requests) < self.max_requests:
                    self.requests.append(now)
                    return True

                if not blocking:
                    return False

                # Calculate wait time until oldest request expires
                if self.requests:
                    wait_time = self.requests[0] + self.window_seconds - now
                else:
                    wait_time = 0.1

            if wait_time > 0:
                logger.debug(
                    f"Rate limit reached ({len(self.requests)}/{self.max_requests}), "
                    f"waiting {wait_time:.2f}s"
                )
                time.sleep(wait_time)
            else:
                time.sleep(0.1)

    def get_current_count(self) -> int:
        """Get current request count in window"""
        with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # Remove old requests
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()

            return len(self.requests)


# Platform-specific rate limiters

class YouTubeRateLimiter:
    """Rate limiter for YouTube API"""

    # YouTube quota costs
    QUOTA_COSTS = {
        'video_upload': 1600,
        'video_update': 50,
        'video_delete': 50,
        'video_list': 1,
        'thumbnail_set': 50,
    }

    def __init__(self):
        """Initialize YouTube rate limiter"""
        self.quota_tracker = QuotaTracker()
        self.quota_tracker.set_quota(
            'youtube',
            daily_limit=10000,  # Default quota
            reset_hour=0  # Midnight PST
        )

        # Request rate limiter (to prevent bursts)
        self.rate_limiter = RateLimiter(
            max_requests=100,  # 100 requests
            time_window=100,    # per 100 seconds
            burst_size=10       # allow burst of 10
        )

    def acquire(self, operation: str, blocking: bool = True) -> bool:
        """
        Acquire permission for YouTube operation

        Args:
            operation: Operation type (e.g., 'video_upload')
            blocking: If True, wait until allowed

        Returns:
            True if operation allowed
        """
        cost = self.QUOTA_COSTS.get(operation, 1)

        # Check quota first
        if not self.quota_tracker.consume('youtube', cost):
            if blocking:
                reset_time = self.quota_tracker.get_reset_time('youtube')
                logger.error(
                    f"YouTube quota exhausted. Resets at {reset_time}"
                )
            return False

        # Then check rate limit
        return self.rate_limiter.acquire(tokens=1, blocking=blocking)

    def get_remaining_quota(self) -> int:
        """Get remaining YouTube quota"""
        return self.quota_tracker.get_remaining('youtube')


class TikTokRateLimiter:
    """Rate limiter for TikTok API"""

    def __init__(self):
        """Initialize TikTok rate limiter"""
        self.quota_tracker = QuotaTracker()
        self.quota_tracker.set_quota(
            'tiktok_video',
            daily_limit=10,  # 10 videos per day per user
            reset_hour=0
        )

        # Request rate limiter
        self.rate_limiter = SlidingWindowLimiter(
            max_requests=50,    # 50 requests
            window_seconds=60   # per minute
        )

    def acquire(self, operation: str = 'video_upload', blocking: bool = True) -> bool:
        """
        Acquire permission for TikTok operation

        Args:
            operation: Operation type
            blocking: If True, wait until allowed

        Returns:
            True if operation allowed
        """
        # Check daily video quota
        if operation == 'video_upload':
            if not self.quota_tracker.consume('tiktok_video', 1):
                if blocking:
                    reset_time = self.quota_tracker.get_reset_time('tiktok_video')
                    logger.error(
                        f"TikTok daily video limit reached. Resets at {reset_time}"
                    )
                return False

        # Then check rate limit
        return self.rate_limiter.acquire(blocking=blocking)

    def get_remaining_videos(self) -> int:
        """Get remaining video uploads for today"""
        return self.quota_tracker.get_remaining('tiktok_video')
