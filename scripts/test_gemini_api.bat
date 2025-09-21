@echo off
REM Google Gemini API Testing Scripts for Windows
REM This script provides comprehensive curl commands for testing the JK-Agents API with Google Gemini models

set API_BASE=http://localhost:8000
set CONFIG_PATH=config/gemini-test.yaml

echo.
echo 🧪 Google Gemini API Testing Scripts
echo ==================================

echo.
echo 📋 1. Basic Text Processing Tests
echo ----------------------------------------

echo.
echo Test: Simple Gemini Test
echo Command:
echo curl -X POST "%API_BASE%/worker" ^
  -H "Content-Type: application/json" ^
  -d "{\"agent_name\": \"gemini_test_agent\", \"input\": \"Hello, can you confirm you are running on Google Gemini and tell me about your capabilities?\", \"config_path\": \"%CONFIG_PATH%\"}"

echo.
echo Test: Text Analysis with Gemini
echo Command:
echo curl -X POST "%API_BASE%/worker" ^
  -H "Content-Type: application/json" ^
  -d "{\"agent_name\": \"gemini_text_agent\", \"input\": \"Analyze the following text for sentiment and key themes: The new product launch exceeded expectations with 150%% growth in the first quarter. Customer feedback has been overwhelmingly positive, particularly regarding the innovative features and user-friendly design.\", \"config_path\": \"%CONFIG_PATH%\"}"

echo.
echo 📋 2. CSV Data Analysis Tests
echo ----------------------------------------

echo.
echo Test: Customer Data Analysis
echo Command:
echo curl -X POST "%API_BASE%/worker/upload" ^
  -F "agent_name=gemini_csv_analyst" ^
  -F "input=Analyze this customer data and provide insights about customer segments, spending patterns, and business recommendations" ^
  -F "config_path=%CONFIG_PATH%" ^
  -F "files=@customer_data.csv"

echo.
echo Test: Sales Data Analysis
echo Command:
echo curl -X POST "%API_BASE%/worker/upload" ^
  -F "agent_name=gemini_csv_analyst" ^
  -F "input=Analyze this sales data to identify trends, top-performing products, and regional performance. Provide actionable business insights." ^
  -F "config_path=%CONFIG_PATH%" ^
  -F "files=@sample_sales_data.csv"

echo.
echo Test: Custom CSV Analysis
echo Command:
echo curl -X POST "%API_BASE%/worker/upload" ^
  -F "agent_name=gemini_csv_analyst" ^
  -F "input=Perform a comprehensive analysis of this dataset. Include data quality assessment, statistical insights, and recommendations for data visualization." ^
  -F "config_path=%CONFIG_PATH%" ^
  -F "files=@your_data.csv"

echo.
echo 📋 3. Image Analysis Tests
echo ----------------------------------------

echo.
echo Test: General Image Analysis
echo Command:
echo curl -X POST "%API_BASE%/worker/upload" ^
  -F "agent_name=gemini_image_analyzer" ^
  -F "input=Analyze this image and describe what you see in detail. Include any text, objects, people, or activities visible." ^
  -F "config_path=%CONFIG_PATH%" ^
  -F "files=@image.jpg"

echo.
echo Test: Chart/Graph Analysis
echo Command:
echo curl -X POST "%API_BASE%/worker/upload" ^
  -F "agent_name=gemini_image_analyzer" ^
  -F "input=This image contains a chart or graph. Please extract the data, analyze the trends, and provide insights about what the visualization shows." ^
  -F "config_path=%CONFIG_PATH%" ^
  -F "files=@chart.png"

echo.
echo Test: OCR Text Extraction
echo Command:
echo curl -X POST "%API_BASE%/worker/upload" ^
  -F "agent_name=gemini_image_analyzer" ^
  -F "input=Extract all text from this image and organize it in a readable format. Also describe the layout and context of the text." ^
  -F "config_path=%CONFIG_PATH%" ^
  -F "files=@document_image.jpg"

echo.
echo 📋 4. Multimodal Analysis Tests
echo ----------------------------------------

echo.
echo Test: Combined CSV and Image Analysis
echo Command:
echo curl -X POST "%API_BASE%/worker/upload" ^
  -F "agent_name=gemini_multimodal_agent" ^
  -F "input=Analyze both the CSV data and the image. Compare the data insights with what you see in the image and provide a comprehensive analysis." ^
  -F "config_path=%CONFIG_PATH%" ^
  -F "files=@data.csv" ^
  -F "files=@related_chart.png"

echo.
echo Test: Multiple Image Analysis
echo Command:
echo curl -X POST "%API_BASE%/worker/upload" ^
  -F "agent_name=gemini_multimodal_agent" ^
  -F "input=Compare and analyze these multiple images. Identify similarities, differences, and relationships between them." ^
  -F "config_path=%CONFIG_PATH%" ^
  -F "files=@image1.jpg" ^
  -F "files=@image2.jpg" ^
  -F "files=@image3.jpg"

echo.
echo 📋 5. Supervised Multi-Agent Tests
echo ----------------------------------------

echo.
echo Test: Complex Analysis Task
echo Command:
echo curl -X POST "%API_BASE%/query" ^
  -H "Content-Type: application/json" ^
  -d "{\"input\": \"Create a comprehensive business intelligence report analyzing customer behavior, sales trends, and market opportunities based on available data.\", \"config_path\": \"%CONFIG_PATH%\"}"

echo.
echo Test: Data-Driven Decision Making
echo Command:
echo curl -X POST "%API_BASE%/query" ^
  -H "Content-Type: application/json" ^
  -d "{\"input\": \"Analyze our business data to identify the top 3 strategic opportunities for growth and provide detailed recommendations with supporting evidence.\", \"config_path\": \"%CONFIG_PATH%\"}"

echo.
echo 📋 6. Health Check and System Status
echo ----------------------------------------

echo.
echo Test: API Health Check
echo Command:
echo curl -X GET "%API_BASE%/health"

echo.
echo Test: System Configuration Check
echo Command:
echo curl -X POST "%API_BASE%/worker" ^
  -H "Content-Type: application/json" ^
  -d "{\"agent_name\": \"gemini_test_agent\", \"input\": \"What model are you running on and what are your current capabilities?\", \"config_path\": \"%CONFIG_PATH%\"}"

echo.
echo 📝 Usage Instructions:
echo 1. Start the FastAPI server: uvicorn api:app --reload
echo 2. Ensure your GOOGLE_API_KEY is set in the .env file
echo 3. Copy and paste the curl commands above to test different scenarios
echo 4. Replace file paths (@file.csv, @image.jpg) with your actual files
echo 5. Modify the input prompts to match your specific use cases

echo.
echo 📁 Required Files for Testing:
echo - customer_data.csv (provided in repository)
echo - sample_sales_data.csv (provided in repository)
echo - Any image files (.jpg, .png, .webp, .gif)
echo - Any CSV files with your data

echo.
echo 🔧 Troubleshooting:
echo - If you get 'Connection refused': Start the FastAPI server first
echo - If you get 'Agent not found': Check the agent_name in your request
echo - If you get 'File not found': Ensure file paths are correct
echo - If you get 'Rate limit exceeded': Wait a moment and try again

echo.
echo ✅ Ready to test Google Gemini integration!

pause
