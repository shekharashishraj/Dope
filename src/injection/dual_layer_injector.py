"""Dual Layer injection method - Visual overlay using \\duallayerbox."""
import re
from typing import Dict, List, Any, Tuple
from .base_injector import BaseInjector


class DualLayerInjector(BaseInjector):
    """Applies visual overlay using dual layer box macro."""
    
    MACRO_DEFINITION = r"""
% --- latex-dual-layer macros (auto-generated) ---
\newlength{\dlboxwidth}
\newlength{\dlboxheight}
\newlength{\dlboxdepth}
\newcommand{\duallayerbox}[2]{%
  \begingroup
  \settowidth{\dlboxwidth}{\strut #1}%
  \settoheight{\dlboxheight}{\strut #1}%
  \settodepth{\dlboxdepth}{\strut #1}%
  \ifdim\dlboxwidth=0pt
    \settowidth{\dlboxwidth}{#2}%
  \fi
  \raisebox{0pt}[\dlboxheight][\dlboxdepth]{%
    \makebox[\dlboxwidth][l]{\resizebox{\dlboxwidth}{!}{\strut #2}}%
  }%
  \endgroup
}
% --- end latex-dual-layer macros ---
""".strip()
    
    PACKAGE_DEPENDENCIES = ("graphicx", "calc", "xcolor")
    
    def inject(
        self,
        tex_content: str,
        perturbations: List[Dict[str, Any]],
        questions: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply dual layer visual overlay to LaTeX.
        
        Args:
            tex_content: Original LaTeX content
            perturbations: List of perturbation mappings
            questions: List of question data
        
        Returns:
            Tuple of (modified_tex, metadata)
        """
        mutated_tex = tex_content
        
        # Add required packages
        mutated_tex = self._ensure_packages(mutated_tex)
        
        # Add dual layer macros
        if "\\duallayerbox" not in mutated_tex:
            mutated_tex = self._insert_in_preamble(mutated_tex, self.MACRO_DEFINITION)
        
        # Apply replacements
        replacements = []
        metadata_replacements = []
        
        for question in questions:
            question_number = question.get('question_number')
            
            if not question_number:
                continue
            
            # Apply ALL valid perturbations (not just the first one)
            # This allows k=3 mappings per question to all be applied
            question_perturbations = question.get('perturbations', [])
            
            # Use latex_stem_text from first perturbation or question
            # All perturbations for the same question should share the same stem
            latex_stem_text = None
            if question_perturbations:
                latex_stem_text = question_perturbations[0].get('latex_stem_text', '')
            if not latex_stem_text:
                latex_stem_text = question.get('stem_text', '')
            
            if not latex_stem_text:
                continue
            
            # Find latex_stem_text in LaTeX (this should match exactly)
            stem_pos = self._find_question_stem_in_tex(mutated_tex, latex_stem_text)
            if not stem_pos:
                # Try with "True or False: " prefix
                prefixed_stem = f"True or False: {latex_stem_text}"
                stem_pos = self._find_question_stem_in_tex(mutated_tex, prefixed_stem)
                if stem_pos:
                    # Adjust to skip the prefix
                    prefix_len = len("True or False: ")
                    stem_pos = (stem_pos[0] + prefix_len, stem_pos[1])
            
            if not stem_pos:
                continue
            
            stem_start, stem_end = stem_pos
            
            # Process each perturbation for this question
            for perturbation in question_perturbations:
                original_substring = perturbation.get('original_substring', '')
                replacement_substring = perturbation.get('replacement_substring', '')
                start_pos = perturbation.get('start_pos', -1)
                end_pos = perturbation.get('end_pos', -1)
                
                if not original_substring or not replacement_substring:
                    continue
                
                # Use positions from perturbation (relative to latex_stem_text)
                # Verify the positions are valid
                if start_pos >= 0 and end_pos > start_pos and end_pos <= len(latex_stem_text):
                    # Use exact positions from perturbation
                    abs_start = stem_start + start_pos
                    abs_end = stem_start + end_pos
                    
                    # Verify the substring matches
                    actual_substring = mutated_tex[abs_start:abs_end]
                    if actual_substring != original_substring:
                        # Try to find it manually if positions don't match
                        stem_in_tex = mutated_tex[stem_start:stem_end]
                        substring_index = stem_in_tex.find(original_substring)
                        if substring_index != -1:
                            abs_start = stem_start + substring_index
                            abs_end = abs_start + len(original_substring)
                        else:
                            continue
                else:
                    # Fallback: find substring manually
                    stem_in_tex = mutated_tex[stem_start:stem_end]
                    substring_index = stem_in_tex.find(original_substring)
                    if substring_index == -1:
                        # Try normalized search
                        normalized_stem = re.sub(r'\s+', ' ', stem_in_tex)
                        normalized_orig = re.sub(r'\s+', ' ', original_substring)
                        substring_index = normalized_stem.find(normalized_orig)
                        if substring_index != -1:
                            # Approximate position
                            substring_index = stem_in_tex.find(original_substring[:5]) if len(original_substring) >= 5 else -1
                    
                    if substring_index == -1:
                        continue
                    
                    abs_start = stem_start + substring_index
                    abs_end = abs_start + len(original_substring)
                
                # Create dual layer replacement using \duallayerbox macro
                # Format: \duallayerbox{original}{replacement}
                # The macro displays #2 (replacement) visually
                # Then image overlays from original PDF will cover it with #1 (original)
                # Result: Visual shows original, text layer has replacement
                escaped_original = self._escape_tex(original_substring)
                escaped_replacement = self._escape_tex(replacement_substring)
                
                replacement = f"\\duallayerbox{{{escaped_original}}}{{{escaped_replacement}}}"
                
                replacements.append((abs_start, abs_end, replacement))
                metadata_replacements.append({
                    "question_number": question_number,
                    "original": original_substring,
                    "replacement": replacement_substring,
                    "position": (abs_start, abs_end)
                })
        
        # Apply replacements in reverse order to preserve positions
        replacements.sort(key=lambda x: x[0], reverse=True)
        for start, end, replacement in replacements:
            mutated_tex = mutated_tex[:start] + replacement + mutated_tex[end:]
        
        metadata = {
            "replacements_count": len(replacements),
            "replacements": metadata_replacements,
            "method": "dual_layer"
        }
        
        return mutated_tex, metadata
    
    def _ensure_packages(self, tex: str) -> str:
        """Ensure required packages are included."""
        for package in self.PACKAGE_DEPENDENCIES:
            if f"\\usepackage{{{package}}}" not in tex:
                tex = self._insert_in_preamble(tex, f"\\usepackage{{{package}}}")
        return tex

