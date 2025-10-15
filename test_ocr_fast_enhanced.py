"""
Test suite for the enhanced OCR fast endpoint with card IDs and metadata tracking.

This test file validates:
1. Card ID generation and uniqueness
2. Metadata tracking of file references per card
3. Response structure compliance with expected format
4. Error handling and edge cases
"""

import asyncio
import io
import json
from typing import Dict, Any, List
from PIL import Image
import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from api import app


class TestOCRFastEndpointEnhanced:
    """Test suite for enhanced OCR fast endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_image_bytes(self):
        """Generate sample image bytes for testing."""
        # Create a simple test image
        img = Image.new('RGB', (300, 200), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    def test_response_structure_with_card_ids(self, client, sample_image_bytes):
        """Test that response includes card IDs for each card."""
        # Create test files
        files = [
            ("files", ("card1_front.jpg", sample_image_bytes, "image/jpeg")),
            ("files", ("card1_back.jpg", sample_image_bytes, "image/jpeg")),
        ]
        
        response = client.post(
            "/ocr/fast",
            files=files,
            data={
                "model": "gemini/gemini-flash-latest",
                "temperature": 0.1
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        
        # Verify response structure
        assert "success" in result
        assert "structured_cards" in result
        assert "meta" in result
        assert "total_images" in result
        assert "timestamp" in result
        
        # Verify structured cards have card IDs
        structured_cards = result["structured_cards"]
        if structured_cards:
            for card in structured_cards:
                assert "cardid" in card, f"Card missing 'cardid' field: {card}"
                assert card["cardid"].startswith("card_"), f"Card ID format incorrect: {card['cardid']}"
    
    def test_card_id_uniqueness(self, client, sample_image_bytes):
        """Test that each card gets a unique card ID."""
        # Create multiple test files
        files = [
            ("files", ("card1.jpg", sample_image_bytes, "image/jpeg")),
            ("files", ("card2.jpg", sample_image_bytes, "image/jpeg")),
            ("files", ("card3.jpg", sample_image_bytes, "image/jpeg")),
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
        result = response.json()
        
        structured_cards = result.get("structured_cards", [])
        if structured_cards:
            card_ids = [card["cardid"] for card in structured_cards]
            # Check uniqueness
            assert len(card_ids) == len(set(card_ids)), f"Duplicate card IDs found: {card_ids}"
    
    def test_meta_field_structure(self, client, sample_image_bytes):
        """Test that meta field has correct structure mapping card IDs to files."""
        files = [
            ("files", ("card1_front.jpg", sample_image_bytes, "image/jpeg")),
            ("files", ("card1_back.jpg", sample_image_bytes, "image/jpeg")),
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
        result = response.json()
        
        # Verify meta field exists
        assert "meta" in result
        meta = result["meta"]
        assert isinstance(meta, list), f"Meta should be a list, got {type(meta)}"
        
        # Verify meta structure
        if meta:
            for meta_entry in meta:
                assert isinstance(meta_entry, dict), f"Meta entry should be dict, got {type(meta_entry)}"
                # Each entry should have exactly one key (the card_id)
                assert len(meta_entry) == 1, f"Meta entry should have one key, got {len(meta_entry)}"
                
                card_id = list(meta_entry.keys())[0]
                assert card_id.startswith("card_"), f"Card ID should start with 'card_', got {card_id}"
                
                refs_data = meta_entry[card_id]
                assert "Refs" in refs_data, f"Meta entry missing 'Refs' field"
                assert isinstance(refs_data["Refs"], list), f"Refs should be a list"
    
    def test_meta_matches_card_ids(self, client, sample_image_bytes):
        """Test that card IDs in meta match card IDs in structured_cards."""
        files = [
            ("files", ("card1.jpg", sample_image_bytes, "image/jpeg")),
            ("files", ("card2.jpg", sample_image_bytes, "image/jpeg")),
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
        result = response.json()
        
        # Extract card IDs from structured_cards
        structured_cards = result.get("structured_cards", [])
        card_ids_in_cards = {card["cardid"] for card in structured_cards}
        
        # Extract card IDs from meta
        meta = result.get("meta", [])
        card_ids_in_meta = set()
        for meta_entry in meta:
            card_ids_in_meta.update(meta_entry.keys())
        
        # Verify they match
        assert card_ids_in_cards == card_ids_in_meta, (
            f"Card IDs mismatch. In cards: {card_ids_in_cards}, In meta: {card_ids_in_meta}"
        )
    
    def test_file_references_in_meta(self, client, sample_image_bytes):
        """Test that meta includes references to the source files."""
        filenames = ["card1_front.jpg", "card1_back.jpg"]
        files = [
            ("files", (filename, sample_image_bytes, "image/jpeg"))
            for filename in filenames
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
        result = response.json()
        
        meta = result.get("meta", [])
        if meta:
            # Check that at least one meta entry has file references
            has_refs = False
            for meta_entry in meta:
                card_id = list(meta_entry.keys())[0]
                refs = meta_entry[card_id]["Refs"]
                if refs:
                    has_refs = True
                    # Verify refs are from our uploaded files
                    for ref in refs:
                        assert ref in filenames, f"Unexpected file reference: {ref}"
            
            # At least one card should have file references
            assert has_refs, "No cards have file references in meta"
    
    def test_empty_files_error(self, client):
        """Test that endpoint returns error when no files are provided."""
        response = client.post(
            "/ocr/fast",
            data={
                "model": "gemini/gemini-flash-latest",
                "temperature": 0.1
            }
        )
        
        # Should return 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"
    
    def test_response_timing_fields(self, client, sample_image_bytes):
        """Test that response includes timing information."""
        files = [
            ("files", ("card1.jpg", sample_image_bytes, "image/jpeg")),
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
        result = response.json()
        
        # Verify timing fields
        assert "total_processing_time" in result
        assert "summarization_time" in result
        assert isinstance(result["total_processing_time"], (int, float))
        assert isinstance(result["summarization_time"], (int, float))
        assert result["total_processing_time"] >= 0
        assert result["summarization_time"] >= 0
    
    def test_reference_output_format(self, client, sample_image_bytes):
        """Test that output matches the reference format provided in requirements."""
        files = [
            ("files", ("olivia_card.jpg", sample_image_bytes, "image/jpeg")),
            ("files", ("joseph_card.jpg", sample_image_bytes, "image/jpeg")),
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
        result = response.json()
        
        # Verify top-level structure matches reference
        required_fields = [
            "success", "message", "structured_cards", "meta",
            "total_images", "successful_count", "failed_count",
            "total_processing_time", "summarization_time",
            "model_used", "timestamp"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Verify structured_cards format
        structured_cards = result["structured_cards"]
        if structured_cards:
            # Check first card has expected fields
            card = structured_cards[0]
            expected_card_fields = ["cardid", "name", "role", "company", "phone", "email", "address", "website"]
            for field in ["cardid"]:  # cardid is mandatory
                assert field in card, f"Card missing required field: {field}"
        
        # Verify meta format
        meta = result["meta"]
        assert isinstance(meta, list)
        if meta:
            meta_entry = meta[0]
            assert isinstance(meta_entry, dict)
            # Should have structure: {card_id: {Refs: [filenames]}}
            card_id = list(meta_entry.keys())[0]
            assert "Refs" in meta_entry[card_id]
            assert isinstance(meta_entry[card_id]["Refs"], list)


def test_summarize_visiting_cards_function():
    """Test the summarize_visiting_cards function directly."""
    from api import summarize_visiting_cards
    
    # Mock OCR results
    mock_ocr_results = [
        {
            "filename": "card1_front.jpg",
            "success": True,
            "extracted_text": "NAME: John Doe\\nROLE: CEO\\nCOMPANY: Tech Corp\\nPHONE: 123-456-7890\\nEMAIL: john@techcorp.com",
            "processing_time": 1.0
        },
        {
            "filename": "card1_back.jpg",
            "success": True,
            "extracted_text": "ADDRESS: 123 Main St\\nWEBSITE: www.techcorp.com",
            "processing_time": 1.0
        }
    ]
    
    # Run the function
    result = asyncio.run(summarize_visiting_cards(
        ocr_results=mock_ocr_results,
        model="gemini/gemini-flash-latest",
        temperature=0.0
    ))
    
    # Verify result structure
    assert "success" in result
    assert "structured_cards" in result
    assert "meta" in result
    
    # If successful, verify cards have IDs
    if result["success"] and result["structured_cards"]:
        for card in result["structured_cards"]:
            assert "cardid" in card
            assert card["cardid"].startswith("card_")
        
        # Verify meta has entries
        assert len(result["meta"]) == len(result["structured_cards"])


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
