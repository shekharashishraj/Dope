"""Test script to verify PDF upload functionality with OpenAI API."""
import argparse
import base64
import logging
import sys
from pathlib import Path
from openai import OpenAI
import fitz  # PyMuPDF

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_file_upload(pdf_path: Path, api_key: str, model: str = "gpt-4o"):
    """Test 1: Upload PDF as file and reference it."""
    logger.info("=" * 80)
    logger.info("TEST 1: File Upload Method")
    logger.info("=" * 80)
    
    client = OpenAI(api_key=api_key)
    
    try:
        # Upload file
        with open(pdf_path, 'rb') as f:
            file_response = client.files.create(
                file=f,
                purpose="assistants"
            )
        file_id = file_response.id
        logger.info(f"✓ File uploaded: {file_id}")
        
        # Wait for processing
        import time
        max_wait = 60
        wait_time = 0
        while wait_time < max_wait:
            status = client.files.retrieve(file_id)
            if status.status == "processed":
                logger.info(f"✓ File processed")
                break
            time.sleep(2)
            wait_time += 2
        
        # Try to use it in chat completion
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What is the first question in this document? Answer it."},
                            {"type": "file", "file_id": file_id}
                        ]
                    }
                ]
            )
            logger.info(f"✓ API call successful")
            logger.info(f"Response: {response.choices[0].message.content[:200]}...")
            return True, response.choices[0].message.content
        except Exception as e:
            logger.error(f"✗ API call failed: {e}")
            return False, str(e)
        finally:
            # Cleanup
            try:
                client.files.delete(file_id)
                logger.info(f"✓ File deleted")
            except:
                pass
                
    except Exception as e:
        logger.error(f"✗ File upload failed: {e}")
        return False, str(e)


def test_pdf_to_images(pdf_path: Path, api_key: str, model: str = "gpt-4o"):
    """Test 2: Convert PDF to images and send as base64."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: PDF to Images Method (Base64)")
    logger.info("=" * 80)
    
    client = OpenAI(api_key=api_key)
    
    try:
        # Convert PDF to images
        pdf_doc = fitz.open(pdf_path)
        images = []
        for page_num in range(min(3, len(pdf_doc))):  # Test first 3 pages
            page = pdf_doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
            img_data = pix.tobytes("png")
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            images.append(img_base64)
        pdf_doc.close()
        logger.info(f"✓ Converted PDF to {len(images)} images")
        
        # Send first image to test
        if images:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "What is the first question in this document? Answer it."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{images[0]}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            logger.info(f"✓ API call successful")
            logger.info(f"Response: {response.choices[0].message.content[:200]}...")
            return True, response.choices[0].message.content
        else:
            logger.error("✗ No images generated")
            return False, "No images"
            
    except Exception as e:
        logger.error(f"✗ PDF to images failed: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def test_multiple_images(pdf_path: Path, api_key: str, model: str = "gpt-4o"):
    """Test 3: Send multiple PDF pages as images."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Multiple Images Method")
    logger.info("=" * 80)
    
    client = OpenAI(api_key=api_key)
    
    try:
        # Convert PDF to images
        pdf_doc = fitz.open(pdf_path)
        image_urls = []
        for page_num in range(min(3, len(pdf_doc))):  # First 3 pages
            page = pdf_doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            image_urls.append(f"data:image/png;base64,{img_base64}")
        pdf_doc.close()
        logger.info(f"✓ Converted PDF to {len(image_urls)} images")
        
        # Build content with multiple images
        content = [
            {"type": "text", "text": "Answer all questions in this document. Start with question 1."}
        ]
        for img_url in image_urls:
            content.append({
                "type": "image_url",
                "image_url": {"url": img_url}
            })
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=1000
        )
        logger.info(f"✓ API call successful")
        logger.info(f"Response: {response.choices[0].message.content[:300]}...")
        return True, response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"✗ Multiple images failed: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Test PDF upload methods with OpenAI")
    parser.add_argument("--pdf", type=str, required=True, help="Path to PDF file")
    parser.add_argument("--model", type=str, default="gpt-4o", help="Model to use")
    parser.add_argument("--api-key", type=str, help="OpenAI API key (or use OPENAI_API_KEY env var)")
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        sys.exit(1)
    
    api_key = args.api_key or None
    if not api_key:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not found. Set OPENAI_API_KEY or use --api-key")
            sys.exit(1)
    
    logger.info(f"Testing PDF: {pdf_path}")
    logger.info(f"Model: {args.model}")
    logger.info("")
    
    # Run tests
    results = {}
    
    # Test 1: File upload
    results['file_upload'] = test_file_upload(pdf_path, api_key, args.model)
    
    # Test 2: PDF to single image
    results['single_image'] = test_pdf_to_images(pdf_path, api_key, args.model)
    
    # Test 3: Multiple images
    results['multiple_images'] = test_multiple_images(pdf_path, api_key, args.model)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    for test_name, (success, result) in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{test_name}: {status}")
        if not success:
            logger.info(f"  Error: {result[:100]}")
    
    # Recommend best method
    if results['multiple_images'][0]:
        logger.info("\n✓ RECOMMENDED: Use multiple images method (Test 3)")
    elif results['single_image'][0]:
        logger.info("\n✓ RECOMMENDED: Use single image method (Test 2)")
    elif results['file_upload'][0]:
        logger.info("\n✓ RECOMMENDED: Use file upload method (Test 1)")
    else:
        logger.error("\n✗ All methods failed. Check API key and model support.")


if __name__ == "__main__":
    main()

