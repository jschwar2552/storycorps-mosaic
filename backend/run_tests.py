#!/usr/bin/env python3
"""Test runner for Mosaic backend"""
import subprocess
import sys

def run_tests():
    """Run pytest with appropriate settings"""
    cmd = [
        "pytest",
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
        "tests/test_rate_limiter.py"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())