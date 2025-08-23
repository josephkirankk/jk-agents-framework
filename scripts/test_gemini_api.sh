#!/bin/bash

# Google Gemini API Testing Scripts
# This script provides comprehensive curl commands for testing the JK-Agents API with Google Gemini models

# Configuration
API_BASE="http://localhost:8000"
CONFIG_PATH="config/gemini-test.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Google Gemini API Testing Scripts${NC}"
echo "=================================="

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}📋 $1${NC}"
    echo "----------------------------------------"
}

# Function to print test commands
print_test() {
    echo -e "${GREEN}Test: $1${NC}"
    echo -e "${BLUE}Command:${NC}"
    echo "$2"
    echo ""
}

print_section "1. Basic Text Processing Tests"

print_test "Simple Gemini Test" \
'curl -X POST "'"$API_BASE"'/worker" \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_name\": \"gemini_test_agent\",
    \"input\": \"Hello, can you confirm you are running on Google Gemini and tell me about your capabilities?\",
    \"config_path\": \"'"$CONFIG_PATH"'\"
  }"'

print_test "Text Analysis with Gemini" \
'curl -X POST "'"$API_BASE"'/worker" \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_name\": \"gemini_text_agent\",
    \"input\": \"Analyze the following text for sentiment and key themes: The new product launch exceeded expectations with 150% growth in the first quarter. Customer feedback has been overwhelmingly positive, particularly regarding the innovative features and user-friendly design.\",
    \"config_path\": \"'"$CONFIG_PATH"'\"
  }"'

print_section "2. CSV Data Analysis Tests"

print_test "Customer Data Analysis" \
'curl -X POST "'"$API_BASE"'/worker/upload" \
  -F "agent_name=gemini_csv_analyst" \
  -F "input=Analyze this customer data and provide insights about customer segments, spending patterns, and business recommendations" \
  -F "config_path='"$CONFIG_PATH"'" \
  -F "files=@customer_data.csv"'

print_test "Sales Data Analysis" \
'curl -X POST "'"$API_BASE"'/worker/upload" \
  -F "agent_name=gemini_csv_analyst" \
  -F "input=Analyze this sales data to identify trends, top-performing products, and regional performance. Provide actionable business insights." \
  -F "config_path='"$CONFIG_PATH"'" \
  -F "files=@sample_sales_data.csv"'

print_test "Custom CSV Analysis" \
'curl -X POST "'"$API_BASE"'/worker/upload" \
  -F "agent_name=gemini_csv_analyst" \
  -F "input=Perform a comprehensive analysis of this dataset. Include data quality assessment, statistical insights, and recommendations for data visualization." \
  -F "config_path='"$CONFIG_PATH"'" \
  -F "files=@your_data.csv"'

print_section "3. Image Analysis Tests"

print_test "General Image Analysis" \
'curl -X POST "'"$API_BASE"'/worker/upload" \
  -F "agent_name=gemini_image_analyzer" \
  -F "input=Analyze this image and describe what you see in detail. Include any text, objects, people, or activities visible." \
  -F "config_path='"$CONFIG_PATH"'" \
  -F "files=@image.jpg"'

print_test "Chart/Graph Analysis" \
'curl -X POST "'"$API_BASE"'/worker/upload" \
  -F "agent_name=gemini_image_analyzer" \
  -F "input=This image contains a chart or graph. Please extract the data, analyze the trends, and provide insights about what the visualization shows." \
  -F "config_path='"$CONFIG_PATH"'" \
  -F "files=@chart.png"'

print_test "OCR Text Extraction" \
'curl -X POST "'"$API_BASE"'/worker/upload" \
  -F "agent_name=gemini_image_analyzer" \
  -F "input=Extract all text from this image and organize it in a readable format. Also describe the layout and context of the text." \
  -F "config_path='"$CONFIG_PATH"'" \
  -F "files=@document_image.jpg"'

print_section "4. Multimodal Analysis Tests"

print_test "Combined CSV and Image Analysis" \
'curl -X POST "'"$API_BASE"'/worker/upload" \
  -F "agent_name=gemini_multimodal_agent" \
  -F "input=Analyze both the CSV data and the image. Compare the data insights with what you see in the image and provide a comprehensive analysis." \
  -F "config_path='"$CONFIG_PATH"'" \
  -F "files=@data.csv" \
  -F "files=@related_chart.png"'

print_test "Multiple Image Analysis" \
'curl -X POST "'"$API_BASE"'/worker/upload" \
  -F "agent_name=gemini_multimodal_agent" \
  -F "input=Compare and analyze these multiple images. Identify similarities, differences, and relationships between them." \
  -F "config_path='"$CONFIG_PATH"'" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"'

print_section "5. Supervised Multi-Agent Tests"

print_test "Complex Analysis Task" \
'curl -X POST "'"$API_BASE"'/query" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": \"Create a comprehensive business intelligence report analyzing customer behavior, sales trends, and market opportunities based on available data.\",
    \"config_path\": \"'"$CONFIG_PATH"'\"
  }"'

print_test "Data-Driven Decision Making" \
'curl -X POST "'"$API_BASE"'/query" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": \"Analyze our business data to identify the top 3 strategic opportunities for growth and provide detailed recommendations with supporting evidence.\",
    \"config_path\": \"'"$CONFIG_PATH"'\"
  }"'

print_section "6. Health Check and System Status"

print_test "API Health Check" \
'curl -X GET "'"$API_BASE"'/health"'

print_test "System Configuration Check" \
'curl -X POST "'"$API_BASE"'/worker" \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_name\": \"gemini_test_agent\",
    \"input\": \"What model are you running on and what are your current capabilities?\",
    \"config_path\": \"'"$CONFIG_PATH"'\"
  }"'

echo -e "\n${GREEN}📝 Usage Instructions:${NC}"
echo "1. Start the FastAPI server: uvicorn app.api:app --reload"
echo "2. Ensure your GOOGLE_API_KEY is set in the .env file"
echo "3. Copy and paste the curl commands above to test different scenarios"
echo "4. Replace file paths (@file.csv, @image.jpg) with your actual files"
echo "5. Modify the input prompts to match your specific use cases"

echo -e "\n${YELLOW}📁 Required Files for Testing:${NC}"
echo "- customer_data.csv (provided in repository)"
echo "- sample_sales_data.csv (provided in repository)"
echo "- Any image files (.jpg, .png, .webp, .gif)"
echo "- Any CSV files with your data"

echo -e "\n${BLUE}🔧 Troubleshooting:${NC}"
echo "- If you get 'Connection refused': Start the FastAPI server first"
echo "- If you get 'Agent not found': Check the agent_name in your request"
echo "- If you get 'File not found': Ensure file paths are correct"
echo "- If you get 'Rate limit exceeded': Wait a moment and try again"

echo -e "\n${GREEN}✅ Ready to test Google Gemini integration!${NC}"
