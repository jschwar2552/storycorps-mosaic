"""Adaptive rate limiter for aggressive but safe API consumption"""
import asyncio
import time
from dataclasses import dataclass
from typing import Optional, Callable, Any


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass


class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, rate: float, capacity: Optional[float] = None):
        self.rate = rate  # Tokens per second
        self.capacity = capacity or rate  # Max tokens
        self.tokens = self.capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def try_consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens, return True if successful"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    async def wait_for_tokens(self, tokens: int = 1) -> float:
        """Wait for tokens to become available, return wait time"""
        start_time = time.time()
        
        while True:
            async with self._lock:
                self._refill()
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return time.time() - start_time
                
                # Calculate wait time
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.rate
            
            # Wait for tokens to refill (outside lock to allow concurrent waiters)
            await asyncio.sleep(max(wait_time, 0.01))
    
    def update_rate(self, new_rate: float):
        """Update token generation rate"""
        self._refill()  # Apply pending refills at old rate
        self.rate = new_rate
        # Adjust capacity proportionally
        self.capacity = max(new_rate, self.capacity * (new_rate / self.rate))


@dataclass
class CircuitBreaker:
    """Circuit breaker to prevent overwhelming failed API"""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    
    def __init__(self):
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def record_success(self):
        """Record successful request"""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == "open":
            # Check if recovery timeout has passed
            if (self.last_failure_time and 
                time.time() - self.last_failure_time > self.recovery_timeout):
                self.state = "half-open"
                return False
            return True
        return False


class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on API responses"""
    
    def __init__(self, 
                 base_rate: float = 10,
                 max_rate: float = 50,
                 min_rate: float = 5,
                 increase_factor: float = 1.1,
                 decrease_factor: float = 0.5):
        self.base_rate = base_rate
        self.max_rate = max_rate
        self.min_rate = min_rate
        self.current_rate = base_rate
        self.increase_factor = increase_factor
        self.decrease_factor = decrease_factor
        
        # Initialize token bucket with burst capacity
        self.token_bucket = TokenBucket(rate=base_rate, capacity=base_rate * 2)
        self.circuit_breaker = CircuitBreaker()
        
        # Statistics
        self.successful_requests = 0
        self.rate_limited_requests = 0
    
    def _on_success(self):
        """Handle successful request"""
        self.successful_requests += 1
        self.circuit_breaker.record_success()
        
        # Gradually increase rate
        if self.current_rate < self.max_rate:
            self.current_rate = min(
                self.current_rate * self.increase_factor,
                self.max_rate
            )
            self.token_bucket.update_rate(self.current_rate)
    
    def _on_rate_limit(self):
        """Handle rate limit error"""
        self.rate_limited_requests += 1
        self.circuit_breaker.record_failure()
        
        # Aggressively decrease rate
        self.current_rate = max(
            self.current_rate * self.decrease_factor,
            self.min_rate
        )
        self.token_bucket.update_rate(self.current_rate)
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker is open"""
        if self.circuit_breaker.is_open():
            raise RateLimitError("Circuit breaker is open - too many failures")
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with rate limiting and retries"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            # Check circuit breaker
            self._check_circuit_breaker()
            
            # Wait for rate limit token
            await self.token_bucket.wait_for_tokens(1)
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                self._on_success()
                return result
                
            except RateLimitError as e:
                self._on_rate_limit()
                retry_count += 1
                
                if retry_count >= max_retries:
                    raise
                
                # Exponential backoff
                wait_time = (2 ** retry_count) * 0.5
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                # Other errors pass through
                raise
        
        raise RateLimitError(f"Max retries ({max_retries}) exceeded")
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        return {
            "current_rate": self.current_rate,
            "successful_requests": self.successful_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "circuit_breaker_state": self.circuit_breaker.state,
            "tokens_available": self.token_bucket.tokens
        }