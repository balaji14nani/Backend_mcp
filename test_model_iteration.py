#!/usr/bin/env python3
"""
Test Model Iteration
Quick test to see the new model iteration functionality
"""
import requests
import json
import time

def test_model_iteration():
    """Test the model iteration by sending a request to the server"""
    
    # Start the server in background (you need to run this manually)
    print("🧪 Testing Model Iteration")
    print("="*50)
    print("Make sure to start the server first:")
    print("  python test.py")
    print("="*50)
    
    # Test message
    test_message = {
        "text": "What could be the cytotoxicity for particle size 10 nm with dose 50 µg/mL?"
    }
    
    try:
        print(f"\n📤 Sending test message...")
        print(f"Message: {test_message['text']}")
        
        response = requests.post(
            "http://localhost:8000/message",
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ SUCCESS!")
            print(f"Response: {result.get('text', 'No text')[:200]}...")
            print(f"Tool calls: {len(result.get('tool_calls', []))}")
            print(f"Iterations: {result.get('iterations', 0)}")
            
            # Show tool call results
            for i, tool_call in enumerate(result.get('tool_calls', []), 1):
                print(f"\nTool Call {i}:")
                print(f"  Function: {tool_call['function']}")
                print(f"  Result: {tool_call['result'].get('class_label', 'N/A')}")
                if 'confidence' in tool_call['result']:
                    print(f"  Confidence: {tool_call['result']['confidence']:.3f}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the server is running:")
        print("  python test.py")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Health check passed!")
            print(f"Status: {result.get('status')}")
            print(f"Models loaded: {result.get('models_loaded')}")
            print(f"Tools available: {len(result.get('tools_available', []))}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except:
        print("❌ Server not running")
        return False

if __name__ == "__main__":
    print("🚀 Model Iteration Test")
    
    # Test health first
    if test_health_check():
        print("\n" + "="*50)
        test_model_iteration()
    else:
        print("\n💡 Start the server first:")
        print("  python test.py")