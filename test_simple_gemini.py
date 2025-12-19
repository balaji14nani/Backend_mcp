#!/usr/bin/env python3
"""
Super Simple Gemini Test
Just test basic API calls to understand rate limits
"""
import os
import time
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_single_request():
    """Test a single simple request"""
    print("\n" + "="*60)
    print("🧪 Test 1: Single Simple Request")
    print("="*60)
    
    try:
        client = genai.Client(api_key=os.getenv("API_KEY"))
        
        print("📤 Sending: 'Hello, what is 2+2?'")
        start = time.time()
        
        response = client.models.generate_content(
            model="models/gemini-2.0-flash-exp",
            contents="Hello, what is 2+2?"
        )
        
        elapsed = time.time() - start
        
        text = response.text if hasattr(response, 'text') else str(response)
        print(f"✅ Success! ({elapsed:.2f}s)")
        print(f"📥 Response: {text[:200]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_rapid_requests(count=5, delay=0):
    """Test multiple rapid requests"""
    print("\n" + "="*60)
    print(f"🧪 Test 2: {count} Rapid Requests (delay={delay}s)")
    print("="*60)
    
    client = genai.Client(api_key=os.getenv("API_KEY"))
    
    success_count = 0
    fail_count = 0
    
    for i in range(count):
        try:
            print(f"\n[{i+1}/{count}] Sending request at {datetime.now().strftime('%H:%M:%S')}")
            
            start = time.time()
            response = client.models.generate_content(
                model="models/gemini-2.0-flash-exp",
                contents=f"What is {i+1} + {i+1}?"
            )
            elapsed = time.time() - start
            
            text = response.text if hasattr(response, 'text') else str(response)
            print(f"  ✅ Success ({elapsed:.2f}s): {text[:50]}")
            success_count += 1
            
            if delay > 0 and i < count - 1:
                print(f"  ⏳ Waiting {delay}s...")
                time.sleep(delay)
                
        except Exception as e:
            error_str = str(e)
            print(f"  ❌ Failed: {error_str[:150]}")
            fail_count += 1
            
            # Check error type
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"  ⚠️  RATE LIMIT HIT!")
                
                # Try to extract wait time
                if "retry" in error_str.lower():
                    print(f"  📋 Full error: {error_str}")
            
            # Wait a bit before next attempt
            if i < count - 1:
                print(f"  ⏳ Waiting 5s before next attempt...")
                time.sleep(5)
    
    print(f"\n📊 Results: {success_count} success, {fail_count} failed")
    return success_count, fail_count

def test_with_increasing_delays():
    """Test with increasing delays to find sweet spot"""
    print("\n" + "="*60)
    print("🧪 Test 3: Finding Optimal Delay")
    print("="*60)
    
    delays = [0, 2, 4, 6, 10]
    
    for delay in delays:
        print(f"\n--- Testing with {delay}s delay ---")
        success, fail = test_rapid_requests(count=3, delay=delay)
        
        if fail == 0:
            print(f"\n✅ {delay}s delay works perfectly!")
            return delay
        
        # Wait before next test
        print("\n⏳ Waiting 30s before next test...")
        time.sleep(30)
    
    return None

def list_available_models():
    """List all available models"""
    print("\n" + "="*60)
    print("📋 Available Models")
    print("="*60)
    
    try:
        client = genai.Client(api_key=os.getenv("API_KEY"))
        
        models = []
        for model in client.models.list():
            models.append(model.name)
            print(f"  ✓ {model.name}")
        
        print(f"\n✅ Found {len(models)} models")
        
        # Check which models exist
        print("\n🔍 Checking specific models:")
        test_models = [
            "models/gemini-2.0-flash-exp",
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-pro"
        ]
        
        for test_model in test_models:
            exists = test_model in models
            status = "✅ EXISTS" if exists else "❌ NOT FOUND"
            print(f"  {status}: {test_model}")
        
        return models
        
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return []

def test_fallback_models():
    """Test different models to see which work"""
    print("\n" + "="*60)
    print("🧪 Test 4: Testing Different Models")
    print("="*60)
    
    client = genai.Client(api_key=os.getenv("API_KEY"))
    
    test_models = [
        "models/gemini-2.0-flash-exp",
        "models/gemini-2.0-flash",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-flash-002",
        "models/gemini-1.5-pro"
    ]
    
    working_models = []
    
    for model in test_models:
        try:
            print(f"\n🔍 Testing: {model}")
            
            response = client.models.generate_content(
                model=model,
                contents="Say 'hello'"
            )
            
            print(f"  ✅ Works!")
            working_models.append(model)
            
            time.sleep(3)  # Small delay between tests
            
        except Exception as e:
            error_str = str(e)
            if "404" in error_str or "NOT_FOUND" in error_str:
                print(f"  ❌ Model not found (404)")
            elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"  ⚠️  Rate limited (model exists but quota hit)")
                working_models.append(model)  # Model exists, just rate limited
            else:
                print(f"  ❌ Error: {error_str[:100]}")
    
    print(f"\n✅ Working models: {working_models}")
    return working_models

def main():
    """Run all tests"""
    import sys
    
    print("🚀 Simple Gemini API Test Suite")
    print("="*60)
    
    # Check API key
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("❌ No API_KEY found in .env file!")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-5:]}")
    
    if len(sys.argv) > 1:
        test = sys.argv[1]
        
        if test == "single":
            test_single_request()
        elif test == "rapid":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            delay = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            test_rapid_requests(count, delay)
        elif test == "models":
            list_available_models()
        elif test == "fallback":
            test_fallback_models()
        elif test == "delay":
            test_with_increasing_delays()
        else:
            print("Usage: python test_simple_gemini.py [single|rapid|models|fallback|delay]")
    else:
        # Run basic tests
        print("\n🎯 Running basic tests...\n")
        
        # Test 1: List models
        models = list_available_models()
        
        time.sleep(2)
        
        # Test 2: Single request
        if test_single_request():
            time.sleep(3)
            
            # Test 3: Rapid requests with 4s delay
            print("\n⏳ Waiting 5s before rapid test...")
            time.sleep(5)
            test_rapid_requests(count=3, delay=4)

if __name__ == "__main__":
    main()
