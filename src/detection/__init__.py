"""Detection module for IntegrityShield - tests perturbed PDFs against MLLMs."""
from .response_collector import ResponseCollector
from .signature_matcher import SignatureMatcher
from .metrics_calculator import MetricsCalculator

__all__ = [
    "ResponseCollector",
    "SignatureMatcher",
    "MetricsCalculator",
]

