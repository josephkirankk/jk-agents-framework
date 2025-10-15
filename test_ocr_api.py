"""
Test suite for standalone OCR API.

Tests the new lightweight ocr_api.py application.
"""

import io
from PIL import Image
from fastapi.testclient import TestClient

# Import the OCR API app
from ocr_api import app

client = TestClient(app)


def create_test_image():
    """Create a simple test image."""
    img = Image.new('RGB', (300, 200), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ocr-api"
    assert data["status"] == "running"
    assert "endpoints" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ocr-api"


def test_ocr_fast_with_single_image():
    """Test OCR fast endpoint with a single image."""
    image_bytes = create_test_image()
    
    response = client.post(
        "/ocr/fast",
        files=[("files", ("test_card.jpg", image_bytes, "image/jpeg"))],
        data={
            "model": "gemini/gemini-flash-latest",
            "temperature": 0.1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "success" in data
    assert "structured_cards" in data
    assert "meta" in data
    assert "total_images" in data
    assert data["total_images"] == 1


def test_ocr_fast_with_multiple_images():
    """Test OCR fast endpoint with multiple images."""
    image_bytes = create_test_image()
    
    files = [
        ("files", ("card1.jpg", image_bytes, "image/jpeg")),
        ("files", ("card2.jpg", image_bytes, "image/jpeg")),
    ]
    
    response = client.post(
        "/ocr/fast",
        files=files,
        data={
            "model": "gemini/gemini-flash-latest",
            "temperature": 0.1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_images"] == 2


def test_ocr_fast_no_files():
    """Test OCR fast endpoint with no files (should fail)."""
    response = client.post(
        "/ocr/fast",
        data={
            "model": "gemini/gemini-flash-latest",
            "temperature": 0.1
        }
    )
    
    # Should return 422 validation error or 400 bad request
    assert response.status_code in [400, 422]


def test_ocr_response_has_card_ids():
    """Test that OCR response includes card IDs."""
    image_bytes = create_test_image()
    
    response = client.post(
        "/ocr/fast",
        files=[("files", ("test_card.jpg", image_bytes, "image/jpeg"))],
        data={"model": "gemini/gemini-flash-latest"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that meta field exists
    assert "meta" in data
    assert isinstance(data["meta"], list)
    
    # If cards were structured, they should have IDs
    if data["structured_cards"]:
        for card in data["structured_cards"]:
            assert "cardid" in card
            assert card["cardid"].startswith("card_")


def test_ocr_response_format():
    """Test that OCR response matches expected format."""
    image_bytes = create_test_image()
    
    response = client.post(
        "/ocr/fast",
        files=[("files", ("test.jpg", image_bytes, "image/jpeg"))],
        data={"model": "gemini/gemini-flash-latest"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Required fields
    required_fields = [
        "success", "message", "structured_cards", "meta",
        "total_images", "successful_count", "failed_count",
        "total_processing_time", "summarization_time",
        "model_used", "timestamp"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
