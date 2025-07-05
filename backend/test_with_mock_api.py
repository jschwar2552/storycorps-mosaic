#!/usr/bin/env python3
"""Test rate limiter against mock StoryCorps API"""
import asyncio
import httpx
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rate_limiting import AdaptiveRateLimiter, RateLimitError

async def test_api_rate_discovery():
    """Test discovering the API's rate limit"""
    print("Testing rate limit discovery against mock API...")
    print("(Make sure mock API is running on port 8001)")
    
    limiter = AdaptiveRateLimiter(base_rate=20, max_rate=50)
    
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        async def fetch_stories():
            response = await client.get("/wp-json/storycorps/v1/interviews")
            if response.status_code == 429:
                raise RateLimitError("Rate limited")
            return response.json()
        
        # Track statistics
        successful = 0
        rate_limited = 0
        
        print("\nRunning for 10 seconds to find optimal rate...")
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < 10:
            try:
                await limiter.execute(fetch_stories)
                successful += 1
                
                # Print progress every second
                elapsed = asyncio.get_event_loop().time() - start_time
                if int(elapsed) > int(elapsed - 0.01):
                    print(f"  {int(elapsed)}s: Rate={limiter.current_rate:.1f} req/s, Success={successful}, Limited={rate_limited}")
                    
            except RateLimitError:
                rate_limited += 1
            
            await asyncio.sleep(0.001)
        
        duration = asyncio.get_event_loop().time() - start_time
        avg_rate = successful / duration
        
        print(f"\nResults after {duration:.1f} seconds:")
        print(f"  ✓ Discovered rate limit: ~{limiter.current_rate:.1f} req/s")
        print(f"  ✓ Average successful rate: {avg_rate:.1f} req/s")
        print(f"  ✓ Successful requests: {successful}")
        print(f"  ✓ Rate limited requests: {rate_limited}")
        print(f"  ✓ Success ratio: {successful/(successful+rate_limited)*100:.1f}%")
        
        # Should stabilize around 30 req/s (mock API limit)
        assert 25 <= limiter.current_rate <= 35, f"Rate should be ~30, got {limiter.current_rate}"
        print("\n✅ Rate limiter successfully adapted to API limit!")

async def test_burst_handling():
    """Test handling burst requests"""
    print("\nTesting burst request handling...")
    
    limiter = AdaptiveRateLimiter()
    limiter.current_rate = 30  # Set to known limit
    
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        async def fetch_story(story_id):
            response = await client.get(f"/wp-json/storycorps/v1/interviews/{story_id}")
            if response.status_code == 429:
                raise RateLimitError("Rate limited")
            return response.json()
        
        print("Sending burst of 50 requests...")
        tasks = []
        for i in range(50):
            task = limiter.execute(fetch_story, f"story_{i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        rate_limited = sum(1 for r in results if isinstance(r, RateLimitError))
        
        print(f"  ✓ Successful: {successful}")
        print(f"  ✓ Rate limited: {rate_limited}")
        print(f"  ✓ Current rate: {limiter.current_rate:.1f} req/s")
        
        assert successful >= 20, "Should handle some burst requests"
        assert rate_limited > 0, "Should hit rate limit on burst"
        
        print("\n✅ Burst handling works correctly!")

async def main():
    """Run all API tests"""
    print("=" * 60)
    print("Mosaic Rate Limiter - Mock API Integration Tests")
    print("=" * 60)
    
    try:
        # Check if mock API is running
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8001/api/stats")
                stats = response.json()
                print(f"\n✓ Mock API running with rate limit: {stats['rate_limit']} req/s")
            except:
                print("\n❌ Error: Mock API not running!")
                print("Please start it with: python tests/mock_storycorps_api.py")
                return 1
        
        # Run tests
        await test_api_rate_discovery()
        await test_burst_handling()
        
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)