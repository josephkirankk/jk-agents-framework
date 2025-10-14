"""
Image Compression Utility

Compresses images to reduce token usage for vision models while maintaining
quality for OCR tasks. Uses intelligent downscaling + quality search to meet
target size while preserving text legibility.
"""
import io
import logging
from typing import Tuple, Optional
from PIL import Image

log = logging.getLogger(__name__)

# Optimal settings for OCR quality vs size
MAX_DIMENSION = 1024      # Reduced from 1536 for more aggressive compression
TARGET_SIZE_KB = 25       # VERY aggressive - was 50KB, now 25KB (accounts for message history)
QUALITY_FLOOR = 40        # Minimum JPEG quality (still readable for OCR)
QUALITY_CEIL = 85         # Maximum JPEG quality (reduced from 92)
CHROMA_SUBSAMPLING = 2    # 4:2:0 subsampling (more aggressive, still OK for cards)


def _encode_jpeg_to_bytes(
    img: Image.Image,
    quality: int,
    progressive: bool = True,
    subsampling: int = CHROMA_SUBSAMPLING,
    optimize: bool = True,
) -> bytes:
    """Encode PIL image to JPEG in-memory and return bytes."""
    buf = io.BytesIO()
    # Strip metadata (exif=None) for smaller size and privacy
    img.save(
        buf,
        format="JPEG",
        quality=quality,
        progressive=progressive,
        subsampling=subsampling,
        optimize=optimize,
        exif=b"",  # Strip all EXIF data
    )
    return buf.getvalue()


def compress_image(
    image_bytes: bytes,
    max_dimension: int = MAX_DIMENSION,
    target_size_kb: int = TARGET_SIZE_KB,
    quality_floor: int = QUALITY_FLOOR,
    quality_ceil: int = QUALITY_CEIL,
    force_format: Optional[str] = None
) -> Tuple[bytes, str, dict]:
    """
    Compress an image for OCR with intelligent downscaling and quality search.
    
    Strategy (optimized for text legibility):
    1. Downscale first if needed (preserves text better than low quality)
    2. Binary search JPEG quality to meet target size
    3. Strip metadata for smaller size
    4. Use text-safe chroma subsampling (4:2:2)
    5. Never make file larger than original
    
    Args:
        image_bytes: Original image bytes
        max_dimension: Maximum width or height in pixels
        target_size_kb: Target max size in KB (will binary search quality)
        quality_floor: Minimum JPEG quality allowed
        quality_ceil: Maximum JPEG quality (starting point)
        force_format: Force output format ('JPEG' or 'PNG'), None for auto
        
    Returns:
        Tuple of (compressed_bytes, format, metadata_dict)
        
    Raises:
        ValueError: If image cannot be opened or processed
    """
    try:
        # Open and prepare image
        img = Image.open(io.BytesIO(image_bytes))
        original_format = img.format or "UNKNOWN"
        original_size = len(image_bytes)
        original_dimensions = img.size
        
        log.info(
            f"Compressing image: format={original_format}, "
            f"size={original_size:,} bytes ({original_size/1024:.1f} KB), "
            f"dimensions={original_dimensions}"
        )
        
        # Convert to RGB (JPEG-ready)
        img = img.convert("RGB")
        
        # Step 1: Downscale first (preserves text better than low quality)
        width, height = img.size
        needs_resize = width > max_dimension or height > max_dimension
        
        if needs_resize:
            # Calculate new dimensions maintaining aspect ratio
            scale = max_dimension / float(max(width, height))
            new_width = max(1, int(round(width * scale)))
            new_height = max(1, int(round(height * scale)))
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            log.info(f"Downscaled: {original_dimensions} -> {img.size}")
        else:
            log.info(f"No downscaling needed: {original_dimensions}")
        
        # Step 2: Binary search for optimal quality to meet target size
        target_bytes = int(target_size_kb * 1024)
        
        # Quick check: try high quality first
        data = _encode_jpeg_to_bytes(img, quality_ceil)
        
        if len(data) <= target_bytes:
            # High quality already fits target! Use it.
            best_q = quality_ceil
            best_data = data
            best_bytes = len(data)
            log.info(f"High quality (Q={quality_ceil}) already fits target: {best_bytes:,} <= {target_bytes:,} bytes")
        else:
            # Binary search for optimal quality
            lo, hi = quality_floor, quality_ceil
            best_bytes = None
            best_q = lo
            best_data = None
            
            while lo <= hi:
                mid = (lo + hi) // 2
                data = _encode_jpeg_to_bytes(img, mid)
                size = len(data)
                
                if size <= target_bytes:
                    # Fits! Try higher quality
                    best_q, best_data, best_bytes = mid, data, size
                    lo = mid + 1
                else:
                    # Too large, need lower quality
                    hi = mid - 1
            
            # If nothing fit, use floor quality
            if best_data is None:
                data = _encode_jpeg_to_bytes(img, quality_floor)
                best_q, best_data, best_bytes = quality_floor, data, len(data)
                log.warning(f"Could not meet target. Using Q={quality_floor}: {best_bytes:,} bytes")
            else:
                log.info(f"Found optimal quality Q={best_q}: {best_bytes:,} bytes (target: {target_bytes:,})")
        
        compressed_bytes = best_data
        compressed_size = best_bytes
        
        # Step 3: Safety check - never make file larger than original
        if compressed_size >= original_size:
            log.warning(
                f"Compression would increase size: {original_size:,} -> {compressed_size:,} bytes. "
                f"Using original image instead."
            )
            return image_bytes, original_format, {}
        
        # Calculate compression ratio
        compression_ratio = (1 - (compressed_size / original_size)) * 100
        
        metadata = {
            "original_format": original_format,
            "original_size_bytes": original_size,
            "original_dimensions": original_dimensions,
            "compressed_format": "JPEG",
            "compressed_size_bytes": compressed_size,
            "compressed_dimensions": img.size,
            "compression_ratio_percent": round(compression_ratio, 2),
            "resized": needs_resize,
            "quality_used": best_q,
            "target_size_kb": target_size_kb
        }
        
        log.info(
            f"✓ Compression successful: {original_size:,} -> {compressed_size:,} bytes "
            f"({compression_ratio:.1f}% reduction) | Q={best_q} | "
            f"{compressed_size/1024:.1f} KB (target: {target_size_kb} KB)"
        )
        
        return compressed_bytes, "JPEG", metadata
        
    except Exception as e:
        log.error(f"Image compression failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        raise ValueError(f"Failed to compress image: {e}")


def estimate_vision_tokens(image_bytes: bytes) -> int:
    """
    Estimate token usage for vision models (GPT-4o).
    
    GPT-4o vision token calculation:
    - Base64 encoding adds ~33% overhead
    - Tokens ≈ (width * height) / 750 for detail=high
    - Minimum 85 tokens per image
    
    Args:
        image_bytes: Image bytes
        
    Returns:
        Estimated token count
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        # GPT-4o tiles images into 512x512 tiles
        # Each tile costs ~170 tokens
        # Plus base cost of 85 tokens
        tiles_width = (width + 511) // 512
        tiles_height = (height + 511) // 512
        num_tiles = tiles_width * tiles_height
        
        estimated_tokens = 85 + (num_tiles * 170)
        
        log.debug(
            f"Token estimate: {width}x{height} = {num_tiles} tiles "
            f"≈ {estimated_tokens} tokens"
        )
        
        return estimated_tokens
        
    except Exception as e:
        log.warning(f"Could not estimate tokens: {e}")
        # Fallback rough estimate
        return len(image_bytes) // 100


def should_compress_image(
    image_bytes: bytes,
    size_threshold_kb: int = 100,
    dimension_threshold: int = 1536
) -> bool:
    """
    Determine if image should be compressed.
    
    Args:
        image_bytes: Image bytes
        size_threshold_kb: Compress if larger than this (KB)
        dimension_threshold: Compress if any dimension exceeds this
        
    Returns:
        True if compression recommended
    """
    size_kb = len(image_bytes) / 1024
    
    if size_kb > size_threshold_kb:
        return True
    
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        if width > dimension_threshold or height > dimension_threshold:
            return True
    except Exception:
        pass
    
    return False