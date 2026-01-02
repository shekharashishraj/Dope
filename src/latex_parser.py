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
    questions = parse_latex_questions_from_content(latex_content)
    return questions.get(question_number)


def parse_latex_questions_from_content(latex_content: str) -> Dict[int, str]:
    """
    Parse LaTeX content and extract all question stems, indexed by question number.
    Uses a simple but reliable approach: find all \item at the top level of enumerate blocks.
    """
    questions = {}
    
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
        
        # Find all \item entries in this section
        # We'll filter to only top-level items by checking depth
        all_items = list(re.finditer(r'\\item', section_content))
        
        items = []
        for item_match in all_items:
            item_pos = item_match.start()
            
            # Count depth: \begin{enumerate} - \end{enumerate} before this position
            before = section_content[:item_pos]
            depth = before.count('\\begin{enumerate}') - before.count('\\end{enumerate}')
            
            if depth == 1:  # Inside exactly one enumerate (the top-level one)
                # Extract text from this item
                item_start = item_pos + len('\\item')
                # Skip whitespace
                while item_start < len(section_content) and section_content[item_start].isspace():
                    item_start += 1
                
                # Find end: next \item at same depth, or \end{enumerate} at depth 1
                item_end = len(section_content)
                
                # Look for next item at depth 1
                for next_item in all_items:
                    if next_item.start() > item_pos:
                        next_pos = next_item.start()
                        before_next = section_content[:next_pos]
                        next_depth = before_next.count('\\begin{enumerate}') - before_next.count('\\end{enumerate}')
                        if next_depth == 1:
                            item_end = next_pos
                            break
                
                # Extract text (stop at nested \begin{enumerate} which is options)
                item_text = section_content[item_start:item_end]
                
                # Remove nested enumerate content (options for MCQ)
                nested_begin = item_text.find('\\begin{enumerate}')
                if nested_begin != -1:
                    item_text = item_text[:nested_begin]
                
                # Clean up
                item_text = item_text.strip()
                # Remove "True or False:" prefix
                item_text = re.sub(r'^True or False:\s*', '', item_text, flags=re.IGNORECASE)
                # Normalize whitespace
                item_text = re.sub(r'\s+', ' ', item_text)
                item_text = item_text.rstrip('\\ \n')
                
                if item_text and len(item_text) > 5:
                    items.append(item_text)
        
        # Assign question numbers
        for item_text in items:
            questions[current_question] = item_text
            current_question += 1
    
    return questions


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
    
    return parse_latex_questions_from_content(latex_content)


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
