#!/usr/bin/env python3
"""Quick test to verify Claude API integration works"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(__file__))

# Check for API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ ANTHROPIC_API_KEY environment variable not set")
    print("\nPlease set it before running this test")
    sys.exit(1)

print(f"✅ Found API key: {api_key[:10]}...")

# Quick test of Claude integration
try:
    from anthropic import AsyncAnthropic
    print("✅ Anthropic module available")
except ImportError:
    print("❌ Anthropic module not installed")
    print("Run: pip install anthropic")
    sys.exit(1)

async def quick_claude_test():
    """Quick test of Claude API"""
    client = AsyncAnthropic(api_key=api_key)
    
    try:
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Say 'Mosaic test successful!' and nothing else."
            }]
        )
        
        result = response.content[0].text
        print(f"\n🤖 Claude says: {result}")
        print("\n✅ API integration working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error calling Claude API: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_claude_test())
    sys.exit(0 if success else 1)