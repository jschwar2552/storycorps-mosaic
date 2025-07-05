"""Integration tests for rate limiter with mock API"""
import asyncio
import pytest
import httpx
from src.rate_limiting import AdaptiveRateLimiter, RateLimitError


class TestMockAPIIntegration:
    """Test rate limiter against mock StoryCorps API"""
    
    @pytest.fixture
    async def mock_api_client(self):
        """Create HTTP client for mock API"""
        async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_find_rate_limit(self, mock_api_client):
        """Test finding the API's actual rate limit"""
        limiter = AdaptiveRateLimiter(base_rate=20, max_rate=50)
        
        async def fetch_stories():
            response = await mock_api_client.get("/wp-json/storycorps/v1/interviews")
            if response.status_code == 429:
                raise RateLimitError("Rate limited")
            return response.json()
        
        # Track successful requests and rate limits
        successful = 0
        rate_limited = 0
        
        # Run for 5 seconds
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < 5:
            try:
                await limiter.execute(fetch_stories)
                successful += 1
            except RateLimitError:
                rate_limited += 1
            
            # Small delay to prevent CPU spinning
            await asyncio.sleep(0.001)
        
        # Should stabilize around 30 req/s (mock API limit)
        avg_rate = successful / 5
        assert 25 <= avg_rate <= 35
        assert rate_limited > 0  # Should have hit limit at least once
        assert 25 <= limiter.current_rate <= 35
        
        print(f"Discovered rate limit: ~{limiter.current_rate:.1f} req/s")
        print(f"Successful requests: {successful} ({avg_rate:.1f}/s)")
        print(f"Rate limited requests: {rate_limited}")
    
    @pytest.mark.asyncio
    async def test_burst_capacity(self, mock_api_client):
        """Test handling burst requests"""
        limiter = AdaptiveRateLimiter(base_rate=30, max_rate=50)
        limiter.current_rate = 30  # Set to known limit
        
        async def fetch_story(story_id):
            response = await mock_api_client.get(
                f"/wp-json/storycorps/v1/interviews/{story_id}"
            )
            if response.status_code == 429:
                raise RateLimitError("Rate limited")
            return response.json()
        
        # Send burst of 50 requests
        tasks = []
        for i in range(50):
            task = limiter.execute(fetch_story, f"story_{i}")
            tasks.append(task)
        
        # Some should succeed, some should be rate limited
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        rate_limited = sum(1 for r in results if isinstance(r, RateLimitError))
        
        assert successful >= 25  # At least some should succeed
        assert rate_limited > 0  # Some should be rate limited
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, mock_api_client):
        """Test circuit breaker recovery after failures"""
        limiter = AdaptiveRateLimiter()
        limiter.circuit_breaker.recovery_timeout = 2  # Faster recovery for testing
        
        async def always_fail():
            raise RateLimitError("Always fails")
        
        # Trigger circuit breaker
        for _ in range(6):
            try:
                await limiter.execute(always_fail)
            except RateLimitError:
                pass
        
        # Circuit should be open
        assert limiter.circuit_breaker.is_open()
        
        # Wait for recovery
        await asyncio.sleep(2.5)
        
        # Should recover
        assert not limiter.circuit_breaker.is_open()


if __name__ == "__main__":
    # Note: Requires mock API to be running
    print("Make sure to start the mock API first:")
    print("python tests/mock_storycorps_api.py")
    pytest.main([__file__, "-v"])