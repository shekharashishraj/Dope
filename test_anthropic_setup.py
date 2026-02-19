#!/usr/bin/env python3
"""Test script to verify Anthropic setup."""
import os
import sys

if not os.getenv("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
    print("Please set it before running the evaluation:")
    print("  export ANTHROPIC_API_KEY='your-key-here'")
    sys.exit(1)

print("✓ ANTHROPIC_API_KEY is set")
print("✓ Ready to run Anthropic evaluation")
