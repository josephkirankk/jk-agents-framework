# Run standalone Multimodal API server with proper environment
# This script activates the virtual environment and runs the Multimodal API server on Windows

# Ensure script is run from the correct directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Check if virtual environment exists
if (-not (Test-Path ".\.venv")) {
    Write-Host "❌ Virtual environment not found!"
    Write-Host "Creating new virtual environment with uv..."
    python -m pip install uv
    uv venv -p python .venv
    
    Write-Host "Installing dependencies..."
    .\.venv\Scripts\Activate.ps1
    uv pip install -r requirements.txt
    uv pip install litellm python-dotenv Pillow langchain-core fastapi uvicorn
} else {
    Write-Host "✅ Found virtual environment"
}

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..."
.\.venv\Scripts\Activate.ps1

# Check if .env exists
if (-not (Test-Path ".\.env")) {
    Write-Host "⚠️ No .env file found. Creating from .env.example (please update with real API keys)..."
    if (Test-Path ".\.env.example") {
        Copy-Item .\.env.example .\.env
        Write-Host "✅ Created .env file from .env.example"
    } else {
        Write-Host "❌ No .env.example file found. Creating minimal .env..."
        @"
# API Keys for LiteLLM providers
# OPENAI_API_KEY=your-api-key
# AZURE_API_KEY=your-api-key
# AZURE_API_BASE=https://your-endpoint.openai.azure.com/
# AZURE_API_VERSION=2023-05-15
# GOOGLE_API_KEY=your-api-key
"@ | Out-File -FilePath .\.env -Encoding utf8
    }
    Write-Host "⚠️ Please edit the .env file with your actual API keys before using"
}

# Start the API server
Write-Host "🚀 Starting Multimodal API server on port 8080..."
python multimodal_api.py
