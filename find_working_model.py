#!/usr/bin/env python3
"""
Find Working Gemini Model
Test different models to find one with available quota
"""
import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_model(client, model_name, test_prompt="Hello, what is 2+2?"):
    """Test a single model"""
    try:
        print(f"🔍 Testing: {model_name}")
        
        start = time.time()
        response = client.models.generate_content(
            model=model_name,
            contents=test_prompt
        )
        elapsed = time.time() - start
        
        # Get response text
        text = ""
        if hasattr(response, 'text'):
            text = response.text
        elif hasattr(response, 'candidates'):
            for candidate in response.candidates:
                if hasattr(candidate, 'content'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            text += part.text
        
        print(f"  ✅ SUCCESS ({elapsed:.2f}s): {text[:100]}")
        return True, text
        
    except Exception as e:
        error_str = str(e)
        
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            if "limit: 0" in error_str:
                print(f"  ❌ QUOTA EXHAUSTED (no quota left)")
            else:
                print(f"  ⚠️  RATE LIMITED (has quota, just too fast)")
            return False, "rate_limited"
        elif "404" in error_str or "NOT_FOUND" in error_str:
            print(f"  ❌ MODEL NOT FOUND")
            return False, "not_found"
        else:
            print(f"  ❌ OTHER ERROR: {error_str[:100]}")
            return False, "other_error"

def find_working_models():
    """Find models that currently work"""
    
    client = genai.Client(api_key=os.getenv("API_KEY"))
    
    # Priority order - try these first
    priority_models = [
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro", 
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-001",
        "models/gemini-flash-latest",
        "models/gemini-pro-latest",
        "models/gemini-2.5-flash-lite",
        "models/gemini-2.0-flash-lite",
        "models/gemma-3-1b-it",
        "models/gemma-3-4b-it"
    ]
    
    working_models = []
    rate_limited_models = []
    
    print("\n" + "="*60)
    print("🔍 Finding Working Models")
    print("="*60)
    
    for model in priority_models:
        success, result = test_model(client, model)
        
        if success:
            working_models.append(model)
            print(f"  🎉 FOUND WORKING MODEL: {model}")
            break  # Found one that works, stop here
        elif result == "rate_limited":
            rate_limited_models.append(model)
        
        # Small delay between tests
        time.sleep(2)
    
    print(f"\n📊 Results:")
    print(f"  ✅ Working models: {working_models}")
    print(f"  ⚠️  Rate limited (have quota): {rate_limited_models}")
    
    return working_models, rate_limited_models

def test_working_model_conversation():
    """Test a conversation with a working model"""
    
    working_models, rate_limited = find_working_models()
    
    if not working_models and not rate_limited:
        print("\n❌ No working models found!")
        return None
    
    # Use working model, or rate limited one (might work after delay)
    model_to_use = working_models[0] if working_models else rate_limited[0]
    
    print(f"\n" + "="*60)
    print(f"💬 Testing Conversation with: {model_to_use}")
    print("="*60)
    
    client = genai.Client(api_key=os.getenv("API_KEY"))
    
    test_questions = [
        "What could be the cytotoxicity for particle size 10 nm?",
        "Explain carbon dot toxicity in simple terms",
        "What factors affect nanoparticle toxicity?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[Q{i}] {question}")
        print("-" * 50)
        
        success, response = test_model(client, model_to_use, question)
        
        if success:
            print(f"[A{i}] {response}")
        else:
            print(f"[A{i}] ❌ Failed: {response}")
            
            if response == "rate_limited":
                print("⏳ Waiting 60s for quota reset...")
                time.sleep(60)
                # Try once more
                success, response = test_model(client, model_to_use, question)
                if success:
                    print(f"[A{i}] (Retry) {response}")
        
        # Delay between questions
        if i < len(test_questions):
            print("\n⏳ Waiting 10s before next question...")
            time.sleep(10)
    
    return model_to_use

def main():
    """Main function"""
    import sys
    
    print("🚀 Find Working Gemini Model")
    print("="*60)
    
    # Check API key
    if not os.getenv("API_KEY"):
        print("❌ No API_KEY found!")
        return
    
    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        # Test conversation
        working_model = test_working_model_conversation()
        if working_model:
            print(f"\n✅ Use this model: {working_model}")
    else:
        # Just find working models
        working, rate_limited = find_working_models()
        
        if working:
            print(f"\n🎉 SUCCESS! Use this model: {working[0]}")
            
            # Test it with a toxicity question
            print(f"\n🧪 Testing with toxicity question...")
            client = genai.Client(api_key=os.getenv("API_KEY"))
            success, response = test_model(
                client, 
                working[0], 
                "What could be the cytotoxicity for particle size 10 nm?"
            )
            
            if success:
                print(f"\n✅ Toxicity response: {response}")
            
        elif rate_limited:
            print(f"\n⚠️  Models have quota but are rate limited. Try: {rate_limited[0]}")
            print("💡 Wait 1-2 minutes and try again")
        else:
            print(f"\n❌ No working models found. Check your quota at: https://ai.dev/usage")

if __name__ == "__main__":
    main()