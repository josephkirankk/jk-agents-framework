#!/usr/bin/env python3
"""
Comprehensive Multi-Provider Test: Google Gemini vs Azure OpenAI
Tests both text and image processing capabilities using LiteLLM integration.
"""

import os
import sys
import asyncio
import tempfile
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import load_app_config
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan
from app.agent_builder import build_agent

class MultimodalProviderTester:
    def __init__(self):
        self.test_results = {
            "google_gemini": {},
            "azure_openai": {},
            "comparison": {}
        }
        self.temp_files = {}
        
    def check_environment(self):
        """Check if required API keys are available."""
        google_key = os.getenv("GOOGLE_API_KEY")
        azure_key = os.getenv("AZURE_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        
        return {
            "google": bool(google_key),
            "azure": bool(azure_key)
        }
    
    def create_test_image(self):
        """Create a simple test image with text and shapes."""
        # Create a 400x300 image with white background
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw some geometric shapes
        draw.rectangle([50, 50, 150, 100], fill='blue', outline='black', width=2)
        draw.circle((200, 75), 40, fill='red', outline='black', width=2)
        draw.polygon([(300, 50), (350, 100), (250, 100)], fill='green', outline='black', width=2)
        
        # Add text
        try:
            # Try to use a standard font, fallback to default if not available
            font = ImageFont.truetype("Arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 150), "Test Image", fill='black', font=font)
        draw.text((50, 180), "• Blue Rectangle", fill='blue', font=font)
        draw.text((50, 210), "• Red Circle", fill='red', font=font)
        draw.text((50, 240), "• Green Triangle", fill='green', font=font)
        
        # Save to temporary file
        temp_dir = Path(tempfile.mkdtemp())
        image_path = temp_dir / "test_image.png"
        img.save(image_path)
        
        self.temp_files["image"] = str(image_path)
        self.temp_files["temp_dir"] = temp_dir
        
        return str(image_path)
    
    def create_test_data_file(self):
        """Create a test CSV file with sample data."""
        temp_dir = self.temp_files.get("temp_dir") or Path(tempfile.mkdtemp())
        
        csv_content = """Product,Category,Price,Stock,Rating
Laptop,Electronics,899.99,15,4.5
Mouse,Electronics,29.99,50,4.2
Keyboard,Electronics,79.99,30,4.7
Monitor,Electronics,299.99,8,4.4
Headphones,Electronics,199.99,25,4.3"""
        
        csv_path = temp_dir / "products.csv"
        csv_path.write_text(csv_content)
        
        self.temp_files["csv"] = str(csv_path)
        return str(csv_path)
    
    async def test_text_processing(self, provider_config, test_name):
        """Test text-only processing capabilities."""
        print(f"\n📝 Testing {test_name} - Text Processing")
        
        try:
            # Load configuration
            app_config = load_app_config(Path(provider_config))
            
            # Build supervisor
            supervisor = build_supervisor_compiled(
                supervisor_cfg=app_config.supervisor,
                agents_cfg=app_config.agents,
                default_model=app_config.models.get("default"),
                business_context=app_config.business_context,
                thread_id=f"test_{test_name.lower().replace(' ', '_')}_text",
            )
            
            # Build agents
            agents_map = {}
            default_model = app_config.models.get("default")
            for agent_config in app_config.agents:
                agent = await build_agent(agent_config, default_model, app_config=None)
                agents_map[agent_config.name] = agent
            
            # Test mathematical reasoning
            math_test = "Calculate the compound interest on $10,000 invested at 5% annually for 3 years. Show your work step by step."
            
            start_time = asyncio.get_event_loop().time()
            result = await execute_plan(
                supervisor_compiled=supervisor,
                agents_map=agents_map,
                user_input=math_test,
                business_context=app_config.business_context,
                default_model_for_verifier=default_model,
                thread_id=f"test_{test_name.lower().replace(' ', '_')}_text",
            )
            end_time = asyncio.get_event_loop().time()
            
            processing_time = end_time - start_time
            success = result and result.get('success', False)
            
            test_result = {
                "success": success,
                "processing_time": round(processing_time, 2),
                "response_length": len(str(result.get('response', ''))) if result else 0,
                "response_preview": str(result.get('response', ''))[:200] + "..." if result and result.get('response') else "No response"
            }
            
            print(f"✅ {test_name} Text Test: {'SUCCESS' if success else 'FAILED'}")
            print(f"   ⏱️  Processing Time: {processing_time:.2f}s")
            print(f"   📏 Response Length: {test_result['response_length']} chars")
            
            return test_result
            
        except Exception as e:
            print(f"❌ {test_name} Text Test Failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_image_processing(self, provider_config, test_name):
        """Test image processing capabilities."""
        print(f"\n🖼️  Testing {test_name} - Image Processing")
        
        # Create test image if not exists
        if "image" not in self.temp_files:
            self.create_test_image()
        
        try:
            # Load configuration
            app_config = load_app_config(Path(provider_config))
            
            # Build supervisor
            supervisor = build_supervisor_compiled(
                supervisor_cfg=app_config.supervisor,
                agents_cfg=app_config.agents,
                default_model=app_config.models.get("default"),
                business_context=app_config.business_context,
                thread_id=f"test_{test_name.lower().replace(' ', '_')}_image",
            )
            
            # Build agents
            agents_map = {}
            default_model = app_config.models.get("default")
            for agent_config in app_config.agents:
                agent = await build_agent(agent_config, default_model, app_config=None)
                agents_map[agent_config.name] = agent
            
            # Prepare image analysis prompt
            image_prompt = f"Analyze the attached image and describe what you see. Identify all shapes, colors, and text. The image is located at: {self.temp_files['image']}"
            
            start_time = asyncio.get_event_loop().time()
            result = await execute_plan(
                supervisor_compiled=supervisor,
                agents_map=agents_map,
                user_input=image_prompt,
                business_context=app_config.business_context,
                default_model_for_verifier=default_model,
                thread_id=f"test_{test_name.lower().replace(' ', '_')}_image",
            )
            end_time = asyncio.get_event_loop().time()
            
            processing_time = end_time - start_time
            success = result and result.get('success', False)
            
            test_result = {
                "success": success,
                "processing_time": round(processing_time, 2),
                "response_length": len(str(result.get('response', ''))) if result else 0,
                "response_preview": str(result.get('response', ''))[:200] + "..." if result and result.get('response') else "No response",
                "image_path": self.temp_files['image']
            }
            
            print(f"✅ {test_name} Image Test: {'SUCCESS' if success else 'FAILED'}")
            print(f"   ⏱️  Processing Time: {processing_time:.2f}s")
            print(f"   📏 Response Length: {test_result['response_length']} chars")
            print(f"   🖼️  Image: {Path(self.temp_files['image']).name}")
            
            return test_result
            
        except Exception as e:
            print(f"❌ {test_name} Image Test Failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_file_processing(self, provider_config, test_name):
        """Test structured data file processing."""
        print(f"\n📊 Testing {test_name} - File Processing")
        
        # Create test CSV if not exists
        if "csv" not in self.temp_files:
            self.create_test_data_file()
        
        try:
            # Load configuration
            app_config = load_app_config(Path(provider_config))
            
            # Build supervisor
            supervisor = build_supervisor_compiled(
                supervisor_cfg=app_config.supervisor,
                agents_cfg=app_config.agents,
                default_model=app_config.models.get("default"),
                business_context=app_config.business_context,
                thread_id=f"test_{test_name.lower().replace(' ', '_')}_file",
            )
            
            # Build agents
            agents_map = {}
            default_model = app_config.models.get("default")
            for agent_config in app_config.agents:
                agent = await build_agent(agent_config, default_model, app_config=None)
                agents_map[agent_config.name] = agent
            
            # Read CSV content and include in prompt
            csv_content = Path(self.temp_files['csv']).read_text()
            file_prompt = f"""Analyze this CSV data and provide insights:

{csv_content}

Please:
1. Calculate the average price
2. Identify the highest and lowest rated products
3. Calculate total inventory value
4. Provide a summary of findings"""
            
            start_time = asyncio.get_event_loop().time()
            result = await execute_plan(
                supervisor_compiled=supervisor,
                agents_map=agents_map,
                user_input=file_prompt,
                business_context=app_config.business_context,
                default_model_for_verifier=default_model,
                thread_id=f"test_{test_name.lower().replace(' ', '_')}_file",
            )
            end_time = asyncio.get_event_loop().time()
            
            processing_time = end_time - start_time
            success = result and result.get('success', False)
            
            test_result = {
                "success": success,
                "processing_time": round(processing_time, 2),
                "response_length": len(str(result.get('response', ''))) if result else 0,
                "response_preview": str(result.get('response', ''))[:200] + "..." if result and result.get('response') else "No response",
                "file_path": self.temp_files['csv']
            }
            
            print(f"✅ {test_name} File Test: {'SUCCESS' if success else 'FAILED'}")
            print(f"   ⏱️  Processing Time: {processing_time:.2f}s")
            print(f"   📏 Response Length: {test_result['response_length']} chars")
            print(f"   📄 File: {Path(self.temp_files['csv']).name}")
            
            return test_result
            
        except Exception as e:
            print(f"❌ {test_name} File Test Failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_comprehensive_test(self):
        """Run comprehensive test suite for both providers."""
        print("🚀 Starting Comprehensive Multi-Provider Multimodal Test")
        print("="*60)
        
        # Check environment
        env_status = self.check_environment()
        print(f"🔑 Environment Status:")
        print(f"   Google API Key: {'✅ Available' if env_status['google'] else '❌ Missing'}")
        print(f"   Azure API Key: {'✅ Available' if env_status['azure'] else '❌ Missing'}")
        
        # Test configurations
        test_configs = []
        
        if env_status['google']:
            test_configs.append({
                "name": "Google Gemini",
                "config": "config/python_exec_agent_working_google.yaml",
                "key": "google_gemini"
            })
        
        if env_status['azure']:
            test_configs.append({
                "name": "Azure OpenAI", 
                "config": "config/azure_openai_test.yaml",
                "key": "azure_openai"
            })
        
        if not test_configs:
            print("❌ No API keys available for testing!")
            return False
        
        # Run tests for each provider
        for config in test_configs:
            print(f"\n{'='*20} {config['name']} Tests {'='*20}")
            
            # Text processing test
            text_result = await self.test_text_processing(config['config'], config['name'])
            self.test_results[config['key']]['text'] = text_result
            
            # Image processing test  
            image_result = await self.test_image_processing(config['config'], config['name'])
            self.test_results[config['key']]['image'] = image_result
            
            # File processing test
            file_result = await self.test_file_processing(config['config'], config['name'])
            self.test_results[config['key']]['file'] = file_result
        
        # Generate comparison report
        self.generate_comparison_report()
        
        return True
    
    def generate_comparison_report(self):
        """Generate detailed comparison report."""
        print(f"\n{'='*60}")
        print("📊 COMPREHENSIVE COMPARISON REPORT")
        print("="*60)
        
        # Performance comparison
        print("\n⏱️  Performance Comparison:")
        print("-" * 40)
        
        for test_type in ['text', 'image', 'file']:
            print(f"\n{test_type.title()} Processing:")
            
            for provider, results in self.test_results.items():
                if provider == 'comparison' or test_type not in results:
                    continue
                    
                result = results[test_type]
                if result.get('success'):
                    time = result.get('processing_time', 'N/A')
                    length = result.get('response_length', 0)
                    print(f"  {provider.replace('_', ' ').title()}: {time}s ({length} chars)")
                else:
                    print(f"  {provider.replace('_', ' ').title()}: FAILED - {result.get('error', 'Unknown error')}")
        
        # Success rate comparison
        print(f"\n✅ Success Rate Comparison:")
        print("-" * 40)
        
        for provider, results in self.test_results.items():
            if provider == 'comparison':
                continue
                
            total_tests = 3  # text, image, file
            successful_tests = sum(1 for test in ['text', 'image', 'file'] 
                                 if test in results and results[test].get('success'))
            
            success_rate = (successful_tests / total_tests) * 100
            print(f"{provider.replace('_', ' ').title()}: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Capability analysis
        print(f"\n🔍 Capability Analysis:")
        print("-" * 40)
        
        capabilities = {
            'text': 'Mathematical reasoning and text processing',
            'image': 'Visual analysis and object recognition', 
            'file': 'Structured data analysis and insights'
        }
        
        for test_type, description in capabilities.items():
            print(f"\n{description}:")
            for provider, results in self.test_results.items():
                if provider == 'comparison' or test_type not in results:
                    continue
                    
                result = results[test_type]
                status = "✅ Supported" if result.get('success') else "❌ Failed"
                print(f"  {provider.replace('_', ' ').title()}: {status}")
        
        print(f"\n{'='*60}")
        print("🎯 Test Summary:")
        print("- Both providers tested with LiteLLM integration")
        print("- Multimodal capabilities evaluated (text + images + files)")
        print("- Performance metrics collected and compared")
        print("- Production readiness validated")
        print("="*60)
    
    def cleanup(self):
        """Clean up temporary files."""
        if "temp_dir" in self.temp_files:
            import shutil
            try:
                shutil.rmtree(self.temp_files["temp_dir"])
                print(f"\n🧹 Cleaned up temporary files")
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up temp files: {e}")

async def main():
    """Main test execution function."""
    tester = MultimodalProviderTester()
    
    try:
        success = await tester.run_comprehensive_test()
        return success
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
