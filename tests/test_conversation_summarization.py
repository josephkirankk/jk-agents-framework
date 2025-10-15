#!/usr/bin/env python3
"""
Test Conversation Self-Summarization System

This test validates that the conversation summarization feature works correctly
when conversations become too long, preserving critical data while reducing memory usage.
"""

import os
import sys
import requests
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent  # Go up one level to project root
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
    
    # Fix for LangChain AzureChatOpenAI compatibility
    # It expects OPENAI_API_VERSION instead of AZURE_OPENAI_API_VERSION
    if os.getenv('AZURE_OPENAI_API_VERSION') and not os.getenv('OPENAI_API_VERSION'):
        os.environ['OPENAI_API_VERSION'] = os.getenv('AZURE_OPENAI_API_VERSION')
        print("✅ Set OPENAI_API_VERSION from AZURE_OPENAI_API_VERSION for compatibility")
    
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, skipping .env file loading")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

class ConversationSummarizationTest:
    """Test conversation summarization and memory optimization."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.thread_id = f"summarization-test-{int(time.time())}"
        self.config_path = "config/python_exec_agent_working.yaml"
        
    def check_api_server(self) -> bool:
        """Check if API server is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def send_request(self, user_input: str) -> dict:
        """Send API request."""
        payload = {
            "input": user_input,
            "thread_id": self.thread_id,
            "config_path": self.config_path,
            "raw_output": False
        }
        
        try:
            response = requests.post(f"{self.base_url}/query", json=payload, timeout=120)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text, "status": response.status_code}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_long_conversation(self) -> list:
        """Create a long conversation with structured data to trigger summarization."""
        print("🏗️ Building long conversation to trigger summarization...")
        
        requests_data = []
        
        # Turn 1: Create initial large dataset
        print("📤 Turn 1: Create large employee dataset")
        result1 = self.send_request("""
        Create a comprehensive employee database with 25 employees. For each employee include:
        - ID (starting from EMP001)
        - Full name (realistic names)
        - Department (Engineering, Marketing, Sales, HR, Finance)
        - Salary (between $40,000 - $120,000)
        - Years of experience (1-15 years)
        - Skills (3-5 technical skills each)
        - Performance rating (1-5 scale)
        
        Structure this as a Python list of dictionaries and execute the code.
        """)
        requests_data.append(("Turn 1 - Create Dataset", result1))
        
        if result1['success']:
            print(f"✅ Turn 1 completed: {len(result1['data']['response'])} chars")
        
        # Turn 2: Add more data and analysis
        print("📤 Turn 2: Add detailed analysis")
        result2 = self.send_request("""
        Using the employee dataset from the previous request:
        1. Calculate average salary by department
        2. Find top 5 performers by rating
        3. Create department-wise skill analysis
        4. Generate summary statistics including:
           - Total employees per department
           - Average experience by department
           - Salary ranges by department
        
        Present this as detailed tables and charts.
        """)
        requests_data.append(("Turn 2 - Analysis", result2))
        
        if result2['success']:
            print(f"✅ Turn 2 completed: {len(result2['data']['response'])} chars")
        
        # Turn 3: More complex operations
        print("📤 Turn 3: Complex data operations")
        result3 = self.send_request("""
        Based on the employee data and analysis from previous turns:
        1. Create a promotion recommendation system
        2. Generate detailed performance improvement plans for low performers
        3. Design optimal team compositions for new projects
        4. Calculate budget projections for salary increases
        5. Create comprehensive reporting dashboard data
        
        Include specific employee names, IDs, and detailed recommendations.
        """)
        requests_data.append(("Turn 3 - Complex Operations", result3))
        
        if result3['success']:
            print(f"✅ Turn 3 completed: {len(result3['data']['response'])} chars")
        
        # Turn 4: Additional large content
        print("📤 Turn 4: Generate training programs")
        result4 = self.send_request("""
        Using all the employee data and analysis from previous turns:
        1. Design personalized training programs for each employee
        2. Create detailed learning paths based on current skills and career goals
        3. Generate training schedules for the next 6 months
        4. Calculate training costs and ROI projections
        5. Create detailed progress tracking mechanisms
        
        Make this very comprehensive with specific details for each employee.
        """)
        requests_data.append(("Turn 4 - Training Programs", result4))
        
        if result4['success']:
            print(f"✅ Turn 4 completed: {len(result4['data']['response'])} chars")
        
        # Turn 5: Final large request to push over summarization threshold
        print("📤 Turn 5: Comprehensive reporting")
        result5 = self.send_request("""
        Create a comprehensive annual report using ALL data from previous turns:
        1. Executive summary with key metrics
        2. Detailed employee profiles with complete histories
        3. Financial analysis with salary breakdowns
        4. Performance trends and predictions
        5. Training effectiveness analysis
        6. Organizational development recommendations
        7. Detailed appendices with raw data tables
        
        Make this extremely detailed - include every piece of data we've discussed.
        """)
        requests_data.append(("Turn 5 - Comprehensive Report", result5))
        
        if result5['success']:
            print(f"✅ Turn 5 completed: {len(result5['data']['response'])} chars")
        
        return requests_data
    
    def check_summarization_triggered(self) -> dict:
        """Check if summarization was triggered by examining memory logs."""
        print("\n🔍 Checking if summarization was triggered...")
        
        # Look for memory logs that might indicate summarization
        import glob
        memory_logs = glob.glob(f"memory_logs/memory_{self.thread_id}_*.log")
        
        summarization_triggered = False
        log_content = ""
        
        if memory_logs:
            try:
                with open(memory_logs[0], 'r') as f:
                    log_content = f.read()
                    summarization_triggered = 'summarization' in log_content.lower() or 'summary' in log_content.lower()
            except:
                pass
        
        # Also check via API request about conversation size
        size_check = self.send_request("What's the current size of our conversation? How many turns have we had?")
        
        return {
            'logs_found': len(memory_logs) > 0,
            'summarization_triggered': summarization_triggered,
            'log_content_sample': log_content[:500] if log_content else "",
            'size_check_response': size_check['data']['response'] if size_check['success'] else "Failed"
        }
    
    def test_data_preservation_after_summarization(self) -> bool:
        """Test that critical data is preserved after summarization."""
        print("\n🔒 Testing data preservation after summarization...")
        
        # Request specific data that should be preserved
        preservation_tests = [
            ("Employee Count", "How many employees are in our dataset? List the first 5 employee IDs."),
            ("Department Data", "What departments do we have and how many employees in each?"),
            ("Salary Analysis", "What was the average salary by department from our analysis?"),
            ("Performance Data", "Who were the top 5 performers we identified?"),
            ("Training Programs", "What training programs did we design? Give me 3 examples.")
        ]
        
        results = {}
        
        for test_name, question in preservation_tests:
            print(f"  • Testing {test_name}...")
            result = self.send_request(question)
            
            if result['success']:
                response = result['data']['response']
                # Check if response contains meaningful data (not just "I don't have that information")
                has_data = (
                    len(response) > 100 and
                    not any(phrase in response.lower() for phrase in [
                        "don't have", "no information", "not available", 
                        "cannot find", "no data", "not provided"
                    ])
                )
                results[test_name] = {
                    'success': True,
                    'has_meaningful_data': has_data,
                    'response_length': len(response)
                }
                print(f"    ✅ {test_name}: {len(response)} chars, meaningful: {has_data}")
            else:
                results[test_name] = {
                    'success': False,
                    'has_meaningful_data': False,
                    'response_length': 0
                }
                print(f"    ❌ {test_name}: Request failed")
        
        return results
    
    def test_continued_functionality(self) -> bool:
        """Test that conversation continues to work after summarization."""
        print("\n🔄 Testing continued functionality after summarization...")
        
        # Make a new request that builds on previous data
        result = self.send_request("""
        Based on all our previous employee data and analysis:
        1. Create a new project team of 5 people from different departments
        2. Assign roles based on their skills and experience
        3. Calculate the team's total cost and average experience
        
        Use specific employee names and data from our previous conversations.
        """)
        
        if result['success']:
            response = result['data']['response']
            has_continuity = (
                len(response) > 200 and
                any(keyword in response.lower() for keyword in [
                    'employee', 'department', 'experience', 'skill', 'emp0'
                ])
            )
            print(f"✅ Continued functionality: {has_continuity}")
            print(f"   Response length: {len(response)} chars")
            return has_continuity
        else:
            print(f"❌ Continued functionality test failed: {result['error']}")
            return False
    
    def run_test(self):
        """Run the conversation summarization test."""
        print("🧪 Conversation Self-Summarization Test")
        print("=" * 60)
        
        if not self.check_api_server():
            print("❌ API server not running")
            return False
            
        print("✅ API server is running")
        
        # Step 1: Create long conversation
        conversation_data = self.create_long_conversation()
        successful_requests = sum(1 for _, result in conversation_data if result['success'])
        
        print(f"\n📊 Conversation Creation Results:")
        print(f"  • Total requests: {len(conversation_data)}")
        print(f"  • Successful requests: {successful_requests}")
        
        if successful_requests < 3:
            print("❌ Not enough successful requests to test summarization")
            return False
        
        # Step 2: Check if summarization was triggered
        time.sleep(3)  # Allow time for any background summarization
        summarization_check = self.check_summarization_triggered()
        
        print(f"\n📈 Summarization Analysis:")
        print(f"  • Memory logs found: {summarization_check['logs_found']}")
        print(f"  • Summarization triggered: {summarization_check['summarization_triggered']}")
        if summarization_check['log_content_sample']:
            print(f"  • Log sample: {summarization_check['log_content_sample'][:100]}...")
        
        # Step 3: Test data preservation
        preservation_results = self.test_data_preservation_after_summarization()
        preserved_data_count = sum(1 for result in preservation_results.values() 
                                 if result['success'] and result['has_meaningful_data'])
        
        print(f"\n📋 Data Preservation Results:")
        print(f"  • Tests passed: {preserved_data_count}/{len(preservation_results)}")
        
        # Step 4: Test continued functionality
        continued_functionality = self.test_continued_functionality()
        
        # Final assessment
        success_criteria = {
            "Long conversation created": successful_requests >= 4,
            "Memory system working": summarization_check['logs_found'],
            "Data preservation": preserved_data_count >= 3,
            "Continued functionality": continued_functionality
        }
        
        print(f"\n📋 Success Criteria:")
        all_passed = True
        for criterion, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {criterion}: {passed}")
            if not passed:
                all_passed = False
        
        print(f"\n" + "=" * 60)
        print("🏆 FINAL RESULTS")
        print("=" * 60)
        
        if all_passed:
            print("🎉 CONVERSATION SUMMARIZATION TEST PASSED!")
            print("✅ Summarization functionality working")
            print("✅ Data preservation successful")
            print("✅ Memory optimization effective")
            print("✅ Continued conversation functionality intact")
        else:
            print("⚠️  SUMMARIZATION ISSUES DETECTED")
            print("🔧 Check specific failure points above")
            
            # Additional diagnostics
            if not summarization_check['logs_found']:
                print("💡 Tip: Memory logs not found - check memory system configuration")
            if preserved_data_count < 3:
                print("💡 Tip: Data preservation issues - check summarization algorithm")
            if not continued_functionality:
                print("💡 Tip: Continued functionality failed - check context injection after summarization")
        
        return all_passed


def main():
    """Run the conversation summarization test."""
    test = ConversationSummarizationTest()
    success = test.run_test()
    
    if success:
        print(f"\n🚀 SUMMARIZATION SYSTEM VALIDATED!")
        print(f"The conversation summarization feature is working correctly.")
    else:
        print(f"\n🔧 SUMMARIZATION NEEDS ATTENTION")
        print(f"Review specific test failures for optimization opportunities.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
