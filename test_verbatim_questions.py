#!/usr/bin/env python3
"""
Test script to upload PDFs and ask GPT to read questions VERBATIM and answer.
Stores outputs for inspection.
Usage: python3 test_verbatim_questions.py <pdf_path>
"""

import argparse
import sys
import time
import json
from pathlib import Path
from openai import OpenAI
import os
from datetime import datetime

def upload_and_ask_verbatim(pdf_path: Path, model: str = "gpt-4o", output_dir: Path = None):
    """Upload PDF via v1/files and ask to read questions verbatim and answer."""
    
    # Get API key - try environment variable first, then config file
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Try loading from config
        try:
            from src.config import Config
            config = Config()
            api_key = config.openai.api_key
        except Exception as e:
            pass
    
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found. Set OPENAI_API_KEY environment variable or configure in config.yaml")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    # Create output directory
    if output_dir is None:
        output_dir = Path("test_verbatim_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prompt asking to read questions verbatim
    prompt = """Please read this document carefully and answer ALL questions that appear in it.

CRITICAL INSTRUCTIONS:
1. Read each question VERBATIM (word-for-word) exactly as it appears in the document
2. Copy the question text EXACTLY as written
3. Then provide your answer

For each question, provide:
1. The question number (if numbered)
2. The question text VERBATIM as it appears in the document (copy it exactly)
3. Your answer

Format your response clearly, indicating which question you are answering. If the document contains multiple choice questions, please indicate your selected option (A, B, C, D, etc.). If it contains True/False questions, please clearly state True or False. For long-form questions, provide a comprehensive answer."""
    
    print(f"📄 PDF: {pdf_path}")
    print(f"❓ Task: Read questions VERBATIM and answer")
    print(f"🤖 Model: {model}")
    print(f"📁 Output: {output_dir}")
    print("-" * 60)
    
    file_id = None
    try:
        # Step 1: Upload PDF via v1/files endpoint
        print("\n[1/3] Uploading PDF via v1/files endpoint...")
        with open(pdf_path, 'rb') as pdf_file:
            file_response = client.files.create(
                file=pdf_file,
                purpose="user_data"
            )
        file_id = file_response.id
        print(f"✓ Uploaded: {file_id}")
        
        # Step 2: Wait for file to be processed
        print("\n[2/3] Waiting for file to be processed...")
        max_wait = 60
        wait_time = 0
        while wait_time < max_wait:
            file_status = client.files.retrieve(file_id)
            if file_status.status == "processed":
                print("✓ File processed")
                break
            time.sleep(2)
            wait_time += 2
            if wait_time % 10 == 0:
                print(f"  Still processing... ({wait_time}s)")
        
        if wait_time >= max_wait:
            print("⚠ Warning: File processing timeout")
        
        # Step 3: Ask question via chat completions
        print("\n[3/3] Asking question via chat completions...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "file",
                            "file": {
                                "file_id": file_id
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            timeout=120,
            max_tokens=4000,
            temperature=0  # Deterministic output
        )
        
        answer = response.choices[0].message.content
        
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{pdf_path.stem}_verbatim_{timestamp}.json"
        
        output_data = {
            "pdf_path": str(pdf_path),
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": answer,
            "file_id": file_id,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print("📝 ANSWER:")
        print("=" * 60)
        print(answer)
        print("=" * 60)
        print(f"\n💾 Saved to: {output_file}")
        
        return answer, output_file
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        # Cleanup: Delete uploaded file
        if file_id:
            try:
                client.files.delete(file_id)
                print(f"\n✓ Cleaned up: Deleted file {file_id}")
            except Exception as e:
                print(f"\n⚠ Warning: Failed to delete file {file_id}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Test PDF upload with verbatim question reading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_verbatim_questions.py document.pdf
  python3 test_verbatim_questions.py document.pdf --model gpt-4o-mini
  python3 test_verbatim_questions.py document.pdf --output custom_output_dir
        """
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to PDF file to upload"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Model to use (default: gpt-4o)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: test_verbatim_outputs)"
    )
    
    args = parser.parse_args()
    
    # Validate PDF path
    if not args.pdf_path.exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    if not args.pdf_path.is_file():
        print(f"ERROR: Not a file: {args.pdf_path}")
        sys.exit(1)
    
    # Run test
    upload_and_ask_verbatim(args.pdf_path, args.model, args.output)


if __name__ == "__main__":
    main()

