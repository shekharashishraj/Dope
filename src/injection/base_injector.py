"""Base injector class for all injection methods."""
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class BaseInjector(ABC):
    """Base class for all injection methods."""
    
    def __init__(self):
        """Initialize base injector."""
        self._tex_package_cache: Dict[str, bool] = {}
    
    @abstractmethod
    def inject(
        self,
        tex_content: str,
        perturbations: List[Dict[str, Any]],
        questions: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply injections to LaTeX content.
        
        Args:
            tex_content: Original LaTeX content
            perturbations: List of perturbation mappings
            questions: List of question data
        
        Returns:
            Tuple of (modified_tex, metadata)
        """
        pass
    
    def _read_tex(self, path: Path) -> str:
        """Read LaTeX file with encoding fallback."""
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1")
    
    def _insert_in_preamble(self, tex: str, snippet: str) -> str:
        """Insert snippet in LaTeX preamble (before \\begin{document})."""
        match = re.search(r"\\begin\{document\}", tex)
        if not match:
            return snippet + "\n" + tex
        insert_at = match.start()
        return tex[:insert_at] + snippet + "\n" + tex[insert_at:]
    
    def _escape_tex(self, value: str) -> str:
        """Escape special LaTeX characters."""
        replacements = {
            "\\": r"\textbackslash{}",
            "{": r"\{",
            "}": r"\}",
            "#": r"\#",
            "%": r"\%",
            "&": r"\&",
            "_": r"\_",
            "^": r"\^{}",
            "~": r"\~{}",
        }
        return "".join(replacements.get(ch, ch) for ch in value)
    
    def _find_question_stem_in_tex(
        self, 
        tex_content: str, 
        stem_text: str
    ) -> Optional[Tuple[int, int]]:
        """
        Find question stem text in LaTeX content.
        
        Returns:
            Tuple of (start_pos, end_pos) or None if not found
        """
        # Try exact match first
        index = tex_content.find(stem_text)
        if index != -1:
            return (index, index + len(stem_text))
        
        # Convert stem_text underscores to LaTeX escaped format
        # latex_stem_text might have "___________" but LaTeX has "\\_\\_\\_..."
        stem_escaped = stem_text.replace('_', '\\_')
        index = tex_content.find(stem_escaped)
        if index != -1:
            return (index, index + len(stem_escaped))
        
        # Try finding by unique substring (avoiding underscores)
        # Extract a unique phrase from the stem that doesn't include underscores
        words = stem_text.split()
        # Find a phrase of 3-5 words that's likely unique
        for phrase_len in range(5, 2, -1):
            for i in range(len(words) - phrase_len + 1):
                phrase = ' '.join(words[i:i+phrase_len])
                # Skip if phrase contains underscores
                if '_' in phrase:
                    continue
                # Try to find this phrase in LaTeX
                phrase_pos = tex_content.find(phrase)
                if phrase_pos != -1:
                    # Found the phrase, now try to find the full stem around it
                    # Search backwards and forwards from phrase position
                    search_start = max(0, phrase_pos - 200)
                    search_end = min(len(tex_content), phrase_pos + len(phrase) + 200)
                    search_area = tex_content[search_start:search_end]
                    
                    # Try to find stem in this area with flexible underscore matching
                    # Create a pattern that matches the stem but allows any number of underscores
                    stem_parts = stem_text.split("'")
                    if len(stem_parts) >= 2:
                        # Look for the structure: "The correct answer to '...' is '...'"
                        before_quotes = stem_parts[0]  # "The correct answer to "
                        in_quotes = stem_parts[1] if len(stem_parts) > 1 else ""  # The part with underscores
                        after_quotes = "'".join(stem_parts[2:]) if len(stem_parts) > 2 else ""  # " is 'Freenet'."
                        
                        # Find before_quotes and after_quotes in search_area
                        before_pos = search_area.find(before_quotes)
                        if before_pos != -1:
                            # Look for after_quotes after a reasonable distance
                            after_search_start = before_pos + len(before_quotes)
                            after_pos = search_area.find(after_quotes, after_search_start)
                            if after_pos != -1:
                                # Found the structure, return the range
                                actual_start = search_start + before_pos
                                actual_end = search_start + after_pos + len(after_quotes)
                                return (actual_start, actual_end)
        
        # Try with normalized whitespace
        normalized_stem = re.sub(r'\s+', ' ', stem_text.strip())
        normalized_stem_escaped = normalized_stem.replace('_', '\\_')
        normalized_tex = re.sub(r'\s+', ' ', tex_content)
        
        index = normalized_tex.find(normalized_stem)
        if index != -1:
            return (index, index + len(normalized_stem))
        
        index = normalized_tex.find(normalized_stem_escaped)
        if index != -1:
            return (index, index + len(normalized_stem_escaped))
        
        return None
    
    def _get_first_valid_perturbation(
        self, 
        perturbations: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get the first valid perturbation mapping."""
        if not perturbations:
            return None
        
        # For now, just return the first one
        # In the future, we could add validation logic
        return perturbations[0]

