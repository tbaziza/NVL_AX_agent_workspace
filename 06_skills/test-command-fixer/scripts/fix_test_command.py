#!/usr/bin/env python3
"""
SLE Emulation Command Fixer (NVL_AX / ZeBu ZSE5)

Adapted from the PCH test-command-fixer for the SLE Emulation Agent.
Automatically fixes common errors in simregress testlists and grdlbuild
command lines used to compile and run DOA tests on NVL_AX models:

  - Unpaired -trex / -trex- tag pairs (PCH equivalent: -simv_args)
  - Missing -model / -emu_model argument
  - Relative -include paths (prefix with $WORKAREA/)
  - Invisible / special chars (zero-width, BOM, \\x00, ...)
  - SLE safety red lines:
      * BUG-001  -local flag in simregress (FORBIDDEN)
      * BUG-002  EMUL_QSLOT=/prj/sv/nvl/showstopper (must be .../emu/interactive)
      * BUG-003  Missing -P zsc11_express -Q /IVE/NVL/emu
      * grdlbuild typos: -Penv=immidiate / -Penv=immedate -> -Penv=immediate
      * Unknown / fuzzy grdlbuild target -> nearest valid SLE target

Valid SLE emu models:
  pkg_ghpf_model, pkg_chp_model_p2e4_fast,
  pkg_chp_hubs_full_model_p2e4, pkg_chp_model_p2e4
"""

import sys
import re
import argparse
from pathlib import Path


def _common_prefix(a, b):
    """Return the common prefix of two strings (used for fuzzy target match)."""
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return a[:i]


# ANSI Color codes for terminal highlighting
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'

# Invisible/problematic Unicode characters
INVISIBLE_CHARS = {
    '\u200b': 'ZERO WIDTH SPACE',
    '\u200c': 'ZERO WIDTH NON-JOINER',
    '\u200d': 'ZERO WIDTH JOINER',
    '\ufeff': 'ZERO WIDTH NO-BREAK SPACE (BOM)',
    '\u2060': 'WORD JOINER',
    '\u202a': 'LEFT-TO-RIGHT EMBEDDING',
    '\u202b': 'RIGHT-TO-LEFT EMBEDDING',
    '\u202c': 'POP DIRECTIONAL FORMATTING',
    '\u202d': 'LEFT-TO-RIGHT OVERRIDE',
    '\u202e': 'RIGHT-TO-LEFT OVERRIDE',
}


class SimregressCommandFixer:
    def __init__(self, testlist_file, dry_run=False, default_model='pkg_chp_model_p2e4_fast', auto_detect_model=True, workarea=None, apply_suggested=False, no_color=False):
        self.testlist_file = Path(testlist_file)
        self.dry_run = dry_run
        self.default_model = default_model
        self.auto_detect_model = auto_detect_model
        self.apply_suggested = apply_suggested
        self.no_color = no_color
        self.fixes_applied = []
        self.suggested_fixes = []  # Store suggested fixes separately
        self.detected_model = None
        # Auto-detect WORKAREA from environment or infer from testlist path
        if workarea:
            self.workarea = Path(workarea)
        else:
            # Try environment variable first
            import os
            env_workarea = os.getenv('WORKAREA')
            if env_workarea:
                self.workarea = Path(env_workarea)
            else:
                # Try to infer from testlist path (look for common patterns)
                self.workarea = self._infer_workarea()
        
    def _infer_workarea(self):
        """Infer WORKAREA from testlist path.

        For NVL_AX SLE workareas, look for a parent that contains the
        canonical SLE subtrees: output/nvlsi7_n2p (emu build output),
        reglist/nvlsi7_n2p (DOA reglists) and verif/emu (emu plugins).
        """
        path = self.testlist_file.absolute()

        sle_markers = [
            ('output', 'nvlsi7_n2p'),
            ('reglist', 'nvlsi7_n2p'),
            ('verif', 'emu'),
        ]
        for parent in path.parents:
            hits = sum(1 for a, b in sle_markers if (parent / a / b).exists())
            if hits >= 2:
                return parent
        
        # Fallback: use current directory
        return Path.cwd()
        
    def read_testlist(self):
        """Read the testlist file"""
        with open(self.testlist_file, 'r') as f:
            return f.readlines()
    
    def write_testlist(self, lines):
        """Write the testlist file"""
        with open(self.testlist_file, 'w') as f:
            f.writelines(lines)
    

    def fix_unpaired_simv_args(self, line):
        """Fix unpaired -trex- closing tags and consecutive closing tags"""
        fixed_line = line
        issues = []
        
        # First, remove consecutive closing tags (these are always wrong)
        consecutive_pattern = r'-trex-\s+-trex-'
        while re.search(consecutive_pattern, fixed_line):
            fixed_line = re.sub(consecutive_pattern, '-trex-', fixed_line, count=1)
            issues.append(f"Removed consecutive '-trex-' closing tag (unpaired)")
        
        # Pattern: standalone -trex- (not preceded by -trex with content)
        # Look for -trex- that appears after another -trex-
        parts = fixed_line.split()
        filtered_parts = []
        i = 0
        
        while i < len(parts):
            part = parts[i]
            
            # Check if this is a standalone -trex-
            if part == '-trex-':
                # Look back to see if there's an unpaired -trex before this
                # Count open and close tags up to this point
                open_count = filtered_parts.count('-trex')
                close_count = filtered_parts.count('-trex-')
                
                # If we have equal or more closes than opens, this is unpaired
                if close_count >= open_count:
                    issues.append(f"Removed unpaired '-trex-' at position {i}")
                    i += 1
                    continue
            
            filtered_parts.append(part)
            i += 1
        
        if issues:
            fixed_line = ' '.join(filtered_parts) + '\n' if line.endswith('\n') else ' '.join(filtered_parts)
            return fixed_line, issues
        
        return line, []
    
    def suggest_balanced_fix(self, line, tag_type='-trex'):
        """Generate suggested fix for unbalanced paired tags with smart placement"""
        close_tag = f'{tag_type}-'
        parts = line.split()
        
        # Count opens and closes
        open_count = parts.count(tag_type)
        close_count = parts.count(close_tag)
        
        if open_count == close_count:
            return None, None  # Already balanced
        
        suggested_line = line
        suggestion = None
        
        if open_count > close_count:
            # More opens than closes - need to find where to insert close tags
            missing = open_count - close_count
            
            # Smart approach: Track each open and find where it should close
            # A block should close when we hit a non-plusarg argument (doesn't start with +)
            new_parts = []
            open_blocks = 0  # Track unclosed blocks
            i = 0
            
            while i < len(parts):
                part = parts[i]
                new_parts.append(part)
                
                if part == tag_type:
                    # Found an opening tag
                    open_blocks += 1
                elif part == close_tag:
                    # Found a closing tag
                    open_blocks -= 1
                elif open_blocks > 0:
                    # We're inside an open block
                    # Check if this is the last plusarg before a non-plusarg
                    if i + 1 < len(parts):
                        next_part = parts[i + 1]
                        # Handle quoted plusargs: "+arg" or '"+arg"' both start with + when stripped of quotes
                        next_is_plusarg = next_part.startswith('+') or (next_part.startswith('"') and len(next_part) > 1 and next_part[1] == '+')
                        # If next part is NOT a plusarg and NOT a close tag, insert close here
                        if not next_is_plusarg and next_part != close_tag:
                            # But only insert if there are unclosed blocks
                            if open_blocks > 0:
                                new_parts.append(close_tag)
                                open_blocks -= 1
                
                i += 1
            
            # If there are still unclosed blocks, add closes at the end (before -dut/-model/-dirtag)
            if open_blocks > 0:
                # Find position to insert (before -dut or -model if they exist)
                insert_before = ['-dut', '-model', '-dirtag']
                insert_pos = None
                for marker in insert_before:
                    if marker in new_parts:
                        insert_pos = new_parts.index(marker)
                        break
                
                if insert_pos is not None:
                    # Check if inserting here would create consecutive closes
                    if insert_pos > 0 and new_parts[insert_pos - 1] == close_tag:
                        # Would create consecutive closes - don't suggest this fix
                        return None, None
                    
                    # Insert before the marker
                    new_parts = new_parts[:insert_pos] + [close_tag] * open_blocks + new_parts[insert_pos:]
                else:
                    # Append at end
                    new_parts = new_parts + [close_tag] * open_blocks
            
            suggested_line = ' '.join(new_parts)
            if line.endswith('\n'):
                suggested_line += '\n'
            suggestion = f"Add {missing} '{close_tag}' tag(s) to balance {open_count} open tag(s)"
            
        elif close_count > open_count:
            # More closes than opens - suggest removing extra closes
            extra = close_count - open_count
            # Remove the last N closes
            new_parts = []
            closes_to_remove = extra
            for part in reversed(parts):
                if part == close_tag and closes_to_remove > 0:
                    closes_to_remove -= 1
                    continue
                new_parts.insert(0, part)
            
            suggested_line = ' '.join(new_parts)
            if line.endswith('\n'):
                suggested_line += '\n'
            suggestion = f"Remove {extra} extra '{close_tag}' tag(s) to balance {open_count} open tag(s)"
        
        return suggested_line, suggestion
    
    def suggest_fix_missing_space(self, line, tag_type='-trex', position='after', tag_kind='open'):
        """Generate suggested fix for missing space around tags
        
        Args:
            position: 'before' or 'after'
            tag_kind: 'open' or 'close'
        """
        close_tag = f'{tag_type}-'
        
        if tag_kind == 'open':
            if position == 'before':
                # Pattern: text-trex (should be text -trex)
                # Use negative lookbehind to avoid matching closing tags
                pattern = f'([^\\s])({re.escape(tag_type)})(?![\\-])'
                
                if not re.search(pattern, line):
                    return None, None
                
                # Add space before the tag
                suggested_line = re.sub(pattern, f'\\1 \\2', line)
                suggestion = f"Add missing space before '{tag_type}' opening tag"
                
            else:  # position == 'after'
                # Pattern: -trex+runtime (should be -trex +runtime)
                pattern = f'{re.escape(tag_type)}([^\\s\\-])'
                
                if not re.search(pattern, line):
                    return None, None
                
                # Add space after the tag
                suggested_line = re.sub(pattern, f'{tag_type} \\1', line)
                suggestion = f"Add missing space after '{tag_type}' opening tag"
        
        else:  # tag_kind == 'close'
            if position == 'before':
                # Pattern: +opt-trex- (should be +opt -trex-)
                pattern = f'([^\\s\\-]){re.escape(close_tag)}'
                
                if not re.search(pattern, line):
                    return None, None
                
                # Add space before the closing tag
                suggested_line = re.sub(pattern, f'\\1 {close_tag}', line)
                suggestion = f"Add missing space before '{close_tag}' closing tag"
                
            else:  # position == 'after'
                # Pattern: -trex-+opt (should be -trex- +opt)
                pattern = f'{re.escape(close_tag)}([^\\s])'
                
                if not re.search(pattern, line):
                    return None, None
                
                # Add space after the closing tag
                suggested_line = re.sub(pattern, f'{close_tag} \\1', line)
                suggestion = f"Add missing space after '{close_tag}' closing tag"
        
        return suggested_line, suggestion
    
    def suggest_fix_plusargs_spacing(self, line):
        """Generate suggested fix for missing space between plusargs"""
        # Pattern: +OPT1+OPT2 (should be +OPT1 +OPT2)
        pattern = r'(\+[A-Z_0-9=]+)(\+[A-Z_0-9=]+)'
        
        if not re.search(pattern, line):
            return None, None
        
        # Add space between plusargs
        suggested_line = re.sub(pattern, r'\1 \2', line)
        # Keep applying until no more consecutive plusargs (with safety limit)
        max_iterations = 20
        iterations = 0
        while re.search(pattern, suggested_line) and iterations < max_iterations:
            suggested_line = re.sub(pattern, r'\1 \2', suggested_line)
            iterations += 1
        
        suggestion = f"Add missing spaces between consecutive plusargs"
        
        return suggested_line, suggestion
    
    def suggest_fix_consecutive_tags(self, line, tag_type='-trex'):
        """Generate suggested fix for consecutive opening tags (invalid nesting)"""
        close_tag = f'{tag_type}-'
        
        # Pattern: -trex -trex (two consecutive opens)
        # Option 1: Remove the second open (most likely a typo)
        # Option 2: Add a close between them
        
        pattern = f'{re.escape(tag_type)}\\s+{re.escape(tag_type)}\\s+'
        
        if not re.search(pattern, line):
            return None, None
        
        # Try option 1: Remove the duplicate open tag
        suggested_line = re.sub(pattern, f'{tag_type} ', line, count=1)
        suggestion = f"Remove duplicate consecutive '{tag_type}' tag (likely a typo)"
        
        return suggested_line, suggestion
    
    def suggest_fix_consecutive_closes(self, line, tag_type='-trex'):
        """Generate suggested fix for consecutive closing tags (unpaired close)"""
        close_tag = f'{tag_type}-'
        
        # Pattern: -trex- -trex- (two consecutive closes)
        # Remove the second close (it's unpaired)
        
        pattern = f'{re.escape(close_tag)}\\s+{re.escape(close_tag)}'
        
        if not re.search(pattern, line):
            return None, None
        
        # Remove the duplicate close tag
        suggested_line = re.sub(pattern, f'{close_tag}', line, count=1)
        suggestion = f"Remove duplicate consecutive '{close_tag}' closing tag (unpaired)"
        
        return suggested_line, suggestion
    
    def fix_unpaired_user_do_files(self, line):
        """Fix unpaired -user_do_files_vcs- closing tags and consecutive closing tags"""
        fixed_line = line
        issues = []
        
        # First, remove consecutive closing tags (these are always wrong)
        consecutive_pattern = r'-user_do_files_vcs-\s+-user_do_files_vcs-'
        while re.search(consecutive_pattern, fixed_line):
            fixed_line = re.sub(consecutive_pattern, '-user_do_files_vcs-', fixed_line, count=1)
            issues.append(f"Removed consecutive '-user_do_files_vcs-' closing tag (unpaired)")
        
        # Pattern: -user_do_files_vcs -user_do_files_vcs- (empty pair)
        if re.search(r'-user_do_files_vcs\s+-user_do_files_vcs-', fixed_line):
            fixed_line = re.sub(r'-user_do_files_vcs\s+-user_do_files_vcs-\s*', '', fixed_line)
            issues.append("Removed empty '-user_do_files_vcs -user_do_files_vcs-' pair")
            return fixed_line, issues
        
        # Pattern: standalone -user_do_files_vcs- (similar to simv_args)
        parts = fixed_line.split()
        filtered_parts = []
        i = 0
        
        while i < len(parts):
            part = parts[i]
            
            if part == '-user_do_files_vcs-':
                open_count = filtered_parts.count('-user_do_files_vcs')
                close_count = filtered_parts.count('-user_do_files_vcs-')
                
                if close_count >= open_count:
                    issues.append(f"Removed unpaired '-user_do_files_vcs-' at position {i}")
                    i += 1
                    continue
            
            filtered_parts.append(part)
            i += 1
        
        if issues:
            fixed_line = ' '.join(filtered_parts) + '\n' if line.endswith('\n') else ' '.join(filtered_parts)
        
        return fixed_line, issues
    
    def auto_detect_model_from_testlist(self, lines):
        """Auto-detect the emu_model used in other tests in the same testlist"""
        model_counts = {}
        
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                match = re.search(r'-emu_model\s+(\S+)', line)
                if match:
                    model = match.group(1)
                    model_counts[model] = model_counts.get(model, 0) + 1
        
        if model_counts:
            most_common = max(model_counts.items(), key=lambda x: x[1])
            return most_common[0]
        
        return None
    
    def fix_missing_model(self, line):
        """Fix missing -emu_model argument on simregress lines"""
        issues = []
        
        # Only act on simregress lines that have -dut but no -emu_model
        if 'simregress' in line and '-dut' in line and '-emu_model' not in line:
            model_to_use = self.detected_model if self.detected_model else self.default_model
            
            match = re.search(r'(-dut\s+\w+)', line)
            if match:
                dut_arg = match.group(1)
                fixed_line = line.replace(dut_arg, f"{dut_arg} -emu_model {model_to_use}")
                
                if self.detected_model:
                    issues.append(f"Added missing '-emu_model {model_to_use}' (auto-detected from testlist)")
                else:
                    issues.append(f"Added missing '-emu_model {model_to_use}' (using default)")
                
                return fixed_line, issues
        
        return line, []
    
    def fix_relative_include_paths(self, line):
        """Fix relative -include paths by prepending $WORKAREA/ and check if files exist"""
        issues = []
        fixed_line = line
        
        # Find all -include arguments
        # Pattern 1: relative paths (don't start with / or $)
        relative_pattern = r'-include\s+([^\s\-/\$][^\s]*)'
        # Pattern 2: $WORKAREA paths or absolute paths
        absolute_pattern = r'-include\s+([\$/][^\s]*)'
        
        # Check relative paths first
        matches = list(re.finditer(relative_pattern, line))
        if matches:
            # Process matches in reverse order to preserve positions
            for match in reversed(matches):
                rel_path = match.group(1)
                
                # Check if this file exists relative to WORKAREA
                full_path = self.workarea / rel_path
                if full_path.exists():
                    # Replace with $WORKAREA/ prefix
                    old_include = f"-include {rel_path}"
                    new_include = f"-include $WORKAREA/{rel_path}"
                    fixed_line = fixed_line.replace(old_include, new_include)
                    issues.append(f"Fixed relative -include path: {rel_path} → $WORKAREA/{rel_path} (file exists)")
                else:
                    # File doesn't exist - report but don't change
                    issues.append(f"⚠ ERROR: Include file not found: {rel_path} (expected at {full_path})")
        
        # Check absolute paths (including $WORKAREA)
        abs_matches = list(re.finditer(absolute_pattern, line))
        for match in abs_matches:
            file_path = match.group(1)
            
            # Expand $WORKAREA if present
            if file_path.startswith('$WORKAREA/'):
                expanded_path = self.workarea / file_path.replace('$WORKAREA/', '')
            elif file_path.startswith('/'):
                expanded_path = Path(file_path)
            else:
                expanded_path = self.workarea / file_path
            
            # Check if file exists
            if not expanded_path.exists():
                issues.append(f"⚠ ERROR: Include file not found: {file_path} (expected at {expanded_path})")
        
        if issues:
            return fixed_line, issues
        
        return line, []
    
    def check_user_do_files_exist(self, line):
        """Check if files specified with -user_do_files_vcs exist"""
        issues = []
        
        # Pattern: -user_do_files_vcs <file_path>
        # Look for the file path after -user_do_files_vcs and before the closing -user_do_files_vcs-
        user_do_files_pattern = r'-user_do_files_vcs\s+([^\s\-][^\s]*)'
        
        matches = re.finditer(user_do_files_pattern, line)
        for match in matches:
            file_path = match.group(1)
            
            # Expand $WORKAREA if present
            if file_path.startswith('$WORKAREA/'):
                expanded_path = self.workarea / file_path.replace('$WORKAREA/', '')
            elif file_path.startswith('/'):
                expanded_path = Path(file_path)
            else:
                # Relative path - assume relative to WORKAREA
                expanded_path = self.workarea / file_path
            
            # Check if file exists
            if not expanded_path.exists():
                issues.append(f"⚠ ERROR: File not found: {file_path} (expected at {expanded_path})")
        
        return issues
    
    def check_special_characters(self, line, line_num):
        """Detect non-printable, non-ASCII, and invisible characters"""
        issues = []
        
        # Skip checking comment lines
        if line.strip().startswith('#'):
            return issues
        
        # Check for literal escape sequences (text like "\x00", "\n", etc.)
        literal_escape_pattern = r'\\x[0-9a-fA-F]{2}|\\[nrt0\\]'
        literal_matches = list(re.finditer(literal_escape_pattern, line))
        if literal_matches:
            for match in literal_matches:
                escaped_text = match.group()
                pos = match.start()
                issues.append(f"⚠ ERROR: Literal escape sequence '{escaped_text}' at position {pos} (should be removed)")
        
        # Check for ANSI escape sequences (from colored terminal output)
        ansi_pattern = r'\x1b\[[0-9;]*[mGKHf]'
        if re.search(ansi_pattern, line):
            issues.append(f"⚠ ERROR: ANSI escape sequence detected (likely from colored terminal copy-paste)")
        
        # Check each character
        special_chars_found = []
        for i, char in enumerate(line):
            # Skip newline characters at end
            if char in ['\n', '\r'] and i >= len(line.rstrip('\r\n')):
                continue
            
            # Check for invisible Unicode characters
            if char in INVISIBLE_CHARS:
                char_name = INVISIBLE_CHARS[char]
                special_chars_found.append({
                    'pos': i,
                    'char': char,
                    'type': 'invisible',
                    'desc': f"Invisible character: {char_name} (U+{ord(char):04X})"
                })
            
            # Check for non-printable control characters (ASCII 0-31, 127)
            # Allow: tab (9), space (32)
            elif ord(char) < 32 and char not in ['\t']:
                if ord(char) == 0:
                    desc = f"NULL byte (\\x00)"
                else:
                    desc = f"Control character (ASCII {ord(char)}, \\x{ord(char):02X})"
                special_chars_found.append({
                    'pos': i,
                    'char': char,
                    'type': 'control',
                    'desc': desc
                })
            
            # Check for non-ASCII characters (> 127) that might cause issues
            elif ord(char) > 127:
                # Common problematic characters from copy-paste
                if char in ['\u201c', '\u201d', '\u2018', '\u2019']:  # Smart quotes
                    desc = f"Smart quote: '{char}' (U+{ord(char):04X}) - use regular quotes"
                elif char in ['\u2014', '\u2013']:  # Em/en dash
                    desc = f"Em/En dash: '{char}' (U+{ord(char):04X}) - use hyphen '-'"
                elif char == '\xa0':  # Non-breaking space
                    desc = f"Non-breaking space (U+00A0) - use regular space"
                else:
                    desc = f"Non-ASCII: '{char}' (U+{ord(char):04X})"
                
                special_chars_found.append({
                    'pos': i,
                    'char': char,
                    'type': 'non-ascii',
                    'desc': desc
                })
        
        # Report found special characters
        if special_chars_found:
            for char_info in special_chars_found:
                # Show context around the character
                pos = char_info['pos']
                start = max(0, pos - 15)
                end = min(len(line), pos + 15)
                
                before = line[start:pos]
                char_repr = repr(char_info['char'])[1:-1]  # Remove quotes
                after = line[pos+1:end]
                
                # Create visual representation
                context = f"...{before}[{char_repr}]{after}..."
                
                issues.append(f"⚠ ERROR: {char_info['desc']} at position {pos}")
                issues.append(f"   Context: {context}")
        
        return issues
    
    def remove_special_characters(self, line):
        """Remove special characters and literal escape sequences from line"""
        issues = []
        fixed_line = line
        
        # Remove literal escape sequences (like "\x00", "\n", etc.)
        literal_escape_pattern = r'\\x[0-9a-fA-F]{2}|\\[nrt0\\]'
        literal_matches = list(re.finditer(literal_escape_pattern, fixed_line))
        if literal_matches:
            for match in literal_matches:
                issues.append(f"   ✓ Removed literal escape sequence: {match.group()}")
            fixed_line = re.sub(literal_escape_pattern, '', fixed_line)
        
        # Remove ANSI escape sequences
        ansi_pattern = r'\x1b\[[0-9;]*[mGKHf]'
        if re.search(ansi_pattern, fixed_line):
            fixed_line = re.sub(ansi_pattern, '', fixed_line)
            issues.append(f"   ✓ Removed ANSI escape sequences")
        
        # Remove invisible Unicode and non-printable characters
        cleaned_chars = []
        removed_chars = []
        for i, char in enumerate(fixed_line):
            # Keep newline characters at end
            if char in ['\n', '\r'] and i >= len(fixed_line.rstrip('\r\n')):
                cleaned_chars.append(char)
                continue
            
            # Remove invisible Unicode
            if char in INVISIBLE_CHARS:
                removed_chars.append(f"{INVISIBLE_CHARS[char]} at pos {i}")
                continue
            
            # Remove non-printable control characters (except tab)
            if ord(char) < 32 and char not in ['\t']:
                removed_chars.append(f"\\x{ord(char):02X} at pos {i}")
                continue
            
            # Keep normal characters
            cleaned_chars.append(char)
        
        if removed_chars:
            issues.append(f"   ✓ Removed special characters: {', '.join(removed_chars)}")
        
        fixed_line = ''.join(cleaned_chars)
        return fixed_line, issues
    
    def visualize_special_chars(self, line):
        """Convert special characters to visible representation and highlight literal escape sequences"""
        # First, mark literal escape sequences
        literal_escape_pattern = r'\\x[0-9a-fA-F]{2}|\\[nrt0\\]'
        marked_line = line.rstrip('\r\n')
        
        # Highlight literal escape sequences
        if self.no_color:
            marked_line = re.sub(literal_escape_pattern, r'>>>\g<0><<<', marked_line)
            # Then convert actual special characters to visible representation
            result = []
            for char in marked_line:
                if char == '\t':
                    result.append('→TAB')
                elif char == '\r':
                    result.append('←CR')
                elif char in INVISIBLE_CHARS:
                    result.append(f'<{INVISIBLE_CHARS[char][:4]}>')
                elif ord(char) < 32:
                    result.append(f'<\\x{ord(char):02X}>')
                elif ord(char) > 127:
                    result.append(f'<U+{ord(char):04X}>')
                else:
                    result.append(char)
            return ''.join(result)
        else:
            # With color mode, we add ANSI codes which we need to preserve
            marked_line = re.sub(literal_escape_pattern, 
                                lambda m: f'{Colors.BG_RED}{Colors.WHITE}{m.group()}{Colors.RESET}', 
                                marked_line)
            # Convert non-ANSI special characters to visible representation
            result = []
            i = 0
            while i < len(marked_line):
                # Check if we're at the start of an ANSI escape sequence
                if marked_line[i:i+2] == '\x1b[':
                    # Find the end of the ANSI sequence
                    end = i + 2
                    while end < len(marked_line) and marked_line[end] not in 'mGKHf':
                        end += 1
                    end += 1  # Include the final character
                    result.append(marked_line[i:end])
                    i = end
                    continue
                
                char = marked_line[i]
                if char == '\t':
                    result.append('→TAB')
                elif char == '\r':
                    result.append('←CR')
                elif char in INVISIBLE_CHARS:
                    result.append(f'<{INVISIBLE_CHARS[char][:4]}>')
                elif ord(char) < 32:
                    result.append(f'<\\x{ord(char):02X}>')
                elif ord(char) > 127:
                    result.append(f'<U+{ord(char):04X}>')
                else:
                    result.append(char)
                i += 1
            return ''.join(result)
    
    def highlight_error_in_line(self, line, error_types, tag_type='-trex'):
        """Create a visual representation highlighting the error location with ANSI colors
        
        Args:
            line: The line to highlight
            error_types: Can be a string (single error) or list of errors
            tag_type: The tag type being checked (default: '-trex')
        """
        close_tag = f'{tag_type}-'
        parts = line.split()
        
        # Ensure error_types is a list
        if isinstance(error_types, str):
            error_types = [error_types]
        
        # Color codes (disabled if no_color is set)
        if self.no_color:
            error_start = ">>>"
            error_end = "<<<<"
            open_start = "["
            open_end = "]"
            close_start = "["
            close_end = "]"
        else:
            error_start = f"{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}"
            error_end = Colors.RESET
            open_start = f"{Colors.CYAN}{Colors.BOLD}["
            open_end = f"]{Colors.RESET}"
            close_start = f"{Colors.YELLOW}{Colors.BOLD}["
            close_end = f"]{Colors.RESET}"
        
        # Check if we have ONLY special character errors (then use visualize_special_chars)
        has_special_char_only = all(
            'special character' in et.lower() or 'non-printable' in et.lower() or 
            'non-ascii' in et.lower() or 'escape sequence' in et.lower()
            for et in error_types
        )
        
        if has_special_char_only:
            return self.visualize_special_chars(line)
        
        # Build a set of parts that should be highlighted based on ALL error types
        parts_to_highlight = set()
        
        for error_type in error_types:
            if 'plusargs' in error_type.lower():
                # Mark consecutive plusargs without space (Pattern: +OPT1+OPT2)
                for i, part in enumerate(parts):
                    if re.search(r'\+[A-Z_0-9=]+\+[A-Z_0-9=]+', part):
                        parts_to_highlight.add(i)
            
            elif 'Missing space' in error_type:
                # Mark any token that contains spacing violations
                for i, part in enumerate(parts):
                    has_error = False
                    
                    # Check for various spacing violations in this token
                    # 1. Opening tag glued to something before it (except at start): text-trex
                    if tag_type in part and part != tag_type and not part.startswith(tag_type):
                        idx = part.find(tag_type)
                        if idx > 0 and part[idx-1] != ' ':
                            has_error = True
                    
                    # 2. Opening tag glued to something after it: -trex+opt or -trex-trex
                    if part.startswith(tag_type) and len(part) > len(tag_type):
                        after_tag = part[len(tag_type):]
                        if not after_tag.startswith('-') or (after_tag.startswith('-') and len(after_tag) > 1):
                            has_error = True
                    
                    # 3. Closing tag glued to something before it: +opt-trex- or -trex--trex-
                    if close_tag in part and len(part) > len(close_tag):
                        idx = part.find(close_tag)
                        if idx > 0:
                            has_error = True
                    
                    # 4. Closing tag glued to something after it: -trex-+opt or -trex-trex
                    if part.startswith(close_tag) and len(part) > len(close_tag):
                        has_error = True
                    
                    if has_error:
                        parts_to_highlight.add(i)
            
            elif 'Consecutive' in error_type:
                # Check if it's consecutive opening or closing tags
                if 'closing tag' in error_type.lower():
                    # Mark consecutive closing tags (the second one is the error)
                    prev_was_close = False
                    for i, part in enumerate(parts):
                        if part == close_tag:
                            if prev_was_close:
                                parts_to_highlight.add(i)
                            prev_was_close = True
                        elif part == tag_type:
                            prev_was_close = False
                        else:
                            prev_was_close = False
                else:
                    # Mark consecutive opening tags (the second one is the error)
                    prev_was_open = False
                    for i, part in enumerate(parts):
                        if part == tag_type:
                            if prev_was_open:
                                parts_to_highlight.add(i)
                            prev_was_open = True
                        elif part == close_tag:
                            prev_was_open = False
            
            elif 'File not found' in error_type or 'Include file not found' in error_type:
                # Mark the missing file path
                if 'not found:' in error_type:
                    match = re.search(r'not found: ([^\s]+)', error_type)
                    if match:
                        missing_file = match.group(1)
                        for i, part in enumerate(parts):
                            if missing_file in part or part in missing_file:
                                parts_to_highlight.add(i)
        
        # Build the highlighted output
        highlighted_parts = []
        
        # Check if we need special handling for Unbalanced (show all tags with numbers)
        has_unbalanced = any('Unbalanced' in et for et in error_types)
        
        if has_unbalanced:
            # For unbalanced errors, show all opens/closes with numbers
            open_count = 0
            close_count = 0
            for i, part in enumerate(parts):
                if part == tag_type:
                    open_count += 1
                    highlighted_parts.append(f"{open_start}{part}#{open_count}{open_end}")
                elif part == close_tag:
                    close_count += 1
                    highlighted_parts.append(f"{close_start}{part}#{close_count}{close_end}")
                elif i in parts_to_highlight:
                    highlighted_parts.append(f"{error_start}{part}{error_end}")
                else:
                    highlighted_parts.append(part)
        else:
            # Standard highlighting for other errors
            for i, part in enumerate(parts):
                if i in parts_to_highlight:
                    highlighted_parts.append(f"{error_start}{part}{error_end}")
                else:
                    highlighted_parts.append(part)
        
        result = ' '.join(highlighted_parts)
        
        # Add special character highlighting if needed
        has_special_chars = any(
            'special character' in et.lower() or 'non-printable' in et.lower() or 
            'non-ascii' in et.lower() or 'escape sequence' in et.lower()
            for et in error_types
        )
        
        if has_special_chars:
            # Apply literal escape sequence highlighting
            literal_escape_pattern = r'\\x[0-9a-fA-F]{2}|\\[nrt0\\]'
            if self.no_color:
                result = re.sub(literal_escape_pattern, r'>>>\g<0><<<', result)
            else:
                result = re.sub(literal_escape_pattern, 
                              lambda m: f'{Colors.BG_RED}{Colors.WHITE}{m.group()}{Colors.RESET}', 
                              result)
        
        return result
    
    def print_full_command_with_highlight(self, line, error_type, tag_type='-trex'):
        """Print the full command with error highlighting"""
        highlighted_line = self.highlight_error_in_line(line, error_type, tag_type)
        
        print(f"\n   📋 FULL COMMAND (error highlighted):")
        print(f"   {'─' * 100}")
        
        # Word wrap at reasonable length (account for ANSI codes in length calculation)
        max_width = 120
        words = highlighted_line.split()
        current_line = "   "
        
        for word in words:
            # Strip ANSI codes for length calculation
            word_display_len = len(re.sub(r'\033\[[0-9;]+m', '', word))
            current_line_len = len(re.sub(r'\033\[[0-9;]+m', '', current_line))
            
            if current_line_len + word_display_len + 1 > max_width:
                print(current_line)
                current_line = "   " + word
            else:
                if current_line == "   ":
                    current_line += word
                else:
                    current_line += " " + word
        
        if current_line.strip():
            print(current_line)
        
        print(f"   {'─' * 100}")
        if self.no_color:
            print(f"   Legend: >>>ERROR<<< = problematic tag, [tag#N] = tag number N")
        else:
            print(f"   Legend: {Colors.BG_RED}{Colors.WHITE}ERROR{Colors.RESET} = problematic tag, "
                  f"{Colors.CYAN}[open#{Colors.RESET}N{Colors.CYAN}]{Colors.RESET} = open tag #N, "
                  f"{Colors.YELLOW}[close#{Colors.RESET}N{Colors.YELLOW}]{Colors.RESET} = close tag #N")
    
    def highlight_suggested_fix(self, original_line, suggested_line):
        """Highlight the parts that changed in the suggested fix"""
        import difflib
        
        # Use green highlighting for changed/added tokens
        if self.no_color:
            fix_start = ">>>"
            fix_end = "<<<"
        else:
            fix_start = f"{Colors.BG_GREEN}{Colors.WHITE}{Colors.BOLD}"
            fix_end = Colors.RESET
        
        orig_tokens = original_line.split()
        sugg_tokens = suggested_line.split()
        
        # Use difflib to get a proper diff
        matcher = difflib.SequenceMatcher(None, orig_tokens, sugg_tokens)
        
        highlighted = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # These tokens are the same
                highlighted.extend(sugg_tokens[j1:j2])
            elif tag == 'replace':
                # Tokens were replaced - highlight the new ones
                for token in sugg_tokens[j1:j2]:
                    highlighted.append(f"{fix_start}{token}{fix_end}")
            elif tag == 'insert':
                # New tokens added - highlight them
                for token in sugg_tokens[j1:j2]:
                    highlighted.append(f"{fix_start}{token}{fix_end}")
            elif tag == 'delete':
                # Tokens were removed - nothing to show in suggested line
                pass
        
        return ' '.join(highlighted)
    
    def validate_paired_switches(self, line):
        """Validate that paired switches are balanced and properly nested
        
        Rule: ALL tags must have space BEFORE and AFTER them:
        - Opening tags: SPACE -trex SPACE
        - Closing tags: SPACE -trex- SPACE
        - Plusargs: SPACE +DEFINE SPACE (inside -trex pairs)
        """
        warnings = []
        
        # Check for missing spaces around plusargs (e.g., +OPT1+OPT2 instead of +OPT1 +OPT2)
        # Pattern: +WORD+WORD (two plusargs without space between)
        if re.search(r'\+[A-Z_0-9=]+\+[A-Z_0-9=]+', line):
            matches = re.findall(r'(\+[A-Z_0-9=]+\+[A-Z_0-9=]+)', line)
            warnings.append(f"⚠ ERROR: Missing space between plusargs (found: '{matches[0][:40]}...')")
        
        # Check for missing space BEFORE opening tags (e.g., text-trex instead of text -trex)
        # Skip the start of line (allow tags at beginning)
        if re.search(r'([^\s])-trex(\s|$)', line):
            matches = re.findall(r'([^\s]+)-trex', line)
            # Filter out closing tags (which end with -)
            non_close_matches = [m for m in matches if not m.endswith('-')]
            if non_close_matches:
                warnings.append(f"⚠ ERROR: Missing space before '-trex' opening tag (found: '...{non_close_matches[0][-20:]}-trex')")
        
        if re.search(r'([^\s])-user_do_files_vcs(\s|$)', line):
            matches = re.findall(r'([^\s]+)-user_do_files_vcs', line)
            non_close_matches = [m for m in matches if not m.endswith('-')]
            if non_close_matches:
                warnings.append(f"⚠ ERROR: Missing space before '-user_do_files_vcs' opening tag (found: '...{non_close_matches[0][-20:]}-user_do_files_vcs')")
        
        # Check for missing space AFTER opening tags (e.g., -trex+runtime instead of -trex +runtime)
        if re.search(r'-trex([^\s\-])', line):
            matches = re.findall(r'-trex([^\s\-]+)', line)
            warnings.append(f"⚠ ERROR: Missing space after '-trex' opening tag (found: '-trex{matches[0][:20]}...')")
        
        if re.search(r'-user_do_files_vcs([^\s\-])', line):
            matches = re.findall(r'-user_do_files_vcs([^\s\-]+)', line)
            warnings.append(f"⚠ ERROR: Missing space after '-user_do_files_vcs' opening tag (found: '-user_do_files_vcs{matches[0][:20]}...')")
        
        # Check for missing space BEFORE closing tags (e.g., +opt-trex- instead of +opt -trex-)
        if re.search(r'([^\s\-])-trex-', line):
            matches = re.findall(r'([^\s\-]+)-trex-', line)
            warnings.append(f"⚠ ERROR: Missing space before '-trex-' closing tag (found: '...{matches[0][-20:]}-trex-')")
        
        if re.search(r'([^\s\-])-user_do_files_vcs-', line):
            matches = re.findall(r'([^\s\-]+)-user_do_files_vcs-', line)
            warnings.append(f"⚠ ERROR: Missing space before '-user_do_files_vcs-' closing tag (found: '...{matches[0][-20:]}-user_do_files_vcs-')")
        
        # Check for missing space AFTER closing tags (e.g., -trex-+opt instead of -trex- +opt)
        if re.search(r'-trex-([^\s])', line):
            matches = re.findall(r'-trex-([^\s]+)', line)
            warnings.append(f"⚠ ERROR: Missing space after '-trex-' closing tag (found: '-trex-{matches[0][:20]}...')")
        
        if re.search(r'-user_do_files_vcs-([^\s])', line):
            matches = re.findall(r'-user_do_files_vcs-([^\s]+)', line)
            warnings.append(f"⚠ ERROR: Missing space after '-user_do_files_vcs-' closing tag (found: '-user_do_files_vcs-{matches[0][:20]}...')")
        
        # Check for consecutive opens (nested incorrectly)
        if re.search(r'-trex\s+-trex\s+', line):
            warnings.append(f"⚠ ERROR: Consecutive -trex tags without closing tag between them (invalid nesting)")
        
        if re.search(r'-user_do_files_vcs\s+-user_do_files_vcs\s+', line):
            warnings.append(f"⚠ ERROR: Consecutive -user_do_files_vcs tags without closing tag between them (invalid nesting)")
        
        # Check for consecutive closes (unpaired closing tag)
        if re.search(r'-trex-\s+-trex-', line):
            warnings.append(f"⚠ ERROR: Consecutive -trex- closing tags (unpaired closing tag)")
        
        if re.search(r'-user_do_files_vcs-\s+-user_do_files_vcs-', line):
            warnings.append(f"⚠ ERROR: Consecutive -user_do_files_vcs- closing tags (unpaired closing tag)")
        
        # Check -trex pairs balance (only if no nesting error)
        simv_open = line.count('-trex ') + line.count('-trex\t')
        simv_close = line.count('-trex-')
        if simv_open != simv_close and not any('Consecutive -trex' in w for w in warnings):
            warnings.append(f"⚠ Unbalanced -trex: {simv_open} open, {simv_close} close (may need manual review)")
        
        # Check -user_do_files_vcs pairs balance
        udf_open = line.count('-user_do_files_vcs ') + line.count('-user_do_files_vcs\t')
        udf_close = line.count('-user_do_files_vcs-')
        if udf_open != udf_close and not any('Consecutive -user_do_files_vcs' in w for w in warnings):
            warnings.append(f"⚠ Unbalanced -user_do_files_vcs: {udf_open} open, {udf_close} close (may need manual review)")
        
        # Check -ms pairs
        ms_open = line.count('-ms ') + line.count('-ms\t')
        ms_close = line.count('-ms-')
        if ms_open != ms_close:
            warnings.append(f"⚠ Unbalanced -ms: {ms_open} open, {ms_close} close (may need manual review)")
        
        # Check if -user_do_files_vcs files exist
        file_warnings = self.check_user_do_files_exist(line)
        warnings.extend(file_warnings)
        
        return warnings
    
    # ------------------------------------------------------------------
    # SLE-specific safety detectors (NVL_AX / ZeBu ZSE5)
    # ------------------------------------------------------------------
    SLE_VALID_TARGETS = (
        'pkg_ghpf_model_zse5',
        'pkg_chp_model_p2e4_fast_zse5',
        'pkg_chp_hubs_full_model_p2e4_zse5',
        'pkg_chp_model_p2e4_zse5',
    )
    SLE_VALID_EMU_MODELS = (
        'pkg_ghpf_model',
        'pkg_chp_model_p2e4_fast',
        'pkg_chp_hubs_full_model_p2e4',
        'pkg_chp_model_p2e4',
    )
    SLE_REQUIRED_QSLOT = 'EMUL_QSLOT=/prj/sv/nvl/emu/interactive'
    SLE_REQUIRED_PQ = ('-P', 'zsc11_express', '-Q', '/IVE/NVL/emu')

    def fix_sle_safety(self, line):
        """SLE-specific auto-fixes for simregress / grdlbuild commands.

        Catches the documented red lines:
          BUG-001: -local flag in simregress (forbidden) -> strip
          BUG-002: EMUL_QSLOT=.../showstopper -> .../emu/interactive
          BUG-003: missing -P zsc11_express -Q /IVE/NVL/emu -> append
                   (only when the line clearly contains a simregress invocation)
          grdlbuild typos: -Penv=immidiate / -Penv=immedate -> -Penv=immediate
          Unknown grdlbuild target (under :emu_build:zebu:) -> fuzzy-suggest
            the nearest valid SLE target (suggestion only, never auto-applied).
        """
        issues = []
        suggestions = []
        fixed = line

        is_simregress = 'simregress' in fixed
        is_grdlbuild  = 'grdlbuild'  in fixed

        # --- BUG-001: -local in simregress ---
        if is_simregress and re.search(r'(?<!\S)-local(?!\S)', fixed):
            fixed = re.sub(r'\s+-local(?=\s|$)', '', fixed)
            fixed = re.sub(r'-local\s+', '', fixed)
            issues.append("BUG-001: stripped forbidden '-local' flag from simregress")

        # --- BUG-002: showstopper queue ---
        if 'EMUL_QSLOT=' in fixed and 'showstopper' in fixed:
            fixed = re.sub(
                r'EMUL_QSLOT=\S*showstopper\S*',
                'EMUL_QSLOT=/prj/sv/nvl/emu/interactive',
                fixed,
            )
            issues.append("BUG-002: replaced EMUL_QSLOT=.../showstopper with /prj/sv/nvl/emu/interactive")

        # --- BUG-002b: simregress without any EMUL_QSLOT -> append ---
        if is_simregress and 'EMUL_QSLOT=' not in fixed:
            # Append before the trailing `-l <reglist>` if present, else at end.
            m = re.search(r'\s-l\s+\S+', fixed)
            insertion = ' ' + self.SLE_REQUIRED_QSLOT
            if m:
                fixed = fixed[:m.start()] + insertion + fixed[m.start():]
            else:
                fixed = fixed.rstrip('\n').rstrip() + insertion + ('\n' if line.endswith('\n') else '')
            issues.append(f"BUG-002: appended required {self.SLE_REQUIRED_QSLOT}")

        # --- BUG-003: missing -P/-Q on simregress ---
        if is_simregress:
            need_P = not re.search(r'(?<!\S)-P\s+zsc11_express\b', fixed)
            need_Q = not re.search(r'(?<!\S)-Q\s+/IVE/NVL/emu\b', fixed)
            if need_P or need_Q:
                add = []
                if need_P: add += ['-P', 'zsc11_express']
                if need_Q: add += ['-Q', '/IVE/NVL/emu']
                addition = ' ' + ' '.join(add)
                m = re.search(r'\s-l\s+\S+', fixed)
                if m:
                    fixed = fixed[:m.start()] + addition + fixed[m.start():]
                else:
                    nl = '\n' if fixed.endswith('\n') else ''
                    fixed = fixed.rstrip('\n').rstrip() + addition + nl
                issues.append(f"BUG-003: added missing {' '.join(add)}")

        # --- grdlbuild -Penv typo ---
        if is_grdlbuild:
            penv_typos = (
                ('-Penv=immidiate',  '-Penv=immediate'),
                ('-Penv=immedate',   '-Penv=immediate'),
                ('-Penv=imediate',   '-Penv=immediate'),
                ('-Penv=immeidate',  '-Penv=immediate'),
            )
            for bad, good in penv_typos:
                if bad in fixed:
                    fixed = fixed.replace(bad, good)
                    issues.append(f"grdlbuild: fixed typo '{bad}' -> '{good}'")

        # --- grdlbuild unknown target (suggestion only) ---
        if is_grdlbuild:
            m = re.search(r':emu_build:zebu:(\S+)', fixed)
            if m:
                tgt = m.group(1)
                # Strip any trailing _post_zcui — that's a valid suffix variant
                base = tgt[:-len('_post_zcui')] if tgt.endswith('_post_zcui') else tgt
                if base not in self.SLE_VALID_TARGETS:
                    # Pick the valid target with the longest common prefix.
                    best = max(self.SLE_VALID_TARGETS,
                               key=lambda v: len(_common_prefix(base, v)))
                    if _common_prefix(base, best):
                        suggestions.append(
                            f"grdlbuild: target '{tgt}' is not a known SLE target. "
                            f"Did you mean ':emu_build:zebu:{best}'? "
                            f"Valid: {', '.join(self.SLE_VALID_TARGETS)}"
                        )

        return fixed, issues, suggestions


    def fix_line(self, line, line_num):
        """Apply all fixes to a single line"""
        original_line = line
        all_issues = []
        suggested_fix = None
        suggestion_desc = None
        
        # Skip comment lines and empty lines
        if line.strip().startswith('#') or not line.strip():
            return line, []
        
        # Check for special/non-printable characters FIRST (before any fixes)
        special_char_issues = self.check_special_characters(original_line, line_num)
        all_issues.extend(special_char_issues)
        
        # Remove special characters if found
        if special_char_issues:
            line, removal_msgs = self.remove_special_characters(line)
            all_issues.extend(removal_msgs)
        
        # Apply fixes in order
        line, issues = self.fix_unpaired_simv_args(line)
        all_issues.extend(issues)

        line, issues = self.fix_unpaired_user_do_files(line)
        all_issues.extend(issues)

        # SLE safety net: -local, EMUL_QSLOT, -P/-Q, -Penv typos, grdlbuild targets.
        line, sle_issues, sle_suggestions = self.fix_sle_safety(line)
        all_issues.extend(sle_issues)
        # SLE suggestions are display-only (no auto-apply for fuzzy target match).
        for s in sle_suggestions:
            all_issues.append(f"⚠ {s}")
        
        line, issues = self.fix_missing_model(line)
        all_issues.extend(issues)
        
        line, issues = self.fix_relative_include_paths(line)
        all_issues.extend(issues)
        
        # If apply_suggested is enabled, iteratively apply ALL suggested fixes
        if self.apply_suggested:
            max_iterations = 10  # Safety limit to prevent infinite loops
            iteration = 0
            current_line = line
            
            while iteration < max_iterations:
                # Validate current state
                warnings = self.validate_paired_switches(current_line)
                if not warnings:
                    break  # No more issues to fix
                
                # Try to generate a suggested fix
                temp_fix = None
                temp_desc = None
                
                # Priority order (most critical to least):
                if any('Missing space between plusargs' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_plusargs_spacing(current_line)
                elif any('Missing space before \'-trex\' opening tag' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_missing_space(current_line, '-trex', 'before', 'open')
                elif any('Missing space before \'-user_do_files_vcs\' opening tag' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_missing_space(current_line, '-user_do_files_vcs', 'before', 'open')
                elif any('Missing space after \'-trex\' opening tag' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_missing_space(current_line, '-trex', 'after', 'open')
                elif any('Missing space after \'-user_do_files_vcs\' opening tag' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_missing_space(current_line, '-user_do_files_vcs', 'after', 'open')
                elif any('Missing space before \'-trex-\' closing tag' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_missing_space(current_line, '-trex', 'before', 'close')
                elif any('Missing space before \'-user_do_files_vcs-\' closing tag' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_missing_space(current_line, '-user_do_files_vcs', 'before', 'close')
                elif any('Missing space after \'-trex-\' closing tag' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_missing_space(current_line, '-trex', 'after', 'close')
                elif any('Missing space after \'-user_do_files_vcs-\' closing tag' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_missing_space(current_line, '-user_do_files_vcs', 'after', 'close')
                elif any('Consecutive -trex tags without closing tag between them' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_consecutive_tags(current_line, '-trex')
                elif any('Consecutive -user_do_files_vcs tags without closing tag between them' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_consecutive_tags(current_line, '-user_do_files_vcs')
                elif any('Consecutive -trex- closing tags' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_consecutive_closes(current_line, '-trex')
                elif any('Consecutive -user_do_files_vcs- closing tags' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_fix_consecutive_closes(current_line, '-user_do_files_vcs')
                elif any('Unbalanced -trex' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_balanced_fix(current_line, '-trex')
                elif any('Unbalanced -user_do_files_vcs' in w for w in warnings):
                    temp_fix, temp_desc = self.suggest_balanced_fix(current_line, '-user_do_files_vcs')
                
                if temp_fix:
                    # Apply this fix and continue
                    current_line = temp_fix
                    if not suggestion_desc:
                        # Save the first fix description for reporting
                        suggestion_desc = temp_desc
                    iteration += 1
                else:
                    # No fixable issues, stop
                    break
            
            # Update line to the fully fixed version
            line = current_line
            suggested_fix = current_line
            if iteration > 1:
                suggestion_desc = f"Applied {iteration} spacing fixes iteratively"
        
        # Validate after fixes and check for remaining issues (for display only)
        warnings = self.validate_paired_switches(line)
        
        # If NOT applying suggested fixes, just generate the first suggestion for display
        if not self.apply_suggested and warnings:
            # Priority order (most critical to least - all spacing errors first):
            # 0. Missing space between plusargs (very common)
            # 1. Missing space before/after opening tags
            # 2. Missing space before/after closing tags
            # 3. Consecutive tags (invalid nesting)
            # 4. Simple imbalance (missing close tags)
            
            # Plusargs spacing issues
            if any('Missing space between plusargs' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_plusargs_spacing(line)
            
            # Opening tag spacing issues
            elif any('Missing space before \'-trex\' opening tag' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_missing_space(line, '-trex', 'before', 'open')
            elif any('Missing space before \'-user_do_files_vcs\' opening tag' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_missing_space(line, '-user_do_files_vcs', 'before', 'open')
            elif any('Missing space after \'-trex\' opening tag' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_missing_space(line, '-trex', 'after', 'open')
            elif any('Missing space after \'-user_do_files_vcs\' opening tag' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_missing_space(line, '-user_do_files_vcs', 'after', 'open')
            
            # Closing tag spacing issues
            elif any('Missing space before \'-trex-\' closing tag' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_missing_space(line, '-trex', 'before', 'close')
            elif any('Missing space before \'-user_do_files_vcs-\' closing tag' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_missing_space(line, '-user_do_files_vcs', 'before', 'close')
            elif any('Missing space after \'-trex-\' closing tag' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_missing_space(line, '-trex', 'after', 'close')
            elif any('Missing space after \'-user_do_files_vcs-\' closing tag' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_missing_space(line, '-user_do_files_vcs', 'after', 'close')
            
            # Structural issues
            elif any('Consecutive -trex tags without closing tag between them' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_consecutive_tags(line, '-trex')
            elif any('Consecutive -user_do_files_vcs tags without closing tag between them' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_consecutive_tags(line, '-user_do_files_vcs')
            elif any('Consecutive -trex- closing tags' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_consecutive_closes(line, '-trex')
            elif any('Consecutive -user_do_files_vcs- closing tags' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_fix_consecutive_closes(line, '-user_do_files_vcs')
            
            # Balance issues
            elif any('Unbalanced -trex' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_balanced_fix(line, '-trex')
            elif any('Unbalanced -user_do_files_vcs' in w for w in warnings):
                suggested_fix, suggestion_desc = self.suggest_balanced_fix(line, '-user_do_files_vcs')
        
        all_issues.extend(warnings)
        
        if all_issues:
            fix_record = {
                'line_num': line_num,
                'original': original_line.strip(),
                'fixed': line.strip(),
                'issues': all_issues
            }
            
            # Store suggested fix if available
            if suggested_fix and suggestion_desc:
                fix_record['suggested_fix'] = suggested_fix.strip()
                fix_record['suggestion_desc'] = suggestion_desc
                
                # If apply_suggested was enabled, the fixes were already applied iteratively above
                if self.apply_suggested:
                    # Update issues to reflect that fixes were applied
                    fix_record['issues'] = [f"📝 Applied suggested fix: {suggestion_desc}"]
            
            self.fixes_applied.append(fix_record)
        
        return line, all_issues
    
    def process(self):
        """Process the testlist file"""
        if not self.testlist_file.exists():
            print(f"✗ Error: File not found: {self.testlist_file}")
            return False
        
        print(f"\n{'='*80}")
        print(f"Simregress Command Fixer")
        print(f"{'='*80}")
        print(f"File: {self.testlist_file}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'FIX'}")
        print(f"{'='*80}\n")
        

        
        # Read and process lines
        lines = self.read_testlist()
        
        # Auto-detect model if enabled
        if self.auto_detect_model:
            self.detected_model = self.auto_detect_model_from_testlist(lines)
            if self.detected_model:
                print(f"ℹ Auto-detected model type: {self.detected_model}")
            else:
                print(f"ℹ No model detected in testlist, using default: {self.default_model}")
            print()
        
        fixed_lines = []
        any_changes_made = False
        
        for line_num, line in enumerate(lines, 1):
            fixed_line, issues = self.fix_line(line, line_num)
            fixed_lines.append(fixed_line)
            
            # Track if any actual changes were made
            if line != fixed_line:
                any_changes_made = True
            
            # Print details for all issues (both dry-run and fix mode)
            if issues:
                # Check if there's a suggested fix for this line
                fix_record = next((f for f in self.fixes_applied if f['line_num'] == line_num), None)
                has_suggestion = fix_record and 'suggested_fix' in fix_record
                
                # Determine if this is a warning or a fix
                has_fixes = any(not issue.startswith('⚠') for issue in issues)
                has_warnings = any(issue.startswith('⚠') for issue in issues)
                
                if has_fixes:
                    icon = "🔧" if self.dry_run else "📝"
                    action = "Would fix" if self.dry_run else "Fixed"
                else:
                    icon = "⚠️"
                    action = "Warning"
                
                # Color the line number for easier differentiation
                if self.no_color:
                    print(f"\n{icon} Line {line_num}:")
                else:
                    print(f"\n{icon} {Colors.CYAN}{Colors.BOLD}Line {line_num}:{Colors.RESET}")
                for issue in issues:
                    if issue.startswith('⚠'):
                        print(f"   {issue}")
                    else:
                        if self.dry_run:
                            print(f"   Would fix: {issue}")
                        else:
                            print(f"   {issue}")
                
                # Determine tag type for highlighting
                tag_type = '-trex'
                if any('user_do_files' in issue for issue in issues):
                    tag_type = '-user_do_files_vcs'
                
                # Show full command with highlighting for warnings
                if has_warnings:
                    # Pass ALL warnings for comprehensive highlighting
                    warning_messages = [issue for issue in issues if issue.startswith('⚠')]
                    self.print_full_command_with_highlight(line, warning_messages, tag_type)
                
                # Show before/after if there were actual fixes (not just warnings)
                if has_fixes and line.strip() != fixed_line.strip():
                    if self.dry_run:
                        print(f"\n   ⚙️  AUTO-FIXES (will be applied when run without --dry-run):")
                        print(f"   Before: {line.strip()}")
                        print(f"   After:  {fixed_line.strip()}")
                    else:
                        print(f"\n   ✅ AUTO-FIXES APPLIED:")
                        print(f"   Before: {line.strip()}")
                        print(f"   After:  {fixed_line.strip()}")
                
                # Show suggested fix if available
                if has_suggestion and has_warnings:
                    print(f"\n   💡 SUGGESTED FIX (requires --apply-suggested flag):")
                    print(f"   {fix_record['suggestion_desc']}")
                    
                    # Highlight the changes in the suggested fix
                    original_for_comparison = fix_record['original']
                    suggested_highlighted = self.highlight_suggested_fix(original_for_comparison, fix_record['suggested_fix'])
                    print(f"\n   Suggested line: {suggested_highlighted}")
                    
                    if self.no_color:
                        print(f"   Legend: >>>changed part<<<")
                    else:
                        print(f"   Legend: {Colors.BG_GREEN}{Colors.WHITE}changed part{Colors.RESET}")
                    
                    if self.dry_run:
                        print(f"\n   💡 Run with --apply-suggested to apply this fix")
                    elif self.apply_suggested:
                        print(f"\n   ✓ Suggested fix was applied!")
        
        # Write fixed content if not dry run AND changes were made
        if not self.dry_run and any_changes_made:
            self.write_testlist(fixed_lines)
            print(f"\n✓ File updated: {self.testlist_file}")
        elif not self.dry_run and not any_changes_made:
            print(f"\nℹ No changes made to file (only warnings detected)")
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print summary of fixes"""
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        
        if not self.fixes_applied:
            print("✓ No issues found!")
            return
        
        # Count issue types
        # Separate actual fixes from warnings
        # Note: Consecutive tags and unbalanced are WARNINGS, only truly fixed if apply_suggested was used
        bucket1_fixed = sum(1 for fix in self.fixes_applied if any(
            'simv_args' in issue and 
            not issue.startswith('⚠') and
            'Applied suggested fix' not in issue
            for issue in fix['issues']))
        bucket1_warnings = sum(1 for fix in self.fixes_applied if any(
            '⚠ Unbalanced -trex' in issue or '⚠ ERROR: Consecutive -trex' in issue 
            for issue in fix['issues']))
        bucket2_fixed = sum(1 for fix in self.fixes_applied if any(
            'user_do_files' in issue and 
            not issue.startswith('⚠') and
            'Applied suggested fix' not in issue
            for issue in fix['issues']))
        bucket2_warnings = sum(1 for fix in self.fixes_applied if any(
            '⚠ Unbalanced -user_do_files' in issue or '⚠ ERROR: Consecutive -user_do_files' in issue
            for issue in fix['issues']))
        bucket3 = sum(1 for fix in self.fixes_applied if any('missing \'-model' in issue for issue in fix['issues']))
        bucket4 = sum(1 for fix in self.fixes_applied if any('relative -include path' in issue for issue in fix['issues']))
        bucket4_warnings = sum(1 for fix in self.fixes_applied if any('Include file not found' in issue for issue in fix['issues']))
        
        # Count suggested fixes that were actually applied
        bucket1_suggested_applied = sum(1 for fix in self.fixes_applied if any(
            'Applied suggested fix' in issue and 'simv_args' in issue
            for issue in fix['issues']))
        bucket2_suggested_applied = sum(1 for fix in self.fixes_applied if any(
            'Applied suggested fix' in issue and 'user_do_files' in issue
            for issue in fix['issues']))
        
        total_fixes = bucket1_fixed + bucket2_fixed + bucket3 + bucket4 + bucket1_suggested_applied + bucket2_suggested_applied
        total_warnings = bucket1_warnings + bucket2_warnings + bucket4_warnings
        
        print(f"Total lines with issues: {len(self.fixes_applied)}")
        print(f"\nIssue breakdown:")
        if bucket1_fixed > 0:
            print(f"  • Bucket 1 (unpaired -trex-): {bucket1_fixed} fixed")
        if bucket2_fixed > 0:
            print(f"  • Bucket 2 (unpaired -user_do_files_vcs-): {bucket2_fixed} fixed")
        if bucket3 > 0:
            print(f"  • Bucket 3 (missing -model): {bucket3} fixed")
        if bucket4 > 0:
            print(f"  • Bucket 4 (relative -include paths): {bucket4} fixed")
        if bucket1_warnings > 0:
            print(f"  • Warnings (unbalanced -trex): {bucket1_warnings} need manual review")
        if bucket2_warnings > 0:
            print(f"  • Warnings (unbalanced -user_do_files_vcs-): {bucket2_warnings} need manual review")
        if bucket4_warnings > 0:
            print(f"  • Warnings (missing include files): {bucket4_warnings} need manual review")
        
        # Count suggested fixes
        suggested_count = sum(1 for f in self.fixes_applied if 'suggested_fix' in f)
        
        if self.dry_run:
            print(f"\n⚠ DRY RUN MODE - No changes were made")
            print(f"   Run without --dry-run to apply fixes")
            if suggested_count > 0:
                print(f"\n💡 {suggested_count} suggested fix(es) available")
                print(f"   Add --apply-suggested to apply these fixes")
        else:
            if self.apply_suggested and suggested_count > 0:
                print(f"\n✓ {suggested_count} suggested fix(es) applied!")
            if total_fixes > 0 and total_warnings > 0:
                if not self.apply_suggested and suggested_count > 0:
                    print(f"\n✓ {total_fixes} fix(es) applied successfully!")
                    print(f"⚠ {total_warnings} warning(s) need manual review")
                    print(f"\n💡 {suggested_count} suggested fix(es) available")
                    print(f"   Run again with --apply-suggested to apply these fixes")
                else:
                    print(f"\n✓ {total_fixes} fix(es) applied successfully!")
                    if total_warnings > 0:
                        print(f"⚠ {total_warnings} warning(s) need manual review")
            elif total_fixes > 0:
                print(f"\n✓ All {total_fixes} fix(es) applied successfully!")
            elif total_warnings > 0:
                if not self.apply_suggested and suggested_count > 0:
                    print(f"\n⚠ No auto-fixes available - {total_warnings} warning(s) detected")
                    print(f"\n💡 {suggested_count} suggested fix(es) available")
                    print(f"   Run with --apply-suggested to apply these fixes")
                else:
                    print(f"\n⚠ No auto-fixes available - {total_warnings} warning(s) need manual review")
            else:
                print(f"\n✓ No issues found!")
        
        print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Fix SLE emulation (simregress / grdlbuild) command errors — NVL_AX, ZeBu ZSE5',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes (default - no file modification)
  %(prog)s reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list

  # Apply automatic fixes only (modify file)
  %(prog)s reglist.list --apply

  # Apply all fixes including suggested (spacing/balance) fixes
  %(prog)s reglist.list --apply-suggested

  # Apply fixes with explicit emu_model
  %(prog)s reglist.list --apply --model pkg_chp_model_p2e4

  # List the 4 valid SLE emu_models / grdlbuild targets
  %(prog)s --list-models

Auto-fixes applied with --apply:
  - Remove unpaired -trex- closing tags
  - Add missing -model / -emu_model argument (auto-detected or specified)
  - Fix relative -include paths (add $WORKAREA/ prefix)
  - Remove invisible/special characters (zero-width, BOM, \\x00, ...)
  - BUG-001: strip forbidden '-local' flag from simregress
  - BUG-002: replace EMUL_QSLOT=.../showstopper with .../emu/interactive
             (and append EMUL_QSLOT=.../emu/interactive if missing from simregress)
  - BUG-003: append missing '-P zsc11_express -Q /IVE/NVL/emu' to simregress
  - grdlbuild: fix -Penv typos (immidiate / immedate / imediate -> immediate)

Additional with --apply-suggested:
  - Balance unbalanced -trex pairs (smart placement)
  - Fix spacing violations around -trex / -trex- tags
  - Fix consecutive opening / closing tags

Suggestions only (never auto-applied):
  - Unknown grdlbuild target -> nearest valid SLE target (manual review)
        """
    )
    
    parser.add_argument('testlist', nargs='?', help='Path to testlist file')
    parser.add_argument('--apply', action='store_true', 
                       help='Apply auto-fixes and modify file (default is preview-only)')
    parser.add_argument('--apply-suggested', action='store_true',
                       help='Apply all fixes including suggested fixes (implies --apply)')

    parser.add_argument('--no-color', action='store_true',
                       help='Disable ANSI color output (for terminals without color support)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--model', '-m', default='pkg_chp_model_p2e4_fast',
                       help='Default emu_model to use if auto-detection fails (default: pkg_chp_model_p2e4_fast)')
    parser.add_argument('--no-auto-detect', action='store_true',
                       help='Disable auto-detection of model type from testlist')
    parser.add_argument('--list-models', action='store_true',
                       help='List common model types and exit')
    parser.add_argument('--workarea', '-w', 
                       help='WORKAREA path for resolving relative includes (default: auto-detect from $WORKAREA or testlist path)')
    
    args = parser.parse_args()
    
    # Handle --list-models
    if args.list_models:
        print("\nNVL_AX SLE Emulation Models (-emu_model values):")
        print("="*70)
        models = [
            ('pkg_ghpf_model',               'GHPF emulation model'),
            ('pkg_chp_model_p2e4_fast',      'CHP fast (ZSE5)'),
            ('pkg_chp_hubs_full_model_p2e4', 'CHP full with hubs (ZSE5)'),
            ('pkg_chp_model_p2e4',           'CHP standard (ZSE5)'),
        ]
        for m, d in models:
            print(f"  • {m:<32s} — {d}")
        print("\ngrdlbuild build targets (add `_zse5` suffix):")
        for m, _ in models:
            print(f"  • {m}_zse5")
        print("\nNote: Auto-detection will use the most common -emu_model found in your testlist.")
        print("      Use --model to override if auto-detection is not suitable.\n")
        return
    
    if not args.testlist:
        parser.error("testlist is required (unless using --list-models)")
    
    # Default is dry-run (preview only) unless --apply or --apply-suggested is specified
    dry_run = not (args.apply or args.apply_suggested)
    
    fixer = SimregressCommandFixer(
        args.testlist,
        dry_run=dry_run,
        default_model=args.model,
        auto_detect_model=not args.no_auto_detect,
        workarea=args.workarea,
        apply_suggested=args.apply_suggested,
        no_color=args.no_color
    )
    
    success = fixer.process()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
