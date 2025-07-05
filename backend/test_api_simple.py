#!/usr/bin/env python3
"""Simple API test using only standard library"""
import urllib.request
import urllib.parse
import json
import time
import ssl

# Create SSL context to handle certificates
ssl_context = ssl.create_default_context()

def test_storycorps_api():
    """Test StoryCorps API with standard library"""
    base_url = "https://archive.storycorps.org/wp-json/storycorps/v1/interviews"
    
    print("=" * 60)
    print("Testing StoryCorps API")
    print("=" * 60)
    
    # Test 1: Basic request
    print("\n1. Testing basic API access...")
    params = urllib.parse.urlencode({"per_page": 2})
    url = f"{base_url}?{params}"
    
    # Create request with headers
    request = urllib.request.Request(url)
    request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    request.add_header('Accept', 'application/json')
    
    try:
        with urllib.request.urlopen(request, context=ssl_context) as response:
            print(f"✓ Status: {response.status}")
            print(f"✓ Headers:")
            for header, value in response.headers.items():
                if 'rate' in header.lower() or 'limit' in header.lower():
                    print(f"  - {header}: {value}")
            
            data = json.loads(response.read().decode())
            print(f"\n✓ Response type: {type(data)}")
            
            if isinstance(data, list):
                print(f"✓ Number of interviews: {len(data)}")
                
                if data:
                    interview = data[0]
                    print(f"\n✓ Interview structure:")
                    for key in interview.keys():
                        print(f"  - {key}")
                    
                    # Save sample
                    with open("sample_api_response.json", "w") as f:
                        json.dump(data, f, indent=2)
                    print("\n✓ Sample saved to sample_api_response.json")
            elif isinstance(data, dict):
                print(f"✓ Response keys: {list(data.keys())}")
                
                if 'data' in data and data['data']:
                    interview = data['data'][0]
                    print(f"\n✓ Interview structure:")
                    for key in interview.keys():
                        print(f"  - {key}")
                    
                    # Save sample
                    with open("sample_api_response.json", "w") as f:
                        json.dump(data, f, indent=2)
                    print("\n✓ Sample saved to sample_api_response.json")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Test 2: Rate limiting behavior
    print("\n2. Testing rate limit behavior (5 quick requests)...")
    for i in range(5):
        try:
            time.sleep(0.5)  # 2 requests per second
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            with urllib.request.urlopen(req, context=ssl_context) as response:
                print(f"  Request {i+1}: Status {response.status}")
        except urllib.error.HTTPError as e:
            print(f"  Request {i+1}: Error {e.code} - {e.reason}")
            if e.code == 429:
                print("  ⚠️  Rate limited!")
                break
    
    print("\n" + "=" * 60)
    print("Test complete! Check sample_api_response.json for data structure")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_storycorps_api()