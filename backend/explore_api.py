#!/usr/bin/env python3
"""
Explore StoryCorps API structure and data format
This script makes minimal requests to understand the API
"""
import asyncio
import httpx
import json
from datetime import datetime
import time

BASE_URL = "https://archive.storycorps.org"

async def explore_api_structure():
    """Explore API endpoints and data structure with minimal requests"""
    
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("StoryCorps API Explorer")
        print("=" * 60)
        
        # Test 1: Basic endpoint
        print("\n1. Testing interviews endpoint...")
        await asyncio.sleep(1)  # Be polite
        
        response = await client.get(
            f"{BASE_URL}/wp-json/storycorps/v1/interviews",
            params={"per_page": 2},
            timeout=15.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Response structure:")
            print(f"  - Type: {type(data)}")
            print(f"  - Keys: {list(data.keys()) if isinstance(data, dict) else 'List response'}")
            
            if isinstance(data, dict) and 'data' in data:
                interviews = data['data']
                if interviews:
                    print(f"\n  Sample interview structure:")
                    sample = interviews[0]
                    for key, value in sample.items():
                        value_type = type(value).__name__
                        if isinstance(value, (list, dict)):
                            print(f"    - {key}: {value_type} with {len(value)} items")
                        elif isinstance(value, str) and len(value) > 50:
                            print(f"    - {key}: {value_type} ({len(value)} chars)")
                        else:
                            print(f"    - {key}: {value}")
            
            # Save sample data
            with open("sample_interview_data.json", "w") as f:
                json.dump(data, f, indent=2)
            print("\n✓ Sample data saved to sample_interview_data.json")
        else:
            print(f"✗ Error: Status {response.status_code}")
            print(f"  Response: {response.text[:500]}")
        
        # Test 2: Search functionality
        print("\n2. Testing search endpoint...")
        await asyncio.sleep(2)  # Wait 2 seconds between requests
        
        search_url = f"{BASE_URL}/wp-json/storycorps/v1/search"
        response = await client.get(
            search_url,
            params={"q": "family", "limit": 2},
            timeout=15.0
        )
        
        if response.status_code == 200:
            print("✓ Search endpoint works!")
            search_data = response.json()
            print(f"  - Response keys: {list(search_data.keys()) if isinstance(search_data, dict) else 'List'}")
        else:
            print(f"✗ Search endpoint returned: {response.status_code}")
        
        # Test 3: Check for rate limit headers
        print("\n3. Checking response headers...")
        if response.headers:
            print("  Headers received:")
            for header, value in response.headers.items():
                if 'limit' in header.lower() or 'rate' in header.lower():
                    print(f"    - {header}: {value}")
        
        # Test 4: Alternative API endpoint
        print("\n4. Testing alternative API endpoint...")
        await asyncio.sleep(2)
        
        alt_url = "https://api.storycorps.me/wp-json/interviews"
        try:
            response = await client.get(alt_url, timeout=15.0)
            if response.status_code == 200:
                print("✓ Alternative API endpoint works!")
                alt_data = response.json()
                print(f"  - Response type: {type(alt_data)}")
                if isinstance(alt_data, list) and alt_data:
                    print(f"  - Number of interviews: {len(alt_data)}")
            else:
                print(f"✗ Alternative API returned: {response.status_code}")
        except Exception as e:
            print(f"✗ Could not access alternative API: {e}")
        
        # Test 5: Check robots.txt
        print("\n5. Checking robots.txt...")
        await asyncio.sleep(1)
        
        robots_response = await client.get(f"{BASE_URL}/robots.txt")
        if robots_response.status_code == 200:
            print("✓ robots.txt found:")
            lines = robots_response.text.split('\n')[:10]
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        
        print("\n" + "=" * 60)
        print("Exploration complete!")
        print("=" * 60)

async def test_pagination():
    """Test pagination parameters"""
    print("\nTesting pagination...")
    
    async with httpx.AsyncClient() as client:
        # Test different page sizes
        for page_size in [1, 10, 50]:
            await asyncio.sleep(2)
            response = await client.get(
                f"{BASE_URL}/wp-json/storycorps/v1/interviews",
                params={"per_page": page_size},
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                actual_size = len(data.get('data', []))
                print(f"  ✓ Requested {page_size}, got {actual_size} interviews")
                
                # Check for pagination metadata
                if 'meta' in data:
                    meta = data['meta']
                    print(f"    Meta: {meta}")
            else:
                print(f"  ✗ Failed with page_size={page_size}: {response.status_code}")

async def main():
    """Run all exploration tests"""
    try:
        await explore_api_structure()
        await test_pagination()
        
        print("\n📋 Next Steps:")
        print("1. Review sample_interview_data.json for data structure")
        print("2. Run test_real_api.py to find rate limits")
        print("3. Build data collection pipeline based on findings")
        
    except Exception as e:
        print(f"\n✗ Error during exploration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)