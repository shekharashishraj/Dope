"""Font builder for generating deceptive fonts for font attack."""
from pathlib import Path
from typing import Optional, Tuple
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.varLib import instancer


class FontBuildError(Exception):
    """Error during font building."""
    pass


class FontBuilder:
    """Builds fonts where hidden characters display as visual characters."""
    
    def __init__(self, base_font_path: Path):
        """
        Initialize font builder.
        
        Args:
            base_font_path: Path to base TrueType font file
        """
        self.base_font_path = Path(base_font_path)
        if not self.base_font_path.exists():
            raise FontBuildError(f"Base font not found: {self.base_font_path}")
        
        # Load base font
        try:
            self._base_font = TTFont(str(self.base_font_path))
        except Exception as e:
            raise FontBuildError(f"Invalid font file: {e}")
        
        # Validate font type
        if self._base_font.sfntVersion not in [b'\x00\x01\x00\x00', b'OTTO']:
            raise FontBuildError("Not a TrueType or OpenType font")
        
        # Handle variable fonts
        if 'fvar' in self._base_font:
            axis_defaults = {axis.axisTag: axis.defaultValue for axis in self._base_font['fvar'].axes}
            self._base_font = instancer.instantiateVariableFont(self._base_font, axis_defaults, inplace=False)
        
        # Get cmap for character lookups
        self._cmap = self._base_font.getBestCmap()
        if not self._cmap:
            raise FontBuildError("Cannot read cmap from base font")
        
        # Get glyph set
        self._glyph_set = self._base_font.getGlyphSet()
    
    def build_font(
        self,
        hidden_char: str,
        visual_text: str,
        output_path: Path
    ) -> bool:
        """
        Build a font where ``hidden_char`` renders as ``visual_text``.

        The ``visual_text`` input can be a single character, multiple
        characters, or even an empty string (used to hide the glyph). When the
        string is empty we synthesize a zero-width glyph so the hidden character
        becomes invisible while still existing in the text layer.

        Args:
            hidden_char: Character encoded in the document (text layer)
            visual_text: Desired visual appearance (can be multi-character)
            output_path: Where to save the generated font

        Returns:
            True if successful, False otherwise
        """
        visual_display = visual_text or ""
        print(
            "[FontBuilder] Building font: '%s' (U+%04X) -> '%s'"
            % (hidden_char, ord(hidden_char), visual_display)
        )
        try:
            # Clone base font
            font = TTFont(str(self.base_font_path))
            
            # Handle variable fonts
            if 'fvar' in font:
                axis_defaults = {axis.axisTag: axis.defaultValue for axis in font['fvar'].axes}
                font = instancer.instantiateVariableFont(font, axis_defaults, inplace=False)
            
            # Get tables
            glyf_table = font.get('glyf')
            hmtx_table = font.get('hmtx')
            
            if not glyf_table or not hmtx_table:
                raise FontBuildError("Missing glyf/hmtx tables")
            
            # Get character codes
            hidden_code = ord(hidden_char)
            # Verify characters exist in font
            hidden_code = ord(hidden_char)
            if hidden_code not in self._cmap:
                raise FontBuildError(
                    f"Hidden character '{hidden_char}' (U+{hidden_code:04X}) not in font"
                )

            hidden_glyph_name = self._cmap[hidden_code]

            font_glyph_set = font.getGlyphSet()
            pen = TTGlyphPen(font_glyph_set)
            total_width = 0
            first_visual_glyph = None

            if visual_text:
                for visual_char in visual_text:
                    visual_code = ord(visual_char)
                    if visual_code not in self._cmap:
                        raise FontBuildError(
                            f"Visual character '{visual_char}' (U+{visual_code:04X}) not in font"
                        )
                    visual_glyph_name = self._cmap[visual_code]
                    visual_glyph = font_glyph_set[visual_glyph_name]

                    transform = TransformPen(pen, (1, 0, 0, 1, total_width, 0))
                    visual_glyph.draw(transform)

                    advance, _lsb = hmtx_table.metrics.get(visual_glyph_name, (0, 0))
                    total_width += advance

                    if first_visual_glyph is None:
                        first_visual_glyph = visual_glyph_name
            else:
                # Empty visual text: synthesize zero-width glyph by leaving pen empty
                total_width = 0

            new_glyph = pen.glyph()
            glyf_table[hidden_glyph_name] = new_glyph

            # Update metrics to match combined glyph width
            original_advance, original_lsb = hmtx_table.metrics.get(hidden_glyph_name, (0, 0))
            advance_width = int(round(total_width)) if total_width else 0
            left_side_bearing = original_lsb
            if first_visual_glyph:
                _, lsb = hmtx_table.metrics.get(first_visual_glyph, (0, original_lsb))
                left_side_bearing = lsb
            if advance_width == 0 and not visual_text:
                left_side_bearing = 0
            if visual_text:
                applied_advance = advance_width or original_advance
            else:
                applied_advance = 0
            hmtx_table.metrics[hidden_glyph_name] = (
                applied_advance,
                left_side_bearing,
            )

            print(
                f"[FontBuilder] Modified glyph '{hidden_glyph_name}' (U+{hidden_code:04X} '{hidden_char}') "
                f"to display as '{visual_display}'"
            )

            # Save font
            output_path.parent.mkdir(parents=True, exist_ok=True)
            font.save(str(output_path))

            return True

        except Exception as e:
            raise FontBuildError(f"Failed to build font: {str(e)}")
    
    def get_glyph_info(self, char: str) -> Optional[Tuple[str, int]]:
        """
        Get glyph name and character code for a character.
        
        Args:
            char: Character to look up
        
        Returns:
            Tuple of (glyph_name, char_code) or None if not found
        """
        char_code = ord(char)
        if char_code in self._cmap:
            return (self._cmap[char_code], char_code)
        return None
