"""File discovery and I/O operations for the pipeline."""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from .latex_parser import get_question_latex_stem, parse_latex_questions


class FileHandler:
    """Handles file discovery, loading, and saving operations."""
    
    def __init__(self, input_dir: str = "output", output_suffix: str = "_perturbation"):
        """
        Initialize file handler.
        
        Args:
            input_dir: Input directory containing JSON files
            output_suffix: Suffix to add to output filenames
        """
        self.input_dir = Path(input_dir)
        self.output_suffix = output_suffix
    
    def discover_json_files(self) -> List[Tuple[Path, Path, Path]]:
        """
        Discover all JSON files in the output directory structure.
        
        Returns:
            List of tuples: (json_file_path, latex_file_path, output_dir_path)
        """
        json_files = []
        
        # Recursively find all JSON_output directories
        for json_output_dir in self.input_dir.rglob("JSON_output"):
            # Find all JSON files in this directory
            for json_file in json_output_dir.glob("*_doc_*.json"):
                # Get the corresponding LaTeX file path from JSON metadata
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    latex_file_path = None
                    if 'file_paths' in data and 'latex_file' in data['file_paths']:
                        latex_path_str = data['file_paths']['latex_file']
                        # Handle both Windows and Unix path separators
                        latex_path_str = latex_path_str.replace('\\', '/')
                        latex_file_path = self.input_dir.parent / latex_path_str
                    
                    # Create output directory path (JSON_output_perturbation)
                    output_dir = json_output_dir.parent / f"JSON_output{self.output_suffix}"
                    
                    json_files.append((json_file, latex_file_path, output_dir))
                except Exception as e:
                    print(f"Warning: Could not process {json_file}: {e}")
                    continue
        
        return json_files
    
    def load_json_file(self, json_file_path: Path) -> Dict[str, Any]:
        """
        Load and parse a JSON file.
        
        Args:
            json_file_path: Path to JSON file
        
        Returns:
            Parsed JSON data
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_latex_stem_for_question(
        self, 
        latex_file_path: Optional[Path], 
        question_number: int
    ) -> Optional[str]:
        """
        Get LaTeX stem text for a specific question.
        
        Args:
            latex_file_path: Path to LaTeX file (can be None)
            question_number: Question number
        
        Returns:
            LaTeX stem text or None if not found
        """
        if latex_file_path is None or not latex_file_path.exists():
            return None
        
        return get_question_latex_stem(str(latex_file_path), question_number)
    
    def create_output_directory(self, output_dir: Path):
        """
        Create output directory if it doesn't exist.
        
        Args:
            output_dir: Output directory path
        """
        output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_perturbed_json(
        self, 
        output_dir: Path, 
        original_json_path: Path, 
        perturbed_data: Dict[str, Any]
    ) -> Path:
        """
        Save perturbed JSON data to output directory.
        
        Args:
            output_dir: Output directory path
            original_json_path: Original JSON file path
            perturbed_data: JSON data with perturbations added
        
        Returns:
            Path to saved file
        """
        self.create_output_directory(output_dir)
        
        # Generate output filename
        original_name = original_json_path.stem
        output_filename = f"{original_name}{self.output_suffix}.json"
        output_path = output_dir / output_filename
        
        # Save JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(perturbed_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def is_already_processed(self, output_dir: Path, original_json_path: Path) -> bool:
        """
        Check if a file has already been processed.
        
        Args:
            output_dir: Output directory path
            original_json_path: Original JSON file path
        
        Returns:
            True if output file exists
        """
        original_name = original_json_path.stem
        output_filename = f"{original_name}{self.output_suffix}.json"
        output_path = output_dir / output_filename
        return output_path.exists()

