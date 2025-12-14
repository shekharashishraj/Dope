"""PDF-level dual layer manipulation to create visual/text layer mismatch."""
import io
from pathlib import Path
from typing import Dict, List, Tuple, Any

try:
    from PyPDF2 import PdfReader, PdfWriter
    from PyPDF2.generic import ContentStream, NameObject, NumberObject, TextStringObject
    PDF_LIB_AVAILABLE = True
except ImportError:
    PDF_LIB_AVAILABLE = False


def apply_dual_layer_to_pdf(
    pdf_path: Path,
    output_path: Path,
    mappings: List[Dict[str, Any]]
) -> bool:
    """
    Apply dual-layer effect to PDF by manipulating text rendering.
    
    Args:
        pdf_path: Input PDF path
        output_path: Output PDF path
        mappings: List of mappings with 'original' and 'replacement' keys
    
    Returns:
        True if successful, False otherwise
    """
    if not PDF_LIB_AVAILABLE:
        return False
    
    if not pdf_path.exists():
        return False
    
    try:
        # Read PDF
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        
        # Build mapping pairs
        pairs = []
        for mapping in mappings:
            original = mapping.get('original', '')
            replacement = mapping.get('replacement', '')
            if original and replacement:
                pairs.append((original, replacement))
        
        if not pairs:
            # No mappings, just copy
            writer.write(output_path)
            return True
        
        # Process each page
        for page in reader.pages:
            try:
                content = ContentStream(page.get_contents(), reader)
                new_ops: List[Tuple[List[object], bytes]] = []
                
                for operands, operator in content.operations:
                    if operator == b"Tj" and operands and isinstance(operands[0], TextStringObject):
                        pdf_text = str(operands[0])
                        
                        # Normalize text for matching (remove extra spaces)
                        normalized_pdf = ' '.join(pdf_text.split())
                        
                        # Check if this text matches any mapping
                        replacement_text = None
                        matched_original = None
                        for orig, repl in pairs:
                            normalized_orig = ' '.join(orig.split())
                            # Try exact match first
                            if normalized_orig in normalized_pdf:
                                replacement_text = normalized_pdf.replace(normalized_orig, repl, 1)
                                matched_original = orig
                                break
                            # Try partial match (for cases where PDF has extra formatting)
                            elif orig.strip() in normalized_pdf:
                                replacement_text = normalized_pdf.replace(orig.strip(), repl, 1)
                                matched_original = orig
                                break
                        
                        if replacement_text and replacement_text != normalized_pdf and matched_original:
                            # Create dual-layer effect:
                            # 1. Write replacement text invisibly (text rendering mode 3) - LLMs see this
                            # 2. Write original text visibly (text rendering mode 0) - Humans see this
                            new_ops.extend([
                                ([NumberObject(3)], b"Tr"),  # Set text rendering to invisible
                                ([TextStringObject(replacement_text)], b"Tj"),  # Write replacement (invisible - for LLMs)
                                ([NumberObject(0)], b"Tr"),  # Set text rendering to visible
                                ([TextStringObject(pdf_text)], b"Tj"),  # Write original PDF text (visible - for humans)
                            ])
                            continue
                    
                    new_ops.append((operands, operator))
                
                content.operations = new_ops
                page[NameObject("/Contents")] = content
                writer.add_page(page)
            
            except Exception:
                # If page processing fails, add page as-is
                writer.add_page(page)
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return True
    
    except Exception:
        return False

