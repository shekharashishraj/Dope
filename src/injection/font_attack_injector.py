"""Font Attack injection method - Custom fonts for hidden/visual text mismatch."""
import math
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from .base_injector import BaseInjector
from .font_builder import FontBuilder, FontBuildError
from ..models.perturbation import PerturbationMapping, Question
from ..latex_parser import extract_question_stem_from_latex


class FontAttackInjector(BaseInjector):
    """Applies font attack using custom fonts."""
    
    UNIVERSAL_HIDDEN_CHAR = 'a'  # All characters map to 'a' in hidden layer
    
    def __init__(self, fonts_dir: Optional[Path] = None, base_font_path: Optional[Path] = None):
        """
        Initialize font attack injector.
        
        Args:
            fonts_dir: Directory for generated font files
            base_font_path: Path to base font (default: resources/fonts/Roboto-Regular.ttf)
        """
        super().__init__()
        self.fonts_dir = fonts_dir
        self._font_counter = 0
        self._font_command_registry: Dict[str, List[str]] = {}  # Maps attack_id to font declarations
        self._generated_fonts: List[Path] = []  # Track generated font files
        
        # Find base font
        if base_font_path is None:
            # Try to find base font in resources
            project_root = Path(__file__).parent.parent.parent
            base_font_path = project_root / "resources" / "fonts" / "Roboto-Regular.ttf"
            if not base_font_path.exists():
                # Try reference_document
                base_font_path = project_root / "reference_document" / "resources" / "fonts" / "Roboto-Regular.ttf"
            if not base_font_path.exists():
                base_font_path = project_root / "reference_document" / "backend" / "resources" / "fonts" / "Roboto-Regular.ttf"
        
        self.base_font_path = base_font_path
        if not self.base_font_path.exists():
            raise FileNotFoundError(f"Base font not found: {self.base_font_path}")
        
        # Initialize font builder
        print(f"[FontAttackInjector] Initializing with base font: {self.base_font_path}")
        try:
            self.font_builder = FontBuilder(self.base_font_path)
            print(f"[FontAttackInjector] Font builder initialized successfully")
        except Exception as e:
            print(f"[FontAttackInjector] ERROR: Failed to initialize font builder: {e}")
            raise RuntimeError(f"Failed to initialize font builder: {e}")
    
    def inject(
        self,
        tex_content: str,
        perturbations: List[PerturbationMapping],
        questions: List[Question]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply font attack to LaTeX.
        
        Args:
            tex_content: Original LaTeX content
            perturbations: List of perturbation mappings
            questions: List of question data
        
        Returns:
            Tuple of (modified_tex, metadata)
        """
        print(f"[FontAttackInjector] Starting injection with {len(questions)} questions, {len(perturbations)} perturbations")
        mutated_tex = tex_content
        
        # Add fontspec package (required for XeTeX font loading)
        if "\\usepackage{fontspec}" not in mutated_tex:
            mutated_tex = self._insert_in_preamble(mutated_tex, "\\usepackage{fontspec}")
        
        # Add setmainfont if not present
        if "\\setmainfont" not in mutated_tex:
            # Use base font as main font
            base_font_name = self.base_font_path.stem
            mainfont_cmd = f"\\setmainfont{{{base_font_name}}}[Path=fonts/,Extension=.ttf]"
            mutated_tex = self._insert_in_preamble(mutated_tex, mainfont_cmd)
        
        # Reset state
        self._font_counter = 0
        self._font_command_registry = {}
        self._generated_fonts = []
        
        replacements = []
        metadata_replacements = []
        
        # Determine fonts directory (relative to output LaTeX file location)
        # For now, we'll use a fonts/ subdirectory
        # The orchestrator will need to copy this during compilation
        
        for question_idx, question in enumerate(questions):
            question_number = question.question_number
            print(f"[FontAttackInjector] Processing question {question_idx+1}/{len(questions)}: Q{question_number}")
            
            if not question_number:
                print(f"[FontAttackInjector] Skipping question {question_idx+1}: no question_number")
                continue
            
            # Apply ALL valid perturbations (not just the first one)
            question_perturbations = question.perturbations
            
            # Use latex_stem_text from first perturbation or question
            latex_stem_text = None
            if question_perturbations:
                latex_stem_text = question_perturbations[0].latex_stem_text or ''
            if not latex_stem_text:
                latex_stem_text = question.latex_stem_text or question.stem_text or ''
            
            # Find latex_stem_text in LaTeX
            stem_pos = self._find_question_stem_in_tex(mutated_tex, latex_stem_text)
            if not stem_pos:
                # Try with "True or False: " prefix
                prefixed_stem = f"True or False: {latex_stem_text}"
                stem_pos = self._find_question_stem_in_tex(mutated_tex, prefixed_stem)
                if stem_pos:
                    prefix_len = len("True or False: ")
                    stem_pos = (stem_pos[0] + prefix_len, stem_pos[1])
            
            # If still not found, try extracting directly from LaTeX by question number
            # This handles cases where LLM-generated latex_stem_text is incorrect
            if not stem_pos:
                print(f"[FontAttackInjector] Question {question_number}: JSON latex_stem_text not found, extracting from LaTeX by question number")
                extracted_stem = extract_question_stem_from_latex(mutated_tex, question_number)
                if extracted_stem:
                    print(f"[FontAttackInjector] Question {question_number}: Extracted stem from LaTeX: {extracted_stem[:50]}...")
                    # Try to find the extracted stem in the LaTeX
                    stem_pos = self._find_question_stem_in_tex(mutated_tex, extracted_stem)
                    if stem_pos:
                        latex_stem_text = extracted_stem  # Update to use the correct stem text
                        print(f"[FontAttackInjector] Question {question_number}: Successfully matched extracted stem")
                    else:
                        # Try with "True or False: " prefix
                        prefixed_extracted = f"True or False: {extracted_stem}"
                        stem_pos = self._find_question_stem_in_tex(mutated_tex, prefixed_extracted)
                        if stem_pos:
                            prefix_len = len("True or False: ")
                            stem_pos = (stem_pos[0] + prefix_len, stem_pos[1])
                            latex_stem_text = extracted_stem
                            print(f"[FontAttackInjector] Question {question_number}: Successfully matched extracted stem with prefix")
            
            if not stem_pos:
                print(f"[FontAttackInjector] Question {question_number}: Could not find stem text in LaTeX (tried JSON value and extraction), skipping")
                continue
            
            stem_start, stem_end = stem_pos
            
            # Process each perturbation for this question
            print(f"[FontAttackInjector] Found {len(question_perturbations)} perturbations for Q{question_number}")
            for pert_idx, perturbation in enumerate(question_perturbations):
                original_substring = perturbation.original_substring
                replacement_substring = perturbation.replacement_substring
                start_pos = perturbation.start_pos
                end_pos = perturbation.end_pos
                
                print(f"[FontAttackInjector] Perturbation {pert_idx+1}: '{original_substring}' -> '{replacement_substring}'")
                
                if not original_substring or not replacement_substring:
                    print(f"[FontAttackInjector] Skipping perturbation {pert_idx+1}: missing original or replacement")
                    continue
                
                # Use positions from perturbation (relative to latex_stem_text)
                if start_pos >= 0 and end_pos > start_pos and end_pos <= len(latex_stem_text):
                    abs_start = stem_start + start_pos
                    abs_end = stem_start + end_pos
                    
                    # Verify the substring matches
                    actual_substring = mutated_tex[abs_start:abs_end]
                    if actual_substring != original_substring:
                        # Try to find it manually
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
                            substring_index = stem_in_tex.find(original_substring[:5]) if len(original_substring) >= 5 else -1
                    
                    if substring_index == -1:
                        continue
                    
                    abs_start = stem_start + substring_index
                    abs_end = abs_start + len(original_substring)
                
                # If perturbation spans multiple words, attack each word
                # separately so LaTeX can still break across spaces.
                multiword_handled = False
                orig_word_spans = self._word_spans(original_substring)
                if len(orig_word_spans) > 1:
                    hidden_chunks = self._split_hidden_text_for_words(
                        replacement_substring,
                        orig_word_spans
                    )
                    multiword_handled = True
                    for (local_start, local_end, orig_word), hidden_chunk in zip(
                        orig_word_spans, hidden_chunks
                    ):
                        if not hidden_chunk:
                            continue
                        plan = self._build_attack_plan(
                            hidden_text=hidden_chunk,
                            visual_text=orig_word
                        )
                        if not plan:
                            multiword_handled = False
                            break
                        attack_id = self._next_attack_id()
                        latex_replacement = self._render_plan(attack_id, plan)
                        start_pos = abs_start + local_start
                        end_pos = abs_start + local_end
                        replacements.append((start_pos, end_pos, latex_replacement))
                        metadata_replacements.append({
                            "question_number": question_number,
                            "original": orig_word,
                            "replacement": hidden_chunk,
                            "position": (start_pos, end_pos),
                            "attack_id": attack_id,
                            "font_info": self._font_command_registry.get(attack_id, []),
                            "plan": plan
                        })

                if multiword_handled:
                    continue

                # Build plan that maps the hidden text (replacement) to the
                # visual string (original). The plan may assign multiple
                # visual characters to a single hidden character or hide
                # characters altogether when the lengths differ.
                attack_plan = self._build_attack_plan(
                    hidden_text=replacement_substring,
                    visual_text=original_substring
                )
                if not attack_plan:
                    print(
                        f"[FontAttackInjector] Skipping attack {question_number}-{pert_idx+1}: empty plan"
                    )
                    continue

                attack_id = self._next_attack_id()
                latex_replacement = self._render_plan(attack_id, attack_plan)

                replacements.append((abs_start, abs_end, latex_replacement))
                metadata_replacements.append({
                    "question_number": question_number,
                    "original": original_substring,
                    "replacement": replacement_substring,
                    "position": (abs_start, abs_end),
                    "attack_id": attack_id,
                    "font_info": self._font_command_registry.get(attack_id, []),
                    "plan": attack_plan
                })
        
        # Apply replacements in reverse order to preserve positions
        # But first, merge adjacent replacements and remove duplicates to avoid position issues
        print(f"[FontAttackInjector] Applying {len(replacements)} replacements")
        
        # Sort by start position (ascending) to identify adjacent/overlapping replacements
        replacements.sort(key=lambda x: x[0])
        
        # Remove exact duplicates (same start, end, and replacement)
        seen_replacements = set()
        unique_replacements = []
        for start, end, replacement in replacements:
            replacement_key = (start, end, replacement)
            if replacement_key not in seen_replacements:
                seen_replacements.add(replacement_key)
                unique_replacements.append((start, end, replacement))
        
        print(f"[FontAttackInjector] Removed {len(replacements) - len(unique_replacements)} duplicate replacements")
        replacements = unique_replacements
        
        # Merge adjacent replacements (where end of one == start of next)
        merged_replacements = []
        for start, end, replacement in replacements:
            if not merged_replacements:
                merged_replacements.append((start, end, replacement))
            else:
                prev_start, prev_end, prev_replacement = merged_replacements[-1]
                # If current replacement is adjacent to previous (start == prev_end)
                if start == prev_end:
                    # Merge: concatenate replacement texts
                    new_start = prev_start
                    new_end = end
                    new_replacement = prev_replacement + replacement
                    merged_replacements[-1] = (new_start, new_end, new_replacement)
                # If current replacement overlaps previous (start < prev_end)
                elif start < prev_end:
                    # Overlapping: Skip the overlapping replacement to avoid duplicate text
                    # Keep the first one (prev_replacement) and skip the overlapping one
                    print(f"[FontAttackInjector] Skipping overlapping replacement at ({start}, {end}) - overlaps with ({prev_start}, {prev_end})")
                    continue
                else:
                    # Not adjacent or overlapping, add as new replacement
                    merged_replacements.append((start, end, replacement))
        
        # Now apply in reverse order (from end to start)
        merged_replacements.sort(key=lambda x: x[0], reverse=True)
        for start, end, replacement in merged_replacements:
            mutated_tex = mutated_tex[:start] + replacement + mutated_tex[end:]
        
        # Add font declarations to preamble
        preamble_fonts = []
        for attack_id, font_info_list in self._font_command_registry.items():
            print(f"[FontAttackInjector] Registering {len(font_info_list)} fonts for {attack_id}")
            for font_info in font_info_list:
                if isinstance(font_info, dict):
                    font_cmd = font_info['font_cmd']
                    font_basename = font_info['font_basename']
                    decl = self._newfontfamily_declaration(font_cmd, font_basename, attack_id)
                    preamble_fonts.append(decl)
        
        if preamble_fonts:
            print(f"[FontAttackInjector] Adding {len(preamble_fonts)} font declarations to preamble")
            font_block = "\n".join(preamble_fonts) + "\n"
            mutated_tex = self._insert_in_preamble(mutated_tex, font_block)
        
        print(f"[FontAttackInjector] Injection complete. Total fonts to generate: {len(self._get_fonts_to_generate())}")
        
        metadata = {
            "replacements_count": len(replacements),
            "replacements": metadata_replacements,
            "font_registry": {
                attack_id: [
                    {
                        'font_cmd': info['font_cmd'],
                        'font_path': info['font_path'],
                        'hidden_char': info['hidden_char'],
                        'visual_text': info['visual_text']
                    } if isinstance(info, dict) else str(info)
                    for info in font_list
                ]
                for attack_id, font_list in self._font_command_registry.items()
            },
            "method": "font_attack",
            "fonts_to_generate": self._get_fonts_to_generate()
        }
        
        return mutated_tex, metadata
    
    def _get_fonts_to_generate(self) -> List[Dict[str, Any]]:
        """Get list of fonts that need to be generated."""
        fonts_to_generate = []
        for attack_id, font_info_list in self._font_command_registry.items():
            for font_info in font_info_list:
                if isinstance(font_info, dict):
                    fonts_to_generate.append({
                        'attack_id': attack_id,
                        'font_basename': font_info['font_basename'],
                        'font_path': font_info['font_path'],
                        'hidden_char': font_info['hidden_char'],
                        'visual_text': font_info['visual_text'],
                        'output_path': f"fonts/{attack_id}/{font_info['font_basename']}.ttf"
                    })
        return fonts_to_generate
    
    def generate_fonts(self, output_fonts_dir: Path) -> List[Path]:
        """
        Generate all required fonts.
        
        Args:
            output_fonts_dir: Directory where fonts should be generated
        
        Returns:
            List of generated font paths
        """
        print(f"[FontAttackInjector] Generating fonts in: {output_fonts_dir}")
        generated = []
        total_fonts = sum(len(font_list) for font_list in self._font_command_registry.values())
        print(f"[FontAttackInjector] Total fonts to generate: {total_fonts}")
        
        font_count = 0
        for attack_id, font_info_list in self._font_command_registry.items():
            attack_font_dir = output_fonts_dir / attack_id
            attack_font_dir.mkdir(parents=True, exist_ok=True)
            print(f"[FontAttackInjector] Creating font directory: {attack_font_dir}")
            
            for font_info in font_info_list:
                if isinstance(font_info, dict):
                    hidden_char = font_info['hidden_char']
                    visual_text = font_info['visual_text']
                    font_basename = font_info['font_basename']
                    
                    font_path = attack_font_dir / f"{font_basename}.ttf"
                    font_count += 1
                    print(
                        f"[FontAttackInjector] [{font_count}/{total_fonts}] Building font: "
                        f"{font_basename} ({hidden_char}->'{visual_text}')"
                    )
                    try:
                        self.font_builder.build_font(
                            hidden_char=hidden_char,
                            visual_text=visual_text,
                            output_path=font_path
                        )
                        generated.append(font_path)
                        print(f"[FontAttackInjector] ✓ Font built: {font_path}")
                    except FontBuildError as e:
                        print(
                            f"[FontAttackInjector] ✗ Warning: Failed to build font for "
                            f"{hidden_char}->'{visual_text}': {e}"
                        )
        
        # Also copy base font
        base_font_dest = output_fonts_dir / self.base_font_path.name
        if not base_font_dest.exists():
            import shutil
            print(f"[FontAttackInjector] Copying base font to: {base_font_dest}")
            shutil.copy2(self.base_font_path, base_font_dest)
            generated.append(base_font_dest)
        
        print(f"[FontAttackInjector] Font generation complete. Generated {len(generated)} fonts")
        return generated
    
    def _newfontfamily_declaration(
        self, macro_name: str, font_basename: str, attack_id: str
    ) -> str:
        """Generate \\newfontfamily declaration."""
        return (
            f"\\expandafter\\newfontfamily\\csname {macro_name}\\endcsname"
            f"{{{font_basename}}}[\n"
            f"    Path=fonts/{attack_id}/,\n"
            "    Extension=.ttf\n"
            "]"
        )
    
    def _font_command_name(self, attack_id: str, index: int) -> str:
        """Generate font command name."""
        safe = re.sub(r"[^A-Za-z0-9]", "", attack_id)
        if not safe:
            safe = "FA"
        if not safe[0].isalpha():
            safe = f"FA{safe}"
        return f"{safe}Font{index}"
    
    def _plain_hidden_char(self, char: str) -> str:
        """Generate plain character LaTeX code."""
        return f"{{\\char\"{ord(char):04X}}}"

    def _font_fragment(self, font_cmd: str, hidden_char: str) -> str:
        """Create LaTeX fragment that forces a specific font for a character."""
        char_code = f"\\char\"{ord(hidden_char):04X}"
        return f"{{\\csname {font_cmd}\\endcsname{char_code}}}"

    def _requires_font(self, hidden_char: str, visual_text: str) -> bool:
        """Determine whether a font swap is required for this position."""
        if visual_text == "":
            return True
        if len(visual_text) != 1:
            return True
        return hidden_char != visual_text

    def _next_attack_id(self) -> str:
        attack_id = f"fa{self._font_counter:04d}"
        self._font_counter += 1
        return attack_id

    def _render_plan(self, attack_id: str, plan: List[Dict[str, Any]]) -> str:
        """Render LaTeX for a prepared attack plan."""
        latex_fragments: List[str] = []
        for position in plan:
            pos_index = position['index']
            hidden_char = position['hidden_char']
            visual_chunk = position['visual_text']
            needs_font = self._requires_font(hidden_char, visual_chunk)

            if needs_font:
                font_cmd_name = self._font_command_name(attack_id, pos_index)
                font_basename = f"{attack_id}_pos{pos_index}"
                font_relative_path = f"fonts/{attack_id}/{font_basename}.ttf"

                latex_fragments.append(
                    self._font_fragment(font_cmd_name, hidden_char)
                )

                if attack_id not in self._font_command_registry:
                    self._font_command_registry[attack_id] = []
                self._font_command_registry[attack_id].append({
                    'font_cmd': font_cmd_name,
                    'font_basename': font_basename,
                    'hidden_char': hidden_char,
                    'visual_text': visual_chunk,
                    'position': pos_index,
                    'font_path': font_relative_path
                })
            else:
                latex_fragments.append(self._plain_hidden_char(hidden_char))

        print(
            f"[FontAttackInjector] Created attack_id: {attack_id} with {len(plan)} positions"
        )
        return "".join(latex_fragments)

    def _build_attack_plan(
        self,
        hidden_text: str,
        visual_text: str
    ) -> List[Dict[str, Any]]:
        """Plan how hidden characters should render to match the visual text."""
        if not hidden_text:
            return []

        hidden_chars = list(hidden_text)
        visual_chars = list(visual_text)
        plan: List[Dict[str, Any]] = []
        visual_index = 0

        if not visual_chars:
            for idx, hidden_char in enumerate(hidden_chars):
                plan.append({
                    'index': idx,
                    'hidden_char': hidden_char,
                    'visual_text': ''
                })
            return plan

        hidden_len = len(hidden_chars)
        visual_len = len(visual_chars)

        if hidden_len >= visual_len:
            for idx, hidden_char in enumerate(hidden_chars):
                if visual_index < visual_len:
                    chunk = visual_chars[visual_index]
                    visual_index += 1
                else:
                    chunk = ''
                plan.append({
                    'index': idx,
                    'hidden_char': hidden_char,
                    'visual_text': chunk
                })
        else:
            for idx, hidden_char in enumerate(hidden_chars):
                remaining_hidden = hidden_len - idx
                remaining_visual = visual_len - visual_index
                if remaining_hidden <= 0:
                    break
                ideal = math.ceil(remaining_visual / remaining_hidden)
                max_take = remaining_visual - (remaining_hidden - 1)
                take = max(1, min(ideal, max_take))
                chunk_chars = visual_chars[visual_index:visual_index + take]
                visual_index += take
                plan.append({
                    'index': idx,
                    'hidden_char': hidden_char,
                    'visual_text': ''.join(chunk_chars)
                })

        if visual_index < visual_len and plan:
            plan[-1]['visual_text'] += ''.join(visual_chars[visual_index:])

        return plan

    def _word_spans(self, text: str) -> List[Tuple[int, int, str]]:
        """Return (start, end, token) tuples for non-whitespace sequences."""
        spans: List[Tuple[int, int, str]] = []
        for match in re.finditer(r'\S+', text):
            spans.append((match.start(), match.end(), match.group(0)))
        return spans

    def _split_hidden_text_for_words(
        self,
        hidden_text: str,
        word_spans: List[Tuple[int, int, str]]
    ) -> List[str]:
        """Distribute hidden text across visual words to preserve whitespace layout."""
        count = len(word_spans)
        if count == 0:
            return []
        if not hidden_text:
            return [''] * count

        segments: List[str] = []
        idx = 0
        total = len(hidden_text)
        for word_idx in range(count):
            remaining_words = count - word_idx
            remaining_chars = total - idx
            if remaining_words <= 1:
                take = remaining_chars
            else:
                avg = remaining_chars // remaining_words
                if avg <= 0 and remaining_chars > 0:
                    avg = 1
                take = min(remaining_chars, avg)
            segments.append(hidden_text[idx: idx + take])
            idx += take
        if idx < total:
            segments[-1] += hidden_text[idx:]
        while len(segments) < count:
            segments.append('')
        return segments
