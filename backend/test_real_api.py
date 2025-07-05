#!/usr/bin/env python3
"""
Test rate limiter against real StoryCorps API
CAUTION: This hits the real API - use responsibly!
"""
import asyncio
import httpx
import sys
import os
import time
from datetime import datetime
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rate_limiting import AdaptiveRateLimiter, RateLimitError

# StoryCorps API endpoints discovered
BASE_URL = "https://archive.storycorps.org"
INTERVIEWS_ENDPOINT = "/wp-json/storycorps/v1/interviews"

class StoryCorpsAPITester:
    def __init__(self):
        self.limiter = AdaptiveRateLimiter(
            base_rate=5,      # Start very conservative
            max_rate=50,      # Allow scaling up
            min_rate=1,       # Never go below 1 req/s
            increase_factor=1.05,  # Increase slowly (5% at a time)
            decrease_factor=0.3    # Back off aggressively (70% reduction)
        )
        self.stats = {
            "successful": 0,
            "rate_limited": 0,
            "errors": 0,
            "start_time": None,
            "discovered_limits": []
        }
    
    async def test_single_request(self):
        """Test a single request to verify API access"""
        print("Testing single request to StoryCorps API...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{BASE_URL}{INTERVIEWS_ENDPOINT}",
                    params={"per_page": 1},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✓ API accessible! Found {len(data.get('data', []))} interviews")
                    print(f"✓ Response headers: {dict(response.headers)}")
                    return True
                else:
                    print(f"✗ API returned status {response.status_code}")
                    print(f"  Response: {response.text[:200]}")
                    return False
                    
            except Exception as e:
                print(f"✗ Error accessing API: {e}")
                return False
    
    async def fetch_interviews(self, client: httpx.AsyncClient, page: int = 1):
        """Fetch interviews with rate limiting"""
        response = await client.get(
            f"{BASE_URL}{INTERVIEWS_ENDPOINT}",
            params={"per_page": 10, "page": page},
            timeout=10.0,
            headers={
                "User-Agent": "MosaicProject/1.0 (Research; Finding human connections)"
            }
        )
        
        # Check for rate limiting
        if response.status_code == 429:
            # Log rate limit headers if available
            headers = response.headers
            print(f"\n⚠️  Rate limited at {self.limiter.current_rate:.1f} req/s")
            if "x-ratelimit-limit" in headers:
                print(f"  API limit: {headers['x-ratelimit-limit']}")
            if "x-ratelimit-reset" in headers:
                print(f"  Reset at: {headers['x-ratelimit-reset']}")
            
            raise RateLimitError("429 Too Many Requests")
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}")
        
        return response.json()
    
    async def discover_rate_limit(self, duration_seconds: int = 60):
        """Gradually increase request rate to find API limits"""
        print(f"\nDiscovering rate limits (running for {duration_seconds} seconds)...")
        print("Starting at 5 req/s and scaling up gradually...")
        print("-" * 60)
        
        self.stats["start_time"] = time.time()
        
        async with httpx.AsyncClient() as client:
            page = 1
            last_report_time = time.time()
            
            while time.time() - self.stats["start_time"] < duration_seconds:
                try:
                    # Execute request with rate limiting
                    await self.limiter.execute(
                        self.fetch_interviews,
                        client,
                        page
                    )
                    
                    self.stats["successful"] += 1
                    page += 1
                    
                    # Report progress every 5 seconds
                    if time.time() - last_report_time >= 5:
                        self._print_progress()
                        last_report_time = time.time()
                    
                except RateLimitError:
                    self.stats["rate_limited"] += 1
                    self.stats["discovered_limits"].append({
                        "rate": self.limiter.current_rate,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    self.stats["errors"] += 1
                    print(f"\n✗ Error: {e}")
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.001)
        
        self._print_final_report()
    
    def _print_progress(self):
        """Print current progress"""
        elapsed = time.time() - self.stats["start_time"]
        rate = self.stats["successful"] / elapsed if elapsed > 0 else 0
        
        print(f"\r[{int(elapsed)}s] "
              f"Rate: {self.limiter.current_rate:.1f} req/s | "
              f"Success: {self.stats['successful']} | "
              f"Limited: {self.stats['rate_limited']} | "
              f"Errors: {self.stats['errors']} | "
              f"Avg: {rate:.1f} req/s", end="", flush=True)
    
    def _print_final_report(self):
        """Print final test report"""
        print("\n\n" + "=" * 60)
        print("RATE LIMIT DISCOVERY REPORT")
        print("=" * 60)
        
        elapsed = time.time() - self.stats["start_time"]
        avg_rate = self.stats["successful"] / elapsed if elapsed > 0 else 0
        
        print(f"\nTest Duration: {elapsed:.1f} seconds")
        print(f"Successful Requests: {self.stats['successful']}")
        print(f"Rate Limited: {self.stats['rate_limited']}")
        print(f"Other Errors: {self.stats['errors']}")
        print(f"Average Success Rate: {avg_rate:.1f} req/s")
        print(f"Final Rate Setting: {self.limiter.current_rate:.1f} req/s")
        
        if self.stats["discovered_limits"]:
            print(f"\nRate Limits Hit:")
            for limit in self.stats["discovered_limits"][-5:]:  # Show last 5
                print(f"  - {limit['rate']:.1f} req/s at {limit['timestamp']}")
        
        # Save results
        results = {
            "test_time": datetime.now().isoformat(),
            "duration_seconds": elapsed,
            "stats": self.stats,
            "final_rate": self.limiter.current_rate,
            "limiter_stats": self.limiter.get_stats()
        }
        
        with open("rate_limit_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to rate_limit_test_results.json")
        
        # Recommendations
        print("\n" + "-" * 60)
        print("RECOMMENDATIONS:")
        if self.stats["rate_limited"] == 0:
            print(f"✓ No rate limits hit! Can safely use up to {self.limiter.current_rate:.1f} req/s")
        else:
            safe_rate = self.limiter.current_rate * 0.8
            print(f"✓ Suggested safe rate: {safe_rate:.1f} req/s (80% of discovered limit)")
        
        print("-" * 60)

async def main():
    """Run the API tests"""
    print("=" * 60)
    print("StoryCorps API Rate Limit Tester")
    print("=" * 60)
    print("\n⚠️  This will make real requests to StoryCorps API")
    print("⚠️  Please use responsibly!\n")
    
    tester = StoryCorpsAPITester()
    
    # First, test single request
    if not await tester.test_single_request():
        print("\n✗ Could not access API. Please check your connection.")
        return 1
    
    # Ask for confirmation before rate testing
    print("\nReady to test rate limits?")
    print("This will gradually increase request rate from 5 to 50 req/s")
    response = input("Continue? (y/n): ")
    
    if response.lower() != 'y':
        print("Test cancelled.")
        return 0
    
    # Run rate limit discovery
    try:
        await tester.discover_rate_limit(duration_seconds=60)
        return 0
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        tester._print_final_report()
        return 0
    except Exception as e:
        print(f"\n\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)