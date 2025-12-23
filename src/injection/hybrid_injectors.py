"""Hybrid injection methods combining ICW with other methods."""
from pathlib import Path
from typing import Dict, List, Any, Tuple
from .icw_injector import ICWInjector
from .dual_layer_injector import DualLayerInjector
from .font_attack_injector import FontAttackInjector
from ..models.perturbation import PerturbationMapping, Question


class ICWDualLayerInjector:
    """Hybrid: ICW + Dual Layer."""
    
    def __init__(self, config=None):
        """Initialize hybrid injector."""
        self.config = config
        self.icw_injector = ICWInjector(config=config)
        self.dual_layer_injector = DualLayerInjector(config=config)
    
    def inject(
        self,
        tex_content: str,
        perturbations: List[PerturbationMapping],
        questions: List[Question]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply ICW first, then Dual Layer.
        
        Args:
            tex_content: Original LaTeX content
            perturbations: List of perturbation mappings
            questions: List of question data
        
        Returns:
            Tuple of (modified_tex, metadata)
        """
        # Step 1: Apply ICW
        icw_tex, icw_metadata = self.icw_injector.inject(
            tex_content, perturbations, questions
        )
        
        # Step 2: Apply Dual Layer to ICW-modified LaTeX
        final_tex, dual_metadata = self.dual_layer_injector.inject(
            icw_tex, perturbations, questions
        )
        
        metadata = {
            "method": "icw_dual_layer",
            "icw": icw_metadata,
            "dual_layer": dual_metadata
        }
        
        return final_tex, metadata


class ICWFontAttackInjector:
    """Hybrid: ICW + Font Attack."""
    
    def __init__(self, fonts_dir=None, config=None):
        """Initialize hybrid injector."""
        self.config = config
        self.icw_injector = ICWInjector(config=config)
        self.font_attack_injector = FontAttackInjector(fonts_dir=fonts_dir)
    
    def inject(
        self,
        tex_content: str,
        perturbations: List[PerturbationMapping],
        questions: List[Question]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply ICW first, then Font Attack.
        
        Args:
            tex_content: Original LaTeX content
            perturbations: List of perturbation mappings
            questions: List of question data
        
        Returns:
            Tuple of (modified_tex, metadata)
        """
        # Step 1: Apply ICW
        icw_tex, icw_metadata = self.icw_injector.inject(
            tex_content, perturbations, questions
        )
        
        # Step 2: Apply Font Attack to ICW-modified LaTeX
        final_tex, font_metadata = self.font_attack_injector.inject(
            icw_tex, perturbations, questions
        )
        
        metadata = {
            "method": "icw_font_attack",
            "icw": icw_metadata,
            "font_attack": font_metadata
        }
        
        return final_tex, metadata
    
    def generate_fonts(self, output_fonts_dir: Path) -> List[Path]:
        """
        Generate fonts for font attack component.
        
        Args:
            output_fonts_dir: Directory where fonts should be generated
        
        Returns:
            List of generated font paths
        """
        if hasattr(self.font_attack_injector, 'generate_fonts'):
            return self.font_attack_injector.generate_fonts(output_fonts_dir)
        return []

