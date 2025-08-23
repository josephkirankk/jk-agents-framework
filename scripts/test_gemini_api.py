#!/usr/bin/env python3
"""
Google Gemini API Testing Script

This script provides comprehensive testing for the JK-Agents API with Google Gemini models.
It includes tests for text processing, CSV analysis, image analysis, and multimodal capabilities.
"""

import requests
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configuration
API_BASE = "http://localhost:8000"
CONFIG_PATH = "config/gemini-test.yaml"

class GeminiAPITester:
    def __init__(self, api_base: str = API_BASE, config_path: str = CONFIG_PATH):
        self.api_base = api_base
        self.config_path = config_path
        self.session = requests.Session()
        
    def print_section(self, title: str):
        """Print a formatted section header."""
        print(f"\n🧪 {title}")
        print("=" * (len(title) + 4))
        
    def print_test(self, test_name: str, success: bool, response_data: Any = None):
        """Print test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if response_data and isinstance(response_data, dict):
            if "response" in response_data:
                print(f"   Response: {response_data['response'][:100]}...")
            elif "error" in response_data:
                print(f"   Error: {response_data['error']}")
        print()
        
    def test_health_check(self) -> bool:
        """Test API health check endpoint."""
        try:
            response = self.session.get(f"{self.api_base}/health")
            success = response.status_code == 200
            self.print_test("Health Check", success, response.json() if success else None)
            return success
        except Exception as e:
            self.print_test("Health Check", False, {"error": str(e)})
            return False
            
    def test_text_processing(self) -> bool:
        """Test basic text processing with Gemini."""
        try:
            data = {
                "agent_name": "gemini_test_agent",
                "input": "Hello, can you confirm you are running on Google Gemini and tell me about your capabilities?",
                "config_path": self.config_path
            }
            
            response = self.session.post(
                f"{self.api_base}/worker",
                headers={"Content-Type": "application/json"},
                json=data
            )
            
            success = response.status_code == 200
            response_data = response.json() if success else {"error": response.text}
            self.print_test("Basic Text Processing", success, response_data)
            return success
            
        except Exception as e:
            self.print_test("Basic Text Processing", False, {"error": str(e)})
            return False
            
    def test_csv_analysis(self, csv_file: str = "customer_data.csv") -> bool:
        """Test CSV analysis with Gemini."""
        try:
            if not os.path.exists(csv_file):
                self.print_test(f"CSV Analysis ({csv_file})", False, {"error": f"File {csv_file} not found"})
                return False
                
            data = {
                "agent_name": "gemini_csv_analyst",
                "input": "Analyze this customer data and provide insights about customer segments, spending patterns, and business recommendations",
                "config_path": self.config_path
            }
            
            with open(csv_file, 'rb') as f:
                files = {"files": (csv_file, f, "text/csv")}
                response = self.session.post(
                    f"{self.api_base}/worker/upload",
                    data=data,
                    files=files
                )
            
            success = response.status_code == 200
            response_data = response.json() if success else {"error": response.text}
            self.print_test(f"CSV Analysis ({csv_file})", success, response_data)
            return success
            
        except Exception as e:
            self.print_test(f"CSV Analysis ({csv_file})", False, {"error": str(e)})
            return False
            
    def test_image_analysis(self, image_file: str) -> bool:
        """Test image analysis with Gemini."""
        try:
            if not os.path.exists(image_file):
                self.print_test(f"Image Analysis ({image_file})", False, {"error": f"File {image_file} not found"})
                return False
                
            data = {
                "agent_name": "gemini_image_analyzer",
                "input": "Analyze this image and describe what you see in detail. Include any text, objects, people, or activities visible.",
                "config_path": self.config_path
            }
            
            # Determine MIME type
            ext = Path(image_file).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp',
                '.gif': 'image/gif'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            
            with open(image_file, 'rb') as f:
                files = {"files": (image_file, f, mime_type)}
                response = self.session.post(
                    f"{self.api_base}/worker/upload",
                    data=data,
                    files=files
                )
            
            success = response.status_code == 200
            response_data = response.json() if success else {"error": response.text}
            self.print_test(f"Image Analysis ({image_file})", success, response_data)
            return success
            
        except Exception as e:
            self.print_test(f"Image Analysis ({image_file})", False, {"error": str(e)})
            return False
            
    def test_multimodal_analysis(self, csv_file: str, image_file: str) -> bool:
        """Test multimodal analysis with both CSV and image."""
        try:
            if not os.path.exists(csv_file) or not os.path.exists(image_file):
                missing = []
                if not os.path.exists(csv_file):
                    missing.append(csv_file)
                if not os.path.exists(image_file):
                    missing.append(image_file)
                self.print_test("Multimodal Analysis", False, {"error": f"Files not found: {', '.join(missing)}"})
                return False
                
            data = {
                "agent_name": "gemini_multimodal_agent",
                "input": "Analyze both the CSV data and the image. Compare the data insights with what you see in the image and provide a comprehensive analysis.",
                "config_path": self.config_path
            }
            
            # Prepare files for multipart upload
            with open(csv_file, 'rb') as f1, open(image_file, 'rb') as f2:
                files = [
                    ("files", (csv_file, f1, "text/csv")),
                    ("files", (image_file, f2, "image/jpeg"))
                ]

                response = self.session.post(
                    f"{self.api_base}/worker/upload",
                    data=data,
                    files=files
                )
            
            success = response.status_code == 200
            response_data = response.json() if success else {"error": response.text}
            self.print_test("Multimodal Analysis", success, response_data)
            return success
            
        except Exception as e:
            self.print_test("Multimodal Analysis", False, {"error": str(e)})
            return False
            
    def test_supervised_query(self) -> bool:
        """Test supervised multi-agent query."""
        try:
            data = {
                "input": "Create a comprehensive analysis of business opportunities using Google Gemini's capabilities",
                "config_path": self.config_path
            }
            
            response = self.session.post(
                f"{self.api_base}/query",
                headers={"Content-Type": "application/json"},
                json=data
            )
            
            success = response.status_code == 200
            response_data = response.json() if success else {"error": response.text}
            self.print_test("Supervised Multi-Agent Query", success, response_data)
            return success
            
        except Exception as e:
            self.print_test("Supervised Multi-Agent Query", False, {"error": str(e)})
            return False
            
    def run_all_tests(self):
        """Run all available tests."""
        print("🚀 Starting Google Gemini API Tests")
        print("====================================")
        
        results = []
        
        # Health check
        self.print_section("Health Check")
        results.append(("Health Check", self.test_health_check()))
        
        # Text processing
        self.print_section("Text Processing")
        results.append(("Text Processing", self.test_text_processing()))
        
        # CSV analysis
        self.print_section("CSV Analysis")
        results.append(("CSV Analysis", self.test_csv_analysis("customer_data.csv")))
        results.append(("Sales CSV Analysis", self.test_csv_analysis("sample_sales_data.csv")))
        
        # Image analysis (if image files exist)
        self.print_section("Image Analysis")
        test_images = ["test_image.jpg", "chart.png", "document.jpg"]
        for img in test_images:
            if os.path.exists(img):
                results.append((f"Image Analysis ({img})", self.test_image_analysis(img)))
                break
        else:
            print("⚠️  No test images found. Skipping image analysis tests.")
            print("   Create test_image.jpg, chart.png, or document.jpg to test image analysis.")
        
        # Multimodal analysis
        self.print_section("Multimodal Analysis")
        if os.path.exists("customer_data.csv") and any(os.path.exists(img) for img in test_images):
            img_file = next((img for img in test_images if os.path.exists(img)), None)
            if img_file:
                results.append(("Multimodal Analysis", self.test_multimodal_analysis("customer_data.csv", img_file)))
        else:
            print("⚠️  Skipping multimodal tests - need both CSV and image files")
        
        # Supervised query
        self.print_section("Supervised Query")
        results.append(("Supervised Query", self.test_supervised_query()))
        
        # Summary
        self.print_section("Test Results Summary")
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Google Gemini integration is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            
        return passed == total


def main():
    """Main function to run the tests."""
    tester = GeminiAPITester()
    
    print("📋 Prerequisites:")
    print("1. FastAPI server should be running: uvicorn app.api:app --reload")
    print("2. GOOGLE_API_KEY should be set in your .env file")
    print("3. Test files should be available (customer_data.csv, sample_sales_data.csv)")
    print("4. Optional: Add test images (test_image.jpg, chart.png, document.jpg)")
    
    input("\nPress Enter to start testing...")
    
    success = tester.run_all_tests()
    
    if not success:
        print("\n🔧 Troubleshooting Tips:")
        print("- Ensure the FastAPI server is running on http://localhost:8000")
        print("- Check that your GOOGLE_API_KEY is valid and has sufficient quota")
        print("- Verify that the config file exists: config/gemini-test.yaml")
        print("- Make sure test files are in the correct location")
    
    return success


if __name__ == "__main__":
    main()
