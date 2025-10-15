@echo off
REM Test script for the v1/query endpoint with file uploads

echo Testing v1/query endpoint with visiting card extractor
echo ========================================================

REM Replace these paths with actual image files you want to test with
set IMAGE_PATH1=C:\path\to\your\first\card.jpg
set IMAGE_PATH2=C:\path\to\your\second\card.jpg

REM Ensure the API server is running before executing this script
curl --location "http://localhost:8000/v1/query" ^
  --form "question=Extract complete data including company research" ^
  --form "config_name=visiting_card_extractor.yaml" ^
  --form "file=@%IMAGE_PATH1%" ^
  --form "file=@%IMAGE_PATH2%"

echo.
echo Test complete
pause
