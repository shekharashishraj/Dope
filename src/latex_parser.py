"""LaTeX parsing utilities to extract question stems."""
import re
from typing import Dict, Optional, List
from pathlib import Path


def extract_question_stem_from_latex(latex_content: str, question_number: int) -> Optional[str]:
    """
    Extract the LaTeX stem text for a specific question number from LaTeX content.
    
    Args:
        latex_content: Full LaTeX document content
        question_number: Question number to extract
    
    Returns:
        LaTeX stem text for the question, or None if not found
    """
    # Pattern to match \item followed by question text
    # This handles both numbered and unnumbered enumerate environments
    # We need to match the question number in the enumerate counter
    
    # First, try to find questions in enumerate environments
    # Pattern: \item followed by optional "True or False:" and then the question text
    # The question number might be set by \setcounter{enumi}{X} or by the enumerate label
    
    # Look for \setcounter{enumi}{X} to understand the starting number
    counter_match = re.search(r'\\setcounter\{enumi\}\{(\d+)\}', latex_content)
    start_number = int(counter_match.group(1)) if counter_match else 1
    
    # Find all \item entries in enumerate environments
    # We need to match the section context (Multiple Choice, True/False, Long Form)
    
    # Split by sections to find the right context
    sections = re.split(r'\\section\*\{([^}]+)\}', latex_content)
    
    # Find items in the relevant section
    # For now, we'll search through all items and match by relative position
    # This is a simplified approach - in practice, we might need more sophisticated parsing
    
    # Pattern to match \item followed by question text
    # Handle both "True or False:" prefix and plain questions
    item_pattern = r'\\item\s+(?:True or False:\s+)?(.*?)(?=\\item|\\end\{enumerate\}|$)'
    
    items = re.findall(item_pattern, latex_content, re.DOTALL)
    
    # Calculate which item index corresponds to our question number
    # Account for the counter offset
    item_index = question_number - start_number
    
    if 0 <= item_index < len(items):
        stem_text = items[item_index].strip()
        # Clean up the stem text - remove extra whitespace and newlines
        stem_text = re.sub(r'\s+', ' ', stem_text)
        # Remove trailing backslashes and newlines
        stem_text = stem_text.rstrip('\\ \n')
        return stem_text
    
    # Alternative approach: search by question number in the text
    # Some questions might have the number embedded
    number_pattern = rf'\\item.*?{question_number}[\.\)]\s*(.*?)(?=\\item|\\end|$)'
    match = re.search(number_pattern, latex_content, re.DOTALL)
    if match:
        stem_text = match.group(1).strip()
        stem_text = re.sub(r'\s+', ' ', stem_text)
        stem_text = stem_text.rstrip('\\ \n')
        return stem_text
    
    return None


def parse_latex_questions(latex_file_path: str) -> Dict[int, str]:
    """
    Parse LaTeX file and extract all question stems, indexed by question number.
    
    Args:
        latex_file_path: Path to LaTeX file
    
    Returns:
        Dictionary mapping question numbers to LaTeX stem text
    """
    latex_path = Path(latex_file_path)
    if not latex_path.exists():
        return {}
    
    with open(latex_path, 'r', encoding='utf-8') as f:
        latex_content = f.read()
    
    questions = {}
    
    # Find all \item entries and extract their content
    # We'll number them sequentially based on their order in enumerate environments
    
    # Split by sections
    section_pattern = r'\\section\*\{([^}]+)\}'
    sections = re.split(section_pattern, latex_content)
    
    current_question = 1
    
    for i in range(1, len(sections), 2):  # Skip section names, get content
        section_content = sections[i + 1] if i + 1 < len(sections) else ""
        
        # Check for counter reset
        counter_match = re.search(r'\\setcounter\{enumi\}\{(\d+)\}', section_content)
        if counter_match:
            current_question = int(counter_match.group(1)) + 1
        # If no counter, continue from previous question number
        
        # Find all top-level \item entries
        # Pattern: \item followed by text until \begin{enumerate} (nested) or next \item or \end{enumerate}
        # Use a more careful pattern that stops at nested enumerates
        item_pattern = r'\\item\s+(?:True or False:\s+)?(.*?)(?=\\begin\{enumerate\}|\\item\s+|\\end\{enumerate\}|$)'
        items = re.findall(item_pattern, section_content, re.DOTALL)
        
        for item_text in items:
            stem_text = item_text.strip()
            # Remove "True or False:" prefix if it wasn't caught by the pattern
            stem_text = re.sub(r'^True or False:\s*', '', stem_text, flags=re.IGNORECASE)
            # Clean up whitespace
            stem_text = re.sub(r'\s+', ' ', stem_text)
            stem_text = stem_text.rstrip('\\ \n')
            if stem_text:
                questions[current_question] = stem_text
                current_question += 1
    
    return questions


def get_question_latex_stem(latex_file_path: str, question_number: int) -> Optional[str]:
    """
    Get LaTeX stem text for a specific question.
    
    Args:
        latex_file_path: Path to LaTeX file
        question_number: Question number
    
    Returns:
        LaTeX stem text or None if not found
    """
    questions = parse_latex_questions(latex_file_path)
    return questions.get(question_number)

