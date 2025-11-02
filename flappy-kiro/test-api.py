#!/usr/bin/env python3
"""
Simple API test script for Flappy Kiro backend
"""

import requests
import json
import time

API_BASE = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_submit_score():
    """Test score submission"""
    test_score = {
        "username": "testplayer",
        "score": 42,
        "difficulty": "medium"
    }
    
    try:
        response = requests.post(f"{API_BASE}/scores", json=test_score)
        print(f"Score submission: {response.status_code} - {response.json()}")
        return response.status_code == 201
    except Exception as e:
        print(f"Score submission failed: {e}")
        return False

def test_leaderboard():
    """Test leaderboard retrieval"""
    try:
        response = requests.get(f"{API_BASE}/leaderboard")
        data = response.json()
        print(f"Leaderboard: {response.status_code} - {len(data)} entries")
        return response.status_code == 200
    except Exception as e:
        print(f"Leaderboard test failed: {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    try:
        response = requests.get(f"{API_BASE}/stats")
        print(f"Stats: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Stats test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Flappy Kiro API...")
    print("Make sure the backend is running on localhost:5000")
    print("-" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Submit Score", test_submit_score),
        ("Get Leaderboard", test_leaderboard),
        ("Get Stats", test_stats)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        if test_func():
            print(f"✅ {test_name} passed")
            passed += 1
        else:
            print(f"❌ {test_name} failed")
        time.sleep(1)
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the backend logs.")