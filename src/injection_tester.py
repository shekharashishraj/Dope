"""Test script for injection methods on 2 documents."""
import json
import sys
from pathlib import Path
from typing import List
from .injection.orchestrator import InjectionOrchestrator


def find_perturbation_files(limit: int = 2) -> List[Path]:
    """Find perturbation JSON files."""
    output_dir = Path("output")
    json_files = []
    
    for json_file in output_dir.rglob("*_perturbation.json"):
        json_files.append(json_file)
        if len(json_files) >= limit:
            break
    
    return json_files


def main():
    """Test injection methods on 2 documents."""
    print("=" * 80)
    print("IntegrityShield Injection Methods Tester")
    print("=" * 80)
    
    # Find 2 perturbation files
    print("\n[1/4] Finding perturbation JSON files...")
    perturbation_files = find_perturbation_files(limit=2)
    
    if len(perturbation_files) < 2:
        print(f"ERROR: Found only {len(perturbation_files)} perturbation files. Need at least 2.")
        sys.exit(1)
    
    print(f"Found {len(perturbation_files)} files:")
    for f in perturbation_files:
        print(f"  - {f}")
    
    # Initialize orchestrator
    print("\n[2/4] Initializing injection orchestrator...")
    orchestrator = InjectionOrchestrator(output_dir=Path("output"))
    
    # Test all 5 methods
    methods = ["icw", "dual_layer", "font_attack", "icw_dual_layer", "icw_font_attack"]
    print(f"\n[3/4] Testing {len(methods)} injection methods on {len(perturbation_files)} documents...")
    print(f"Methods: {', '.join(methods)}")
    
    all_results = {}
    
    for i, json_file in enumerate(perturbation_files, 1):
        print(f"\n--- Processing Document {i}/{len(perturbation_files)}: {json_file.name} ---")
        
        try:
            results = orchestrator.process_document(
                perturbation_json_path=json_file,
                methods=methods,
                compile_pdf=True
            )
            
            all_results[json_file.name] = results
            
            # Print summary
            print(f"  Document ID: {results['docid']}")
            for method_name, method_result in results['methods'].items():
                status = "✓" if method_result.get('success') else "✗"
                print(f"  {status} {method_name}: ", end="")
                if method_result.get('success'):
                    print("SUCCESS")
                    if 'pdf_compilation' in method_result:
                        pdf_success = method_result['pdf_compilation'].get('success', False)
                        print(f"      PDF: {'✓ Compiled' if pdf_success else '✗ Failed'}")
                else:
                    print(f"FAILED - {method_result.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"  ✗ ERROR processing {json_file.name}: {e}")
            all_results[json_file.name] = {"error": str(e)}
    
    # Final summary
    print("\n" + "=" * 80)
    print("[4/4] Final Summary")
    print("=" * 80)
    
    total_tests = len(perturbation_files) * len(methods)
    successful_tests = 0
    successful_pdfs = 0
    
    for doc_name, doc_results in all_results.items():
        if 'error' in doc_results:
            continue
        
        print(f"\n{doc_name}:")
        for method_name, method_result in doc_results.get('methods', {}).items():
            if method_result.get('success'):
                successful_tests += 1
                if method_result.get('pdf_compilation', {}).get('success'):
                    successful_pdfs += 1
                    print(f"  ✓ {method_name}: LaTeX + PDF")
                else:
                    print(f"  ✓ {method_name}: LaTeX only (PDF failed)")
            else:
                print(f"  ✗ {method_name}: Failed")
    
    print(f"\nResults: {successful_tests}/{total_tests} methods successful")
    print(f"PDFs: {successful_pdfs}/{total_tests} compiled successfully")
    
    # Save results to JSON
    results_file = Path("injection_test_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    if successful_tests == total_tests:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠ {total_tests - successful_tests} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

