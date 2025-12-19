#!/usr/bin/env python3
"""
Working Gemini Client
Simple client that uses the working model with proper rate limiting
"""
import os
import time
import json
from datetime import datetime
from google import genai
from dotenv import load_dotenv
from mcp1 import execute_function

load_dotenv()

class WorkingGeminiClient:
    def __init__(self):
        """Initialize with working model"""
        self.client = genai.Client(api_key=os.getenv("API_KEY"))
        self.model = "models/gemini-2.5-flash"  # This one works!
        self.last_request_time = 0
        self.min_delay = 5  # 5 seconds between requests to be safe
        
        print(f"✅ Using working model: {self.model}")
    
    def _wait_if_needed(self):
        """Wait if we need to respect rate limits"""
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.min_delay:
            wait_time = self.min_delay - time_since_last
            print(f"⏳ Waiting {wait_time:.1f}s for rate limiting...")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def ask(self, question, temperature=0.3):
        """Ask a simple question"""
        self._wait_if_needed()
        
        try:
            print(f"\n💬 You: {question}")
            print(f"🤖 Thinking... (using {self.model.split('/')[-1]})")
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=question,
                config={"temperature": temperature}
            )
            
            # Extract text
            text = ""
            if hasattr(response, 'text'):
                text = response.text
            elif hasattr(response, 'candidates'):
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            text += part.text
            
            print(f"\n🤖 Gemini: {text}")
            return text
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)[:200]}"
            print(error_msg)
            return None
    
    def predict_toxicity(self, particle_size, zeta_potential=None, dose=None, 
                        time_hours=None, solvent=None, cell_type=None, cell_origin=None):
        """Predict toxicity using MCP1 functions and explain with Gemini"""
        
        print(f"\n🔬 Predicting toxicity for {particle_size}nm particle...")
        
        # Use defaults if not provided
        params = {
            "ParticleSize": float(particle_size),
            "ZetaPotential": float(zeta_potential or -20.0),
            "Dose": float(dose or 50.0),
            "Time": float(time_hours or 24),
            "Solvent": str(solvent or "Water"),
            "CellType": str(cell_type or "HeLa"),
            "CellOrigin": str(cell_origin or "Human")
        }
        
        print(f"📋 Parameters: {params}")
        
        # Run prediction
        result = execute_function("predict_toxicity_without_family", **params)
        
        if result["success"]:
            print(f"✅ Prediction: {result['class_label']}")
            print(f"   Confidence: {result['confidence']:.3f}")
            print(f"   Toxic Probability: {result['probability_toxic']:.3f}")
            
            # Ask Gemini to explain
            explanation_prompt = f"""
            I ran a toxicity prediction for carbon dots with these parameters:
            - Particle Size: {params['ParticleSize']} nm
            - Zeta Potential: {params['ZetaPotential']} mV
            - Dose: {params['Dose']} µg/mL
            - Time: {params['Time']} hours
            - Solvent: {params['Solvent']}
            - Cell Type: {params['CellType']}
            - Cell Origin: {params['CellOrigin']}
            
            The ML model predicted: {result['class_label']} with {result['confidence']:.1%} confidence.
            Toxic probability: {result['probability_toxic']:.1%}
            
            Can you explain what this result means and what factors likely contributed to this prediction?
            Keep it concise and scientific.
            """
            
            print(f"\n🤖 Getting Gemini's explanation...")
            explanation = self.ask(explanation_prompt, temperature=0.2)
            
            return {
                "prediction": result,
                "explanation": explanation
            }
        else:
            print(f"❌ Prediction failed: {result['error']}")
            return None
    
    def chat_loop(self):
        """Interactive chat loop"""
        print("\n" + "="*60)
        print("💬 Interactive Chat with Working Gemini Model")
        print("="*60)
        print("Commands:")
        print("  'predict 10' - Predict toxicity for 10nm particle")
        print("  'quit' - Exit")
        print("  Or ask any question about toxicity...")
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower().startswith('predict'):
                    # Extract particle size
                    try:
                        parts = user_input.split()
                        size = float(parts[1]) if len(parts) > 1 else 10.0
                        self.predict_toxicity(size)
                    except:
                        print("❌ Usage: predict <size_nm>")
                else:
                    # Regular chat
                    self.ask(user_input)
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function"""
    import sys
    
    try:
        client = WorkingGeminiClient()
        
        if len(sys.argv) > 1:
            if sys.argv[1] == "chat":
                client.chat_loop()
            elif sys.argv[1] == "predict":
                size = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
                client.predict_toxicity(size)
            elif sys.argv[1] == "ask":
                question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hello"
                client.ask(question)
            else:
                print("Usage: python working_gemini_client.py [chat|predict <size>|ask <question>]")
        else:
            # Default: test basic functionality
            print("🧪 Testing basic functionality...")
            
            # Test 1: Simple question
            client.ask("What could be the cytotoxicity for particle size 10 nm?")
            
            # Test 2: Prediction with explanation
            client.predict_toxicity(10.0)
    
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    main()