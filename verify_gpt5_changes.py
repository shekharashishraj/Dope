"""Simple verification script for GPT-5.1 changes."""
import yaml
from pathlib import Path

def verify_changes():
    """Verify that GPT-5.1 changes are correctly implemented."""
    print("Verifying GPT-5.1 Implementation Changes")
    print("=" * 80)
    
    # Check config.yaml
    print("\n1. Checking config.yaml...")
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print(f"   ✗ Config file not found: {config_path}")
        return False
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    model = config_data.get("openai", {}).get("model", "")
    reasoning_effort = config_data.get("openai", {}).get("reasoning_effort")
    verbosity = config_data.get("openai", {}).get("verbosity")
    
    print(f"   Model: {model}")
    print(f"   Reasoning effort: {reasoning_effort}")
    print(f"   Verbosity: {verbosity}")
    
    if model == "gpt-5.1-2025-11-13":
        print(f"   ✓ Model correctly set to gpt-5.1-2025-11-13")
    else:
        print(f"   ✗ Model should be 'gpt-5.1-2025-11-13', got '{model}'")
        return False
    
    if reasoning_effort and verbosity:
        print(f"   ✓ GPT-5.1 parameters configured")
    else:
        print(f"   ⚠ GPT-5.1 parameters may be missing")
    
    # Check config.py model
    print("\n2. Checking src/models/config.py...")
    config_py = Path("src/models/config.py")
    if not config_py.exists():
        print(f"   ✗ Config model file not found: {config_py}")
        return False
    
    content = config_py.read_text()
    
    checks = [
        ("reasoning_effort", "reasoning_effort" in content),
        ("verbosity", "verbosity" in content),
        ("is_gpt5_model", "is_gpt5_model" in content),
    ]
    
    all_passed = True
    for name, passed in checks:
        if passed:
            print(f"   ✓ {name} found")
        else:
            print(f"   ✗ {name} not found")
            all_passed = False
    
    # Check openai_client.py
    print("\n3. Checking src/openai_client.py...")
    client_py = Path("src/openai_client.py")
    if not client_py.exists():
        print(f"   ✗ OpenAI client file not found: {client_py}")
        return False
    
    content = client_py.read_text()
    
    checks = [
        ("_is_gpt5_model", "_is_gpt5_model" in content),
        ("reasoning", '"reasoning"' in content or "'reasoning'" in content),
        ("verbosity", '"verbosity"' in content or "'verbosity'" in content),
        ("GPT-5.1 conditional", "if self._is_gpt5_model()" in content),
    ]
    
    for name, passed in checks:
        if passed:
            print(f"   ✓ {name} found")
        else:
            print(f"   ✗ {name} not found")
            all_passed = False
    
    # Check response_collector.py
    print("\n4. Checking src/detection/response_collector.py...")
    collector_py = Path("src/detection/response_collector.py")
    if not collector_py.exists():
        print(f"   ✗ Response collector file not found: {collector_py}")
        return False
    
    content = collector_py.read_text()
    
    checks = [
        ("_is_gpt5_model", "_is_gpt5_model" in content),
        ("reasoning_effort", "reasoning_effort" in content),
        ("verbosity", "verbosity" in content),
    ]
    
    for name, passed in checks:
        if passed:
            print(f"   ✓ {name} found")
        else:
            print(f"   ✗ {name} not found")
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ All verification checks passed!")
        return True
    else:
        print("✗ Some verification checks failed")
        return False

if __name__ == "__main__":
    success = verify_changes()
    exit(0 if success else 1)

