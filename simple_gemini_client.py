#!/usr/bin/env python3
"""
Simple Gemini API Client with Rate Limiting
Standalone script to call Gemini API with proper rate limiting and error handling
"""
import os
import time
import json
from datetime import datetime
from google import genai
from dotenv import load_dotenv
from collections import deque

# Load environment variables
load_dotenv()

class GeminiClient:
    def __init__(self, api_key=None):
        """Initialize Gemini client with rate limiting"""
        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY not found in environment variables")
        
        self.client = genai.Client(api_key=self.api_key)
        
        # Rate limiting - Conservative approach
        self.request_times = deque(maxlen=15)  # Track last 15 requests
        self.min_interval = 4.0  # 4 seconds between requests (15 req/min)
        
        # Available models (will be discovered)
        self.available_models = []
        self.primary_model = None
        self.fallback_models = []
        
        # Discover models on init
        self._discover_models()
    
    def _discover_models(self):
        """Discover available Gemini models"""
        try:
            print("🔍 Discovering available Gemini models...")
            
            for model in self.client.models.list():
                model_name = model.name
                display_name = model_name.split("/")[-1]
                
                self.available_models.append({
                    "full_name": model_name,
                    "display_name": display_name
                })
                print(f"  ✓ {display_name}")
            
            # Set primary and fallback models
            self._set_preferred_models()
            
            print(f"\n✓ Primary model: {self.primary_model.split('/')[-1] if self.primary_model else 'None'}")
            print(f"✓ Fallback models: {[m.split('/')[-1] for m in self.fallback_models]}")
            
        except Exception as e:
            print(f"⚠️  Could not discover models: {e}")
            # Use default models
            self.primary_model = "models/gemini-2.0-flash-exp"
            self.fallback_models = ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]
    
    def _set_preferred_models(self):
        """Set preferred models based on availability"""
        model_names = [m["full_name"] for m in self.available_models]
        
        # Priority order for primary model
        primary_preferences = [
            "models/gemini-2.0-flash-exp",
            "models/gemini-2.0-flash", 
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro"
        ]
        
        # Find primary model
        for pref in primary_preferences:
            if pref in model_names:
                self.primary_model = pref
                break
        
        # Set fallback models (exclude primary)
        fallback_preferences = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro", 
            "models/gemini-2.0-flash",
            "models/gemini-pro"
        ]
        
        for pref in fallback_preferences:
            if pref in model_names and pref != self.primary_model:
                self.fallback_models.append(pref)
        
        # If no primary found, use first available
        if not self.primary_model and self.available_models:
            self.primary_model = self.available_models[0]["full_name"]
    
    def _rate_limit(self):
        """Apply rate limiting before making requests"""
        now = time.time()
        
        # Remove old requests (older than 1 minute)
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()
        
        # Check if we need to wait
        if self.request_times:
            time_since_last = now - self.request_times[-1]
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                print(f"⏳ Rate limiting: Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
        
        # Record this request
        self.request_times.append(time.time())
    
    def _is_rate_limit_error(self, error_str):
        """Check if error is rate limit related"""
        rate_limit_indicators = [
            "429", "RESOURCE_EXHAUSTED", "quota", "rate limit", 
            "too many requests", "exceeded"
        ]
        return any(indicator in error_str.lower() for indicator in rate_limit_indicators)
    
    def _is_model_not_found(self, error_str):
        """Check if error is model not found"""
        not_found_indicators = ["404", "NOT_FOUND", "not found", "is not found"]
        return any(indicator in error_str.lower() for indicator in not_found_indicators)
    
    def generate_content(self, prompt, model=None, max_retries=3, temperature=0.7):
        """
        Generate content with automatic retry and fallback
        
        Args:
            prompt (str): The prompt to send
            model (str, optional): Specific model to use
            max_retries (int): Maximum retry attempts
            temperature (float): Generation temperature
        
        Returns:
            dict: Response with success status and content
        """
        # Use primary model if none specified
        if not model:
            model = self.primary_model
        
        models_to_try = [model] + [m for m in self.fallback_models if m != model]
        
        for model_attempt, current_model in enumerate(models_to_try):
            print(f"\n🤖 Trying model: {current_model.split('/')[-1]}")
            
            for retry in range(max_retries):
                try:
                    # Apply rate limiting
                    self._rate_limit()
                    
                    # Make the request
                    response = self.client.models.generate_content(
                        model=current_model,
                        contents=[{"role": "user", "parts": [{"text": prompt}]}],
                        config={
                            "temperature": temperature,
                            "max_output_tokens": 2048
                        }
                    )
                    
                    # Extract text from response
                    text_content = ""
                    for candidate in response.candidates:
                        for part in candidate.content.parts:
                            if part.text:
                                text_content += part.text
                    
                    print(f"✅ Success with {current_model.split('/')[-1]}")
                    return {
                        "success": True,
                        "content": text_content,
                        "model_used": current_model,
                        "attempt": model_attempt + 1,
                        "retry": retry + 1
                    }
                
                except Exception as e:
                    error_str = str(e)
                    
                    # Check error type
                    is_rate_limit = self._is_rate_limit_error(error_str)
                    is_not_found = self._is_model_not_found(error_str)
                    
                    if is_not_found:
                        print(f"❌ Model {current_model.split('/')[-1]} not found (404)")
                        break  # Try next model
                    
                    if is_rate_limit:
                        if retry < max_retries - 1:
                            wait_time = min(30 + (retry * 10), 120)  # 30s, 40s, 50s max 120s
                            print(f"⚠️  Rate limit hit (retry {retry + 1}/{max_retries})")
                            print(f"⏳ Waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"❌ Rate limit exceeded for {current_model.split('/')[-1]} after {max_retries} retries")
                            break  # Try next model
                    else:
                        # Other error, try next model
                        print(f"❌ Error with {current_model.split('/')[-1]}: {error_str[:100]}")
                        break
        
        # All models failed
        return {
            "success": False,
            "error": "All models failed or rate limited",
            "content": None
        }
    
    def chat(self, message):
        """Simple chat interface"""
        print(f"\n💬 You: {message}")
        
        result = self.generate_content(message)
        
        if result["success"]:
            print(f"\n🤖 Gemini ({result['model_used'].split('/')[-1]}): {result['content']}")
            return result["content"]
        else:
            print(f"\n❌ Error: {result['error']}")
            return None
    
    def list_models(self):
        """List all available models"""
        print("\n📋 Available Models:")
        for i, model in enumerate(self.available_models, 1):
            marker = "🟢" if model["full_name"] == self.primary_model else "🔵"
            print(f"  {marker} {i:2d}. {model['display_name']}")
        
        print(f"\n🟢 Primary: {self.primary_model.split('/')[-1] if self.primary_model else 'None'}")
        print(f"🔵 Fallbacks: {', '.join([m.split('/')[-1] for m in self.fallback_models])}")


def main():
    """Main function for interactive usage"""
    try:
        # Initialize client
        client = GeminiClient()
        
        print("\n" + "="*60)
        print("🚀 Simple Gemini Client Ready!")
        print("="*60)
        
        # Show available commands
        print("\nCommands:")
        print("  /models  - List available models")
        print("  /quit    - Exit")
        print("  /help    - Show this help")
        print("  Or just type your message...")
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() in ['/models', 'models']:
                    client.list_models()
                
                elif user_input.lower() in ['/help', 'help']:
                    print("\nCommands:")
                    print("  /models  - List available models")
                    print("  /quit    - Exit")
                    print("  /help    - Show this help")
                
                else:
                    # Send message to Gemini
                    client.chat(user_input)
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")


# Example usage functions
def quick_test():
    """Quick test function"""
    client = GeminiClient()
    
    test_prompts = [
        "What could be the cytotoxicity for particle size 10 nm?",
        "Explain carbon dot toxicity in simple terms",
        "What factors affect nanoparticle toxicity?"
    ]
    
    for prompt in test_prompts:
        print(f"\n{'='*60}")
        print(f"Testing: {prompt}")
        print('='*60)
        
        result = client.generate_content(prompt)
        
        if result["success"]:
            print(f"✅ Response: {result['content'][:200]}...")
        else:
            print(f"❌ Failed: {result['error']}")
        
        time.sleep(2)  # Small delay between tests


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        quick_test()
    else:
        main()