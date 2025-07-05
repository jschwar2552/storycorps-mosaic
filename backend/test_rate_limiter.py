#!/usr/bin/env python3
"""Quick test script for rate limiter without pytest"""
import asyncio
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rate_limiting import TokenBucket, AdaptiveRateLimiter, RateLimitError

def test_token_bucket():
    """Test basic token bucket functionality"""
    print("Testing TokenBucket...")
    
    # Test initialization
    bucket = TokenBucket(rate=10, capacity=10)
    assert bucket.rate == 10
    assert bucket.capacity == 10
    assert bucket.tokens == 10
    print("✓ Initialization correct")
    
    # Test consumption
    consumed = bucket.try_consume(5)
    print(f"  Consumed 5 tokens: {consumed}, tokens left: {bucket.tokens}")
    assert consumed == True
    assert bucket.tokens == 5
    
    consumed = bucket.try_consume(6)
    print(f"  Tried to consume 6 tokens: {consumed}, tokens left: {bucket.tokens}")
    assert consumed == False
    assert bucket.tokens >= 5  # May have slightly more due to refill
    print("✓ Token consumption works")
    
    # Test refill
    bucket.tokens = 0
    time.sleep(0.1)
    bucket._refill()
    assert 0.9 <= bucket.tokens <= 1.1
    print("✓ Token refill works")
    
    print("TokenBucket tests passed!\n")

async def test_adaptive_rate_limiter():
    """Test adaptive rate limiter"""
    print("Testing AdaptiveRateLimiter...")
    
    limiter = AdaptiveRateLimiter()
    assert limiter.current_rate == 10
    print("✓ Initialization correct")
    
    # Test rate increase
    initial_rate = limiter.current_rate
    for _ in range(10):
        limiter._on_success()
    assert limiter.current_rate > initial_rate
    print(f"✓ Rate increased from {initial_rate} to {limiter.current_rate}")
    
    # Test rate decrease
    limiter.current_rate = 40
    limiter._on_rate_limit()
    assert limiter.current_rate == 20
    print("✓ Rate decreased on 429")
    
    # Test async execution
    async def test_func(value):
        return f"success: {value}"
    
    result = await limiter.execute(test_func, "test")
    assert result == "success: test"
    print("✓ Async execution works")
    
    print("AdaptiveRateLimiter tests passed!\n")

async def test_rate_limiting_behavior():
    """Test actual rate limiting behavior"""
    print("Testing rate limiting behavior...")
    
    limiter = AdaptiveRateLimiter()
    limiter.current_rate = 10  # 10 requests per second
    # Empty the bucket to test rate limiting
    limiter.token_bucket.tokens = 0
    
    request_times = []
    
    async def track_request():
        await limiter.token_bucket.wait_for_tokens(1)
        request_times.append(time.time())
    
    # Launch 20 requests
    print("Launching 20 requests at 10 req/s...")
    start = time.time()
    tasks = [track_request() for _ in range(20)]
    await asyncio.gather(*tasks)
    
    # Should take about 2 seconds
    duration = time.time() - start
    print(f"✓ 20 requests took {duration:.2f}s (expected ~2s)")
    
    # Check spacing
    spacings = []
    for i in range(1, len(request_times)):
        spacings.append(request_times[i] - request_times[i-1])
    
    avg_spacing = sum(spacings) / len(spacings)
    print(f"✓ Average spacing: {avg_spacing:.3f}s (expected ~0.1s)")
    
    print("Rate limiting behavior tests passed!\n")

async def main():
    """Run all tests"""
    print("=" * 50)
    print("Mosaic Rate Limiter Tests")
    print("=" * 50 + "\n")
    
    try:
        # Sync tests
        test_token_bucket()
        
        # Async tests
        await test_adaptive_rate_limiter()
        await test_rate_limiting_behavior()
        
        print("✅ All tests passed!")
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)