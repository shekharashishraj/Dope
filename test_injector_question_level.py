#!/usr/bin/env python3
"""
Test script to verify injectors handle question-level substitutions correctly.
Tests both question stem substitutions and option substitutions.
"""

import sys
from pathlib import Path
from src.injection.dual_layer_injector import DualLayerInjector
from src.models.perturbation import Question, PerturbationMapping, QuestionType

def test_question_level_substitution():
    """Test substitution in question stem."""
    print("=" * 80)
    print("TEST 1: Question-Level Substitution (in stem)")
    print("=" * 80)
    
    # Create a simple LaTeX with a question
    tex_content = r"""
\documentclass{article}
\begin{document}
\begin{enumerate}
\item Suppose your model is overfitting. Which method should you use?
\begin{enumerate}
    \item Increase training data
    \item Decrease model complexity
\end{enumerate}
\end{enumerate}
\end{document}
"""
    
    # Create perturbation that targets the question stem
    perturbation = PerturbationMapping(
        question_index=1,
        latex_stem_text="Suppose your model is overfitting. Which method should you use?",
        original_substring="overfitting",
        replacement_substring="underfitting",
        start_pos=25,
        end_pos=36,
        target_wrong_answer="A",
        reasoning="Test"
    )
    
    question = Question(
        question_number=1,
        question_type=QuestionType.MCQ,
        stem_text="Suppose your model is overfitting. Which method should you use?",
        options={"A": "Increase training data", "B": "Decrease model complexity"},
        gold_answer="B",
        perturbations=[perturbation]
    )
    
    injector = DualLayerInjector()
    modified_tex, metadata = injector.inject(tex_content, [perturbation], [question])
    
    # Check if substitution was applied
    if "\\duallayerbox{overfitting}{underfitting}" in modified_tex:
        print("✓ PASS: Question-level substitution applied correctly")
        print(f"  Found: \\duallayerbox{{overfitting}}{{underfitting}}")
        return True
    else:
        print("✗ FAIL: Question-level substitution not found")
        print(f"  Modified LaTeX snippet: {modified_tex[200:400]}")
        return False


def test_option_level_substitution():
    """Test substitution in options."""
    print("\n" + "=" * 80)
    print("TEST 2: Option-Level Substitution")
    print("=" * 80)
    
    tex_content = r"""
\documentclass{article}
\begin{document}
\begin{enumerate}
\item What is the best method?
\begin{enumerate}
    \item Increase training data
    \item Decrease model complexity
\end{enumerate}
\end{enumerate}
\end{document}
"""
    
    # Create perturbation that targets an option
    # The original_substring should be in the options, not the stem
    perturbation = PerturbationMapping(
        question_index=1,
        latex_stem_text="What is the best method?",
        original_substring="Increase training data",
        replacement_substring="Decrease training data",
        start_pos=0,  # Position relative to latex_stem_text (but substring is in options)
        end_pos=22,
        target_wrong_answer="A",
        reasoning="Test"
    )
    
    question = Question(
        question_number=1,
        question_type=QuestionType.MCQ,
        stem_text="What is the best method?",
        options={"A": "Increase training data", "B": "Decrease model complexity"},
        gold_answer="A",
        perturbations=[perturbation]
    )
    
    injector = DualLayerInjector()
    modified_tex, metadata = injector.inject(tex_content, [perturbation], [question])
    
    # Check if substitution was applied in options
    if "\\duallayerbox{Increase training data}{Decrease training data}" in modified_tex:
        print("✓ PASS: Option-level substitution applied correctly")
        print(f"  Found: \\duallayerbox{{Increase training data}}{{Decrease training data}}")
        return True
    else:
        print("✗ FAIL: Option-level substitution not found")
        print(f"  Replacements applied: {metadata.get('final_replacements_count', 0)}")
        # Check if it's in the modified tex
        if "Decrease training data" in modified_tex:
            print("  Note: Replacement text found but not in duallayerbox format")
        return False


def test_extraction_fallback():
    """Test that extraction fallback works when latex_stem_text is wrong."""
    print("\n" + "=" * 80)
    print("TEST 3: Extraction Fallback (incorrect latex_stem_text)")
    print("=" * 80)
    
    tex_content = r"""
\documentclass{article}
\begin{document}
\section*{Test}
\begin{enumerate}
\item Suppose your model is overfitting. Which method should you use?
\begin{enumerate}
    \item Increase training data
    \item Decrease model complexity
\end{enumerate}
\end{enumerate}
\end{document}
"""
    
    # Create perturbation with WRONG latex_stem_text
    perturbation = PerturbationMapping(
        question_index=1,
        latex_stem_text="WRONG TEXT",  # Wrong!
        original_substring="overfitting",
        replacement_substring="underfitting",
        start_pos=0,
        end_pos=11,
        target_wrong_answer="A",
        reasoning="Test"
    )
    
    question = Question(
        question_number=1,
        question_type=QuestionType.MCQ,
        stem_text="Suppose your model is overfitting. Which method should you use?",
        options={"A": "Increase training data", "B": "Decrease model complexity"},
        gold_answer="B",
        perturbations=[perturbation]
    )
    
    injector = DualLayerInjector()
    modified_tex, metadata = injector.inject(tex_content, [perturbation], [question])
    
    # Should still work because of extraction fallback
    if "\\duallayerbox{overfitting}{underfitting}" in modified_tex:
        print("✓ PASS: Extraction fallback worked - found correct stem despite wrong JSON")
        return True
    else:
        print("✗ FAIL: Extraction fallback did not work")
        print(f"  Replacements: {metadata.get('final_replacements_count', 0)}")
        return False


if __name__ == "__main__":
    results = []
    results.append(test_question_level_substitution())
    results.append(test_option_level_substitution())
    results.append(test_extraction_fallback())
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)

