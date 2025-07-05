"""Test suite for adaptive rate limiter - TDD approach"""
import asyncio
import time
import pytest
from unittest.mock import Mock, AsyncMock

# Import the rate limiter we'll implement
from src.rate_limiting import AdaptiveRateLimiter, TokenBucket, RateLimitError


class TestTokenBucket:
    """Test token bucket algorithm implementation"""
    
    def test_initialization(self):
        """Token bucket should initialize with correct capacity"""
        bucket = TokenBucket(rate=10, capacity=10)
        assert bucket.rate == 10
        assert bucket.capacity == 10
        assert bucket.tokens == 10  # Should start full
    
    def test_token_consumption(self):
        """Tokens should be consumed when requested"""
        bucket = TokenBucket(rate=10, capacity=10)
        assert bucket.try_consume(5) == True
        assert bucket.tokens == 5
        assert bucket.try_consume(6) == False  # Not enough tokens
        assert bucket.tokens == 5  # Tokens unchanged on failure
    
    def test_token_refill(self):
        """Tokens should refill at specified rate"""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 0
        
        # Wait for tokens to refill
        time.sleep(0.1)  # Should add 1 token (10/second * 0.1 second)
        bucket._refill()
        assert bucket.tokens >= 0.9  # Account for timing variance
        assert bucket.tokens <= 1.1
    
    def test_capacity_limit(self):
        """Tokens should not exceed capacity"""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 10
        time.sleep(0.1)
        bucket._refill()
        assert bucket.tokens == 10  # Should remain at capacity
    
    @pytest.mark.asyncio
    async def test_async_wait_for_tokens(self):
        """Should wait for tokens to become available"""
        bucket = TokenBucket(rate=10, capacity=10)
        bucket.tokens = 0
        
        start = time.time()
        wait_time = await bucket.wait_for_tokens(5)
        elapsed = time.time() - start
        
        assert wait_time >= 0.4  # Should wait ~0.5 seconds for 5 tokens
        assert elapsed >= 0.4
        assert bucket.tokens < 1  # Most tokens consumed


class TestAdaptiveRateLimiter:
    """Test adaptive rate limiting with automatic scaling"""
    
    def test_initialization(self):
        """Rate limiter should start with conservative settings"""
        limiter = AdaptiveRateLimiter()
        assert limiter.base_rate == 10
        assert limiter.current_rate == 10
        assert limiter.max_rate == 50
        assert limiter.min_rate == 5
    
    def test_rate_increase_on_success(self):
        """Rate should increase gradually on successful requests"""
        limiter = AdaptiveRateLimiter()
        initial_rate = limiter.current_rate
        
        # Simulate successful requests
        for _ in range(10):
            limiter._on_success()
        
        assert limiter.current_rate > initial_rate
        assert limiter.current_rate <= limiter.max_rate
    
    def test_rate_decrease_on_429(self):
        """Rate should decrease aggressively on rate limit errors"""
        limiter = AdaptiveRateLimiter()
        limiter.current_rate = 40
        
        limiter._on_rate_limit()
        
        assert limiter.current_rate == 20  # 50% reduction
        assert limiter.current_rate >= limiter.min_rate
    
    def test_circuit_breaker_activation(self):
        """Circuit breaker should activate after multiple failures"""
        limiter = AdaptiveRateLimiter()
        
        # Trigger multiple rate limit errors
        for _ in range(5):
            limiter._on_rate_limit()
        
        assert limiter.circuit_breaker.is_open() == True
        
        # Should raise when circuit is open
        with pytest.raises(RateLimitError):
            limiter._check_circuit_breaker()
    
    @pytest.mark.asyncio
    async def test_execute_with_rate_limit(self):
        """Should execute function with rate limiting"""
        limiter = AdaptiveRateLimiter()
        mock_func = AsyncMock(return_value="success")
        
        result = await limiter.execute(mock_func, "arg1", kwarg="value")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg="value")
    
    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self):
        """Should retry with backoff on rate limit errors"""
        limiter = AdaptiveRateLimiter()
        mock_func = AsyncMock()
        
        # First call raises rate limit, second succeeds
        mock_func.side_effect = [
            RateLimitError("429 Too Many Requests"),
            "success"
        ]
        
        result = await limiter.execute(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 2
        assert limiter.current_rate < 10  # Rate should decrease
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_respect_limit(self):
        """Concurrent requests should respect rate limit"""
        limiter = AdaptiveRateLimiter()
        limiter.current_rate = 10  # 10 requests per second
        
        request_times = []
        
        async def track_request():
            await limiter.token_bucket.wait_for_tokens(1)
            request_times.append(time.time())
        
        # Launch 20 concurrent requests
        tasks = [track_request() for _ in range(20)]
        await asyncio.gather(*tasks)
        
        # Check spacing between requests
        for i in range(1, len(request_times)):
            time_diff = request_times[i] - request_times[i-1]
            assert time_diff >= 0.08  # ~10 req/s = 0.1s between requests


class TestRateLimiterIntegration:
    """Integration tests with mock API"""
    
    @pytest.mark.asyncio
    async def test_adaptive_scaling(self):
        """Rate should adapt based on API responses"""
        limiter = AdaptiveRateLimiter()
        successful_requests = 0
        rate_limited_requests = 0
        
        async def mock_api_call():
            nonlocal successful_requests, rate_limited_requests
            # Simulate API that rate limits above 30 req/s
            current_rate = limiter.current_rate
            if current_rate > 30:
                rate_limited_requests += 1
                raise RateLimitError("429")
            successful_requests += 1
            return {"status": "ok"}
        
        # Make 100 requests
        for _ in range(100):
            try:
                await limiter.execute(mock_api_call)
            except RateLimitError:
                pass
            await asyncio.sleep(0.01)
        
        # Should stabilize around 30 req/s
        assert 25 <= limiter.current_rate <= 35
        assert successful_requests > 50
        assert rate_limited_requests > 0
    
    @pytest.mark.asyncio
    async def test_burst_handling(self):
        """Should handle burst requests within capacity"""
        limiter = AdaptiveRateLimiter()
        limiter.token_bucket = TokenBucket(rate=10, capacity=50)  # Allow bursts
        
        burst_times = []
        
        async def burst_request():
            start = time.time()
            await limiter.token_bucket.wait_for_tokens(1)
            burst_times.append(time.time() - start)
        
        # Send burst of 30 requests
        tasks = [burst_request() for _ in range(30)]
        await asyncio.gather(*tasks)
        
        # First requests should be immediate (using capacity)
        immediate_requests = sum(1 for t in burst_times if t < 0.01)
        assert immediate_requests >= 20  # Most should use burst capacity


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks for rate limiter"""
    
    def test_token_bucket_performance(self, benchmark):
        """Token bucket operations should be fast"""
        bucket = TokenBucket(rate=50, capacity=50)
        
        def consume_tokens():
            for _ in range(1000):
                bucket.try_consume(1)
                bucket._refill()
        
        result = benchmark(consume_tokens)
        # Should handle 1000 operations in < 10ms
        assert result.duration < 0.01
    
    @pytest.mark.asyncio
    async def test_throughput_at_max_rate(self, benchmark):
        """Should sustain maximum configured rate"""
        limiter = AdaptiveRateLimiter()
        limiter.current_rate = 50  # Max rate
        
        request_count = 0
        
        async def make_requests():
            nonlocal request_count
            start = time.time()
            while time.time() - start < 1.0:  # Run for 1 second
                await limiter.token_bucket.wait_for_tokens(1)
                request_count += 1
        
        await make_requests()
        
        # Should achieve close to 50 req/s
        assert 45 <= request_count <= 55