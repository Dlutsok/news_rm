import time
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    In-memory rate limiter for FastAPI applications.
    Tracks requests per IP address with different limits for different endpoints.
    """
    
    def __init__(self, config=None):
        # Store request timestamps for each IP: {ip: deque([timestamp1, timestamp2, ...])}
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Default rate limits if no config provided (увеличены для разработки)
        default_limits = {
            "/api/auth": (200, 60),          # Auth endpoints: 200 req/min (увеличено для разработки)
            "/api/news/parse": (20, 60),     # Parsing: 20 req/min (heavy operations)
            "/api/news-generation": (100, 60), # Content generation: 100 req/min (увеличено)
            "/api/admin": (200, 60),         # Admin operations: 200 req/min (увеличено)
            "/api/expenses": (150, 60),      # Expenses: 150 req/min
            "/api/settings": (100, 60),      # Settings: 100 req/min
            "/api/users": (120, 60),         # User management: 120 req/min
            "/api/news": (300, 60),          # General news API: 300 req/min
            "default": (300, 60)             # Default: 300 req/min
        }
        
        # Use config values if provided
        if config:
            self.rate_limits = {
                "/api/auth": (config.RATE_LIMIT_AUTH, 60),
                "/api/news/parse": (config.RATE_LIMIT_PARSING, 60),
                "/api/news-generation": (config.RATE_LIMIT_GENERATION, 60),
                "/api/admin": (config.RATE_LIMIT_ADMIN, 60),
                "/api/expenses": (config.RATE_LIMIT_DEFAULT, 60),
                "/api/settings": (config.RATE_LIMIT_ADMIN, 60),
                "/api/users": (config.RATE_LIMIT_ADMIN, 60),
                "/api/news": (config.RATE_LIMIT_DEFAULT, 60),
                "default": (config.RATE_LIMIT_DEFAULT, 60)
            }
        else:
            self.rate_limits = default_limits
        
        # Exempt paths (no rate limiting)
        self.exempt_paths = [
            "/health",
            "/api/health",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            # Мониторинг endpoints - исключения для автоматических запросов
            "/api/admin/monitoring/overview",
            "/api/admin/monitoring/system",
            "/api/admin/monitoring/services",
            "/api/admin/monitoring/alerts",
            "/api/admin/stats/database"
        ]
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (in case of proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP if multiple are present
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to client host
        client_host = getattr(request.client, "host", "unknown")
        return client_host
    
    def _get_rate_limit_for_path(self, path: str) -> Tuple[int, int]:
        """Get rate limit (requests, window_seconds) for given path."""
        # Check exact matches and patterns
        for pattern, (requests, window) in self.rate_limits.items():
            if pattern == "default":
                continue
            if path.startswith(pattern):
                return requests, window
        
        # Return default rate limit
        return self.rate_limits["default"]
    
    def _cleanup_old_requests(self, ip: str, window_seconds: int):
        """Remove request timestamps older than the window."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        requests_deque = self.requests[ip]
        
        # Remove old timestamps from the left side of deque
        while requests_deque and requests_deque[0] < cutoff_time:
            requests_deque.popleft()
    
    def is_allowed(self, request: Request) -> Tuple[bool, Optional[dict]]:
        """
        Check if request is allowed based on rate limits.
        Returns (is_allowed, rate_limit_info)
        """
        path = request.url.path
        
        # Skip rate limiting for exempt paths
        if path in self.exempt_paths:
            return True, None
        
        client_ip = self._get_client_ip(request)
        requests_limit, window_seconds = self._get_rate_limit_for_path(path)
        
        # Clean up old requests
        self._cleanup_old_requests(client_ip, window_seconds)
        
        # Check current request count
        current_requests = len(self.requests[client_ip])
        
        rate_limit_info = {
            "limit": requests_limit,
            "remaining": max(0, requests_limit - current_requests - 1),
            "reset_time": int(time.time() + window_seconds),
            "window_seconds": window_seconds
        }
        
        if current_requests >= requests_limit:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip} on path {path}. "
                f"Requests: {current_requests}/{requests_limit} in {window_seconds}s window"
            )
            return False, rate_limit_info
        
        # Add current request timestamp
        self.requests[client_ip].append(time.time())
        
        # Update remaining count
        rate_limit_info["remaining"] = max(0, requests_limit - len(self.requests[client_ip]))
        
        return True, rate_limit_info
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        current_time = time.time()
        
        stats = {
            "active_ips": len(self.requests),
            "total_requests_tracked": sum(len(deque) for deque in self.requests.values()),
            "rate_limit_rules": dict(self.rate_limits),
            "exempt_paths": self.exempt_paths
        }
        
        return stats


# Global rate limiter instance - will be initialized in main.py
rate_limiter = None


def initialize_rate_limiter(config):
    """Initialize global rate limiter with configuration."""
    global rate_limiter
    if config.RATE_LIMITING_ENABLED:
        rate_limiter = RateLimiter(config)
        logger.info("Rate limiting initialized and enabled")
    else:
        rate_limiter = None
        logger.info("Rate limiting disabled via configuration")


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting.
    """
    # Skip if rate limiter is not initialized or disabled
    if rate_limiter is None:
        return await call_next(request)
    
    # Check rate limit
    is_allowed, rate_limit_info = rate_limiter.is_allowed(request)
    
    if not is_allowed:
        # Return 429 Too Many Requests
        headers = {}
        if rate_limit_info:
            headers.update({
                "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                "X-RateLimit-Reset": str(rate_limit_info["reset_time"]),
                "Retry-After": str(rate_limit_info["window_seconds"])
            })
        
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please try again later.",
                "error": "rate_limit_exceeded",
                "limit": rate_limit_info["limit"] if rate_limit_info else None,
                "window_seconds": rate_limit_info["window_seconds"] if rate_limit_info else None
            },
            headers=headers
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers to response
    if rate_limit_info:
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset_time"])
    
    return response