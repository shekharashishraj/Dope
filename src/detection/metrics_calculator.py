"""Step 3: Calculate detection metrics from matched responses."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculates detection metrics from matched responses."""
    
    def __init__(self):
        """Initialize metrics calculator."""
        pass
    
    def calculate_metrics(
        self,
        detection_results: List[Dict[str, Any]],
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Calculate overall detection metrics.
        
        Args:
            detection_results: List of detection results from signature matcher
            output_dir: Directory to save metrics
        
        Returns:
            Dictionary with calculated metrics
        """
        if not detection_results:
            logger.warning("No detection results provided")
            return {}
        
        total_questions = len(detection_results)
        
        # Count detections, refusals, false negatives (overall)
        detected_count = sum(1 for r in detection_results if r.get("detected", False))
        refused_count = sum(1 for r in detection_results if r.get("refused", False))
        not_detected_count = total_questions - detected_count - refused_count
        
        # Calculate rates (overall)
        detection_rate = (detected_count / total_questions * 100) if total_questions > 0 else 0.0
        refusal_rate = (refused_count / total_questions * 100) if total_questions > 0 else 0.0
        false_negative_rate = (not_detected_count / total_questions * 100) if total_questions > 0 else 0.0
        
        # Separate metrics by parsing method
        parsing_methods = ["llm_judge", "json_mode", "regex"]
        parsing_metrics = {}
        
        for method in parsing_methods:
            method_results = [r for r in detection_results if r.get("parsing_method") == method]
            if not method_results:
                continue
            
            method_total = len(method_results)
            method_detected = sum(1 for r in method_results if r.get("detected", False))
            method_refused = sum(1 for r in method_results if r.get("refused", False))
            method_not_detected = method_total - method_detected - method_refused
            
            method_detection_rate = (method_detected / method_total * 100) if method_total > 0 else 0.0
            method_refusal_rate = (method_refused / method_total * 100) if method_total > 0 else 0.0
            method_false_negative_rate = (method_not_detected / method_total * 100) if method_total > 0 else 0.0
            
            # Average confidence for detected cases
            method_detected_results = [r for r in method_results if r.get("detected", False)]
            method_avg_confidence = (
                sum(r.get("match_confidence", 0.0) for r in method_detected_results) / len(method_detected_results)
                if method_detected_results else 0.0
            )
            
            parsing_metrics[method] = {
                "total_questions": method_total,
                "detected": method_detected,
                "refused": method_refused,
                "not_detected": method_not_detected,
                "detection_rate": round(method_detection_rate, 2),
                "refusal_rate": round(method_refusal_rate, 2),
                "false_negative_rate": round(method_false_negative_rate, 2),
                "average_confidence": round(method_avg_confidence, 3)
            }
        
        # Breakdown by question type
        by_type = defaultdict(lambda: {"total": 0, "detected": 0, "refused": 0})
        for result in detection_results:
            q_type = result.get("question_type", "UNKNOWN")
            by_type[q_type]["total"] += 1
            if result.get("detected", False):
                by_type[q_type]["detected"] += 1
            if result.get("refused", False):
                by_type[q_type]["refused"] += 1
        
        # Calculate rates by type
        type_metrics = {}
        for q_type, counts in by_type.items():
            total = counts["total"]
            type_metrics[q_type] = {
                "total": total,
                "detected": counts["detected"],
                "refused": counts["refused"],
                "detection_rate": (counts["detected"] / total * 100) if total > 0 else 0.0,
                "refusal_rate": (counts["refused"] / total * 100) if total > 0 else 0.0
            }
        
        # Average confidence for detected cases
        detected_results = [r for r in detection_results if r.get("detected", False)]
        avg_confidence = (
            sum(r.get("match_confidence", 0.0) for r in detected_results) / len(detected_results)
            if detected_results else 0.0
        )
        
        metrics = {
            "summary": {
                "total_questions": total_questions,
                "detected": detected_count,
                "refused": refused_count,
                "not_detected": not_detected_count,
                "detection_rate": round(detection_rate, 2),
                "refusal_rate": round(refusal_rate, 2),
                "false_negative_rate": round(false_negative_rate, 2),
                "average_confidence": round(avg_confidence, 3)
            },
            "by_parsing_method": parsing_metrics,
            "by_question_type": type_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save metrics
        output_file = output_dir / "detection_metrics.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Calculated metrics: Detection Rate={detection_rate:.2f}%, Refusal Rate={refusal_rate:.2f}%")
        for method, method_metrics in parsing_metrics.items():
            logger.info(f"  {method}: Detection Rate={method_metrics['detection_rate']:.2f}% ({method_metrics['total_questions']} questions)")
        logger.info(f"Saved metrics to {output_file}")
        
        return metrics
    
    def generate_report(
        self,
        metrics: Dict[str, Any],
        detection_results: List[Dict[str, Any]],
        output_dir: Path
    ) -> Path:
        """
        Generate human-readable report.
        
        Args:
            metrics: Calculated metrics
            detection_results: Individual detection results
            output_dir: Directory to save report
        
        Returns:
            Path to report file
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("IntegrityShield Detection Report")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Summary
        summary = metrics.get("summary", {})
        report_lines.append("SUMMARY")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Questions: {summary.get('total_questions', 0)}")
        report_lines.append(f"Detected: {summary.get('detected', 0)} ({summary.get('detection_rate', 0):.2f}%)")
        report_lines.append(f"Refused: {summary.get('refused', 0)} ({summary.get('refusal_rate', 0):.2f}%)")
        report_lines.append(f"Not Detected: {summary.get('not_detected', 0)} ({summary.get('false_negative_rate', 0):.2f}%)")
        report_lines.append(f"Average Confidence: {summary.get('average_confidence', 0):.3f}")
        report_lines.append("")
        
        # By parsing method
        by_parsing = metrics.get("by_parsing_method", {})
        if by_parsing:
            report_lines.append("BREAKDOWN BY PARSING METHOD")
            report_lines.append("-" * 80)
            for method, method_metrics in sorted(by_parsing.items()):
                report_lines.append(f"\n{method.upper()}:")
                report_lines.append(f"  Total Questions: {method_metrics['total_questions']}")
                report_lines.append(f"  Detected: {method_metrics['detected']} ({method_metrics['detection_rate']:.2f}%)")
                report_lines.append(f"  Refused: {method_metrics['refused']} ({method_metrics['refusal_rate']:.2f}%)")
                report_lines.append(f"  Not Detected: {method_metrics['not_detected']} ({method_metrics['false_negative_rate']:.2f}%)")
                report_lines.append(f"  Average Confidence: {method_metrics['average_confidence']:.3f}")
            report_lines.append("")
        
        # By question type
        report_lines.append("BREAKDOWN BY QUESTION TYPE")
        report_lines.append("-" * 80)
        by_type = metrics.get("by_question_type", {})
        for q_type, type_metrics in sorted(by_type.items()):
            report_lines.append(f"\n{q_type}:")
            report_lines.append(f"  Total: {type_metrics['total']}")
            report_lines.append(f"  Detected: {type_metrics['detected']} ({type_metrics['detection_rate']:.2f}%)")
            report_lines.append(f"  Refused: {type_metrics['refused']} ({type_metrics['refusal_rate']:.2f}%)")
        report_lines.append("")
        
        # Sample results
        report_lines.append("SAMPLE DETECTION RESULTS")
        report_lines.append("-" * 80)
        for i, result in enumerate(detection_results[:10], 1):  # Show first 10
            q_num = result.get("question_number", "?")
            q_type = result.get("question_type", "?")
            detected = "✓" if result.get("detected", False) else "✗"
            refused = "REFUSED" if result.get("refused", False) else ""
            confidence = result.get("match_confidence", 0.0)
            reason = result.get("reason", "")
            
            report_lines.append(f"{i}. Question {q_num} ({q_type}): {detected} {refused}")
            if confidence > 0:
                report_lines.append(f"   Confidence: {confidence:.2f}")
            if reason:
                report_lines.append(f"   Reason: {reason}")
            report_lines.append("")
        
        if len(detection_results) > 10:
            report_lines.append(f"... and {len(detection_results) - 10} more results")
        
        report_text = "\n".join(report_lines)
        
        # Save report
        report_file = output_dir / "detection_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        # Also print to console
        print(report_text)
        
        logger.info(f"Generated report: {report_file}")
        
        return report_file

