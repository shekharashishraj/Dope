"""Prevention-specific metrics calculator.

For prevention mode, we calculate:
- Prevention success rate (refusals) = main metric
- Prevention failure rate (answers) = failure metric
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class PreventionMetricsCalculator:
    """Calculates prevention metrics - refusals are success."""
    
    def __init__(self):
        """Initialize prevention metrics calculator."""
        pass
    
    def calculate_metrics(
        self,
        prevention_results: List[Dict[str, Any]],
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Calculate prevention metrics.
        
        Args:
            prevention_results: List of prevention results from PreventionMatcher
            output_dir: Directory to save metrics
        
        Returns:
            Dictionary with calculated prevention metrics
        """
        if not prevention_results:
            logger.warning("No prevention results provided")
            return {}
        
        total_questions = len(prevention_results)
        
        # Count prevention successes (refusals) and failures (answers)
        prevention_success_count = sum(1 for r in prevention_results if r.get("prevention_success", False))
        prevention_failure_count = total_questions - prevention_success_count
        
        # Also track refusals and detections for reference
        refused_count = sum(1 for r in prevention_results if r.get("refused", False))
        detected_count = sum(1 for r in prevention_results if r.get("detected", False))
        
        # Calculate rates
        prevention_success_rate = (prevention_success_count / total_questions * 100) if total_questions > 0 else 0.0
        prevention_failure_rate = (prevention_failure_count / total_questions * 100) if total_questions > 0 else 0.0
        refusal_rate = (refused_count / total_questions * 100) if total_questions > 0 else 0.0
        detection_rate = (detected_count / total_questions * 100) if total_questions > 0 else 0.0
        
        # Separate metrics by parsing method
        parsing_methods = ["llm_judge", "json_mode", "regex"]
        parsing_metrics = {}
        
        for method in parsing_methods:
            method_results = [r for r in prevention_results if r.get("parsing_method") == method]
            if not method_results:
                continue
            
            method_total = len(method_results)
            method_success = sum(1 for r in method_results if r.get("prevention_success", False))
            method_failure = method_total - method_success
            
            method_success_rate = (method_success / method_total * 100) if method_total > 0 else 0.0
            method_failure_rate = (method_failure / method_total * 100) if method_total > 0 else 0.0
            
            parsing_metrics[method] = {
                "total_questions": method_total,
                "prevention_success": method_success,
                "prevention_failure": method_failure,
                "prevention_success_rate": round(method_success_rate, 2),
                "prevention_failure_rate": round(method_failure_rate, 2),
            }
        
        # Breakdown by question type
        by_type = defaultdict(lambda: {"total": 0, "success": 0, "failure": 0})
        for result in prevention_results:
            q_type = result.get("question_type", "UNKNOWN")
            by_type[q_type]["total"] += 1
            if result.get("prevention_success", False):
                by_type[q_type]["success"] += 1
            else:
                by_type[q_type]["failure"] += 1
        
        # Calculate rates by type
        type_metrics = {}
        for q_type, counts in by_type.items():
            total = counts["total"]
            type_metrics[q_type] = {
                "total": total,
                "prevention_success": counts["success"],
                "prevention_failure": counts["failure"],
                "prevention_success_rate": (counts["success"] / total * 100) if total > 0 else 0.0,
                "prevention_failure_rate": (counts["failure"] / total * 100) if total > 0 else 0.0,
            }
        
        # Breakdown by variant
        by_variant = defaultdict(lambda: {"total": 0, "success": 0, "failure": 0})
        for result in prevention_results:
            variant = result.get("variant") or "icw"
            by_variant[variant]["total"] += 1
            if result.get("prevention_success", False):
                by_variant[variant]["success"] += 1
            else:
                by_variant[variant]["failure"] += 1
        
        variant_metrics = {}
        for variant, counts in by_variant.items():
            total = counts["total"]
            variant_metrics[variant] = {
                "total": total,
                "prevention_success": counts["success"],
                "prevention_failure": counts["failure"],
                "prevention_success_rate": (counts["success"] / total * 100) if total > 0 else 0.0,
                "prevention_failure_rate": (counts["failure"] / total * 100) if total > 0 else 0.0,
            }
        
        # Breakdown by method
        by_method = defaultdict(lambda: {"total": 0, "success": 0, "failure": 0})
        for result in prevention_results:
            method = result.get("method", "unknown")
            by_method[method]["total"] += 1
            if result.get("prevention_success", False):
                by_method[method]["success"] += 1
            else:
                by_method[method]["failure"] += 1
        
        method_metrics = {}
        for method, counts in by_method.items():
            total = counts["total"]
            method_metrics[method] = {
                "total": total,
                "prevention_success": counts["success"],
                "prevention_failure": counts["failure"],
                "prevention_success_rate": (counts["success"] / total * 100) if total > 0 else 0.0,
                "prevention_failure_rate": (counts["failure"] / total * 100) if total > 0 else 0.0,
            }
        
        metrics = {
            "summary": {
                "total_questions": total_questions,
                "prevention_success": prevention_success_count,
                "prevention_failure": prevention_failure_count,
                "prevention_success_rate": round(prevention_success_rate, 2),
                "prevention_failure_rate": round(prevention_failure_rate, 2),
                "refusal_rate": round(refusal_rate, 2),  # Same as success rate, kept for clarity
                "detection_rate": round(detection_rate, 2),  # For reference (wrong answers given)
            },
            "by_parsing_method": parsing_metrics,
            "by_question_type": type_metrics,
            "by_variant": variant_metrics,
            "by_method": method_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save metrics
        output_file = output_dir / "prevention_metrics.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Calculated prevention metrics: Success Rate={prevention_success_rate:.2f}%, Failure Rate={prevention_failure_rate:.2f}%")
        for method, method_metrics in parsing_metrics.items():
            logger.info(f"  {method}: Success Rate={method_metrics['prevention_success_rate']:.2f}% ({method_metrics['total_questions']} questions)")
        logger.info(f"Saved metrics to {output_file}")
        
        return metrics
