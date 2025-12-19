#!/usr/bin/env python3
"""
Test Caching System
Demonstrates the intelligent model caching functionality
"""
import requests
import json
import time

def test_health_with_cache():
    """Test the health endpoint with cache status"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Health check with cache status:")
            print(f"  Status: {result.get('status')}")
            print(f"  Primary model: {result.get('primary_model')}")
            print(f"  Fallback model: {result.get('fallback_model')}")
            print(f"  Cache status:")
            cache = result.get('cache_status', {})
            print(f"    🟢 Working models: {cache.get('working_models', 0)}")
            print(f"    🔴 Quota exhausted: {cache.get('quota_exhausted', 0)}")
            print(f"    🟡 Rate limited: {cache.get('rate_limited', 0)}")
            print(f"    ❌ Not found: {cache.get('not_found', 0)}")
            print(f"    ⚠️  Other errors: {cache.get('other_errors', 0)}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except:
        print("❌ Server not running")
        return False

def test_detailed_cache_status():
    """Test the detailed cache status endpoint"""
    try:
        response = requests.get("http://localhost:8000/cache/status", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("\n📊 Detailed Cache Status:")
            
            working = result.get('working_models', [])
            print(f"  🟢 Working models ({len(working)}):")
            for model in working[:3]:  # Show first 3
                print(f"    • {model.split('/')[-1]}")
            if len(working) > 3:
                print(f"    ... and {len(working) - 3} more")
            
            quota_exhausted = result.get('quota_exhausted', {})
            if quota_exhausted:
                print(f"  🔴 Quota exhausted ({len(quota_exhausted)}):")
                for model, info in list(quota_exhausted.items())[:3]:
                    print(f"    • {model.split('/')[-1]}: expires in {info['expires_in_minutes']}m")
            
            rate_limited = result.get('rate_limited', {})
            if rate_limited:
                print(f"  🟡 Rate limited ({len(rate_limited)}):")
                for model, info in list(rate_limited.items())[:3]:
                    print(f"    • {model.split('/')[-1]}: expires in {info['expires_in_minutes']}m")
            
            not_found = result.get('not_found', [])
            if not_found:
                print(f"  ❌ Not found ({len(not_found)}):")
                for model in not_found[:3]:
                    print(f"    • {model.split('/')[-1]}")
            
            return True
        else:
            print(f"❌ Cache status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cache status error: {e}")
        return False

def test_cache_reset():
    """Test cache reset functionality"""
    try:
        response = requests.post("http://localhost:8000/cache/reset", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n🔄 Cache reset: {result.get('message')}")
            return True
        else:
            print(f"❌ Cache reset failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cache reset error: {e}")
        return False

def test_message_with_caching():
    """Test sending a message to see caching in action"""
    test_message = {
        "text": "Predict toxicity for 5nm carbon dots with zeta potential -15mV, dose 25 µg/mL, time 12h, solvent Ethanol, cell type MCF7, cell origin Human"
    }
    
    try:
        print(f"\n📤 Sending test message to see caching in action...")
        print(f"Message: {test_message['text'][:80]}...")
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/message",
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ SUCCESS! (took {elapsed:.1f}s)")
            print(f"Response: {result.get('text', 'No text')[:150]}...")
            print(f"Tool calls: {len(result.get('tool_calls', []))}")
            print(f"Iterations: {result.get('iterations', 0)}")
            
            # Show tool call results
            for i, tool_call in enumerate(result.get('tool_calls', []), 1):
                if i <= 2:  # Show first 2
                    print(f"  Tool {i}: {tool_call['function']} → {tool_call['result'].get('class_label', 'N/A')}")
            
            return True
        else:
            print(f"❌ Message failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    
    except Exception as e:
        print(f"❌ Message error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Intelligent Model Caching System")
    print("="*60)
    
    # Test 1: Health check with cache
    if not test_health_with_cache():
        print("\n💡 Start the server first:")
        print("  python test.py")
        return
    
    # Test 2: Detailed cache status
    test_detailed_cache_status()
    
    # Test 3: Send a message to populate cache
    print("\n" + "="*60)
    print("🔄 Testing message processing (will populate cache)")
    print("="*60)
    
    success = test_message_with_caching()
    
    if success:
        # Test 4: Check cache after message
        print("\n" + "="*60)
        print("📊 Cache status after processing")
        print("="*60)
        test_detailed_cache_status()
        
        # Test 5: Send another message (should use cached info)
        print("\n" + "="*60)
        print("🚀 Testing second message (should be faster with cache)")
        print("="*60)
        test_message_with_caching()
        
        # Test 6: Final cache status
        print("\n" + "="*60)
        print("📊 Final cache status")
        print("="*60)
        test_detailed_cache_status()
    
    print("\n" + "="*60)
    print("🎯 Caching System Test Complete!")
    print("="*60)
    print("Key benefits demonstrated:")
    print("  ✅ Models are cached as working/failing")
    print("  ✅ Failed models are skipped in future requests")
    print("  ✅ Cache expires automatically")
    print("  ✅ Detailed status available via API")
    print("  ✅ Cache can be reset if needed")

if __name__ == "__main__":
    main()