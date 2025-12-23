#!/usr/bin/env python3
"""
Simple test script to upload a PDF via v1/files API and ask questions.
Usage: python3 test_pdf_upload.py <pdf_path> [question]
"""

import argparse
import sys
import time
from pathlib import Path
from openai import OpenAI
import os

def upload_and_ask(pdf_path: Path, question: str = None, model: str = "gpt-4o", answer_all: bool = False):
    """Upload PDF via v1/files and ask a question."""
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    # Default question if not provided
    if answer_all:
        question = """Please read this document carefully and answer ALL questions that appear in it.

IMPORTANT: Read each question VERBATIM (word-for-word) exactly as it appears in the document, then provide your answer.

For each question, provide:
1. The question number (if numbered)
2. The question text VERBATIM as it appears in the document
3. Your answer

Format your response clearly, indicating which question you are answering. If the document contains multiple choice questions, please indicate your selected option (A, B, C, D, etc.). If it contains True/False questions, please clearly state True or False. For long-form questions, provide a comprehensive answer."""
    elif question is None:
        question = "Please read this document and answer: What is the main topic of this document? Provide a brief summary."
    
    print(f"📄 PDF: {pdf_path}")
    if answer_all:
        print(f"❓ Task: Answer ALL questions in the document")
    else:
        print(f"❓ Question: {question}")
    print(f"🤖 Model: {model}")
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
                            "text": question
                        }
                    ]
                }
            ],
            timeout=120,  # Longer timeout for answering all questions
            max_tokens=4000  # More tokens for multiple answers
        )
        
        answer = response.choices[0].message.content
        print("\n" + "=" * 60)
        print("📝 ANSWER:")
        print("=" * 60)
        print(answer)
        print("=" * 60)
        
        return answer
        
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
        description="Test PDF upload via OpenAI v1/files API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_pdf_upload.py document.pdf
  python3 test_pdf_upload.py document.pdf "What are the key points?"
  python3 test_pdf_upload.py document.pdf --all
  python3 test_pdf_upload.py document.pdf --all --model gpt-4o-mini
        """
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to PDF file to upload"
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=None,
        help="Question to ask about the PDF (default: asks for summary). Use --all to answer all questions."
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Model to use (default: gpt-4o)"
    )
    parser.add_argument(
        "--all",
        "--answer-all",
        dest="answer_all",
        action="store_true",
        help="Answer ALL questions in the document"
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
    upload_and_ask(args.pdf_path, args.question, args.model, args.answer_all)


if __name__ == "__main__":
    main()

