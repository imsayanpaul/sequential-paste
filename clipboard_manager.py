"""
Clipboard Manager - Core logic for sequential paste functionality
"""
import re
import threading
import functools
from typing import Optional, List
from config import DELIMITER_PATTERNS, DelimiterType, DEFAULT_DELIMITER, ABBREVIATIONS


def _locked(method):
    """Run the method while holding the manager's lock"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)
    return wrapper


class ClipboardManager:
    """Manages clipboard content and sequential paste state"""
    
    def __init__(self):
        self.current_content: str = ""
        self.segments: List[str] = []
        self.current_index: int = 0
        self.delimiter: DelimiterType = DEFAULT_DELIMITER
        # State is shared by the hotkey worker, clipboard monitor and tray threads
        self.lock = threading.RLock()
    
    @_locked
    def set_delimiter(self, delimiter: DelimiterType) -> None:
        """Change the delimiter type and re-parse content"""
        self.delimiter = delimiter
        if self.current_content:
            self._parse_content()
            self.current_index = 0
    
    @_locked
    def load_text(self, text: str) -> None:
        """
        Load text directly and always reset sequence.
        Used by clipboard monitor to handle all copies including re-copies.
        """
        if not text:
            return
        self.current_content = text
        self._parse_content()
        self.current_index = 0
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Smart sentence splitting that handles edge cases:
        - Abbreviations (Mr., Mrs., Dr., etc.)
        - Initials (J.K., A.B.C.)
        - Ellipsis (...)
        - Decimals (3.14, $19.99)
        - URLs (www.example.com)
        - Emails (user@test.com)
        - File extensions (.pdf, .txt)
        - Numbered lists (1. 2. 3.)
        - Hindi purna viram (।)
        - Chinese/Japanese period (。)
        """
        # Placeholders for protected patterns
        ABBR_PH = "\x00ABBR\x00"
        ELLIPSIS_PH = "\x00ELLIPSIS\x00"
        DECIMAL_PH = "\x00DECIMAL\x00"
        URL_PH = "\x00URL\x00"
        EMAIL_PH = "\x00EMAIL\x00"
        INITIAL_PH = "\x00INITIAL\x00"
        NUMLIST_PH = "\x00NUMLIST\x00"
        
        protected_text = text
        
        # 1. Protect ellipsis (... or …)
        protected_text = re.sub(r'\.\.\.', ELLIPSIS_PH, protected_text)
        protected_text = protected_text.replace('…', ELLIPSIS_PH)
        
        # 2. Protect URLs (www.example.com, http://example.com)
        # The URL must not end in punctuation, so "Visit www.example.com. Next"
        # still splits after the URL.
        protected_text = re.sub(
            r'(https?://[^\s]*[^\s.,;:!?)\'"]|www\.[^\s]*[^\s.,;:!?)\'"])',
            lambda m: m.group().replace('.', URL_PH),
            protected_text
        )
        
        # 3. Protect emails (user@domain.com)
        protected_text = re.sub(
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            lambda m: m.group().replace('.', EMAIL_PH),
            protected_text
        )
        
        # 4. Protect decimals and currency ($19.99, 3.14, 1.5)
        protected_text = re.sub(
            r'(\d+)\.(\d+)',
            rf'\1{DECIMAL_PH}\2',
            protected_text
        )
        
        # 5. Protect numbered lists (1. 2. 3. at start of a line only, so a
        # sentence ending in a number like "I bought 5." still splits)
        protected_text = re.sub(
            r'(^|\n)([ \t]*\d{1,3})\.',
            rf'\1\2{NUMLIST_PH}',
            protected_text
        )
        
        # 6. Protect initials (single capital letters followed by period)
        # Matches: J.K., A.B.C., U.S.A.
        protected_text = re.sub(
            r'\b([A-Z])\.(?=[A-Z]\.|\s|$)',
            rf'\1{INITIAL_PH}',
            protected_text
        )
        
        # 7. Protect abbreviations
        # Case-sensitive on purpose: with IGNORECASE, "The answer is no." was
        # treated as the abbreviation "No." and never split.
        for abbr in ABBREVIATIONS:
            pattern = rf'\b({re.escape(abbr)})\.'
            protected_text = re.sub(pattern, rf'\1{ABBR_PH}', protected_text)

        # Now split on sentence-ending punctuation
        # Supports: . ! ? । (Hindi) 。！？ (Chinese/Japanese) ؟ (Arabic)
        # Use a more Unicode-friendly approach: insert delimiter then split
        SPLIT_MARKER = "\x00SPLIT\x00"

        # Insert split marker after sentence-ending punctuation followed by:
        # - whitespace, OR
        # - uppercase letter (handles missing space typos like "working.I am")
        protected_text = re.sub(
            r'([.!?।؟])(\s+|(?=[A-Z]))',
            rf'\1{SPLIT_MARKER}',
            protected_text
        )
        # CJK full-width punctuation is normally not followed by a space
        protected_text = re.sub(
            r'([。！？])\s*',
            rf'\1{SPLIT_MARKER}',
            protected_text
        )
        
        # Split on the marker
        sentences = protected_text.split(SPLIT_MARKER)
        
        # Restore all placeholders
        final_sentences = []
        for sent in sentences:
            restored = sent
            restored = restored.replace(ABBR_PH, '.')
            restored = restored.replace(ELLIPSIS_PH, '...')
            restored = restored.replace(DECIMAL_PH, '.')
            restored = restored.replace(URL_PH, '.')
            restored = restored.replace(EMAIL_PH, '.')
            restored = restored.replace(INITIAL_PH, '.')
            restored = restored.replace(NUMLIST_PH, '.')
            if restored.strip():
                final_sentences.append(restored.strip())
        
        return final_sentences
    
    def _split_cells(self, text: str) -> List[str]:
        """
        Split spreadsheet cells (tab-separated, one row per line), row by row.
        Empty cells inside a row are kept so that with "After each item: Tab"
        every cell still lands in its own form field. Blank rows are dropped.
        """
        cells = []
        for row in text.split('\n'):
            row = row.rstrip('\r')
            if not row.strip():
                continue
            cells.extend(cell.strip() for cell in row.split('\t'))
        return cells

    def _parse_content(self) -> None:
        """Split current content into segments based on delimiter"""
        if not self.current_content:
            self.segments = []
            return
        
        if self.delimiter == DelimiterType.SENTENCE:
            # Use smart sentence splitting
            self.segments = self._split_sentences(self.current_content)
        elif self.delimiter == DelimiterType.TAB:
            self.segments = self._split_cells(self.current_content)
        else:
            pattern = DELIMITER_PATTERNS.get(self.delimiter)
            if pattern:
                # Split and filter out empty segments
                raw_segments = re.split(pattern, self.current_content)
                self.segments = [seg.strip() for seg in raw_segments if seg.strip()]
            else:
                self.segments = [self.current_content]
    
    @_locked
    def get_next_segment(self) -> Optional[str]:
        """
        Get the next segment in sequence.
        Returns None if sequence is exhausted.
        """
        if self.is_exhausted():
            return None
        
        segment = self.segments[self.current_index]
        self.current_index += 1
        return segment
    
    @_locked
    def peek_next_segment(self) -> Optional[str]:
        """Preview the next segment without advancing the index"""
        if self.is_exhausted():
            return None
        return self.segments[self.current_index]
    
    @_locked
    def reset(self) -> None:
        """Reset sequence index to start"""
        self.current_index = 0
    
    @_locked
    def skip_segment(self) -> bool:
        """
        Skip the current segment without pasting.
        Returns True if skipped, False if already exhausted.
        """
        if self.is_exhausted():
            return False
        self.current_index += 1
        return True
    
    @_locked
    def go_back(self) -> bool:
        """
        Go back to the previous segment.
        Returns True if went back, False if already at start.
        """
        if self.current_index <= 0:
            return False
        self.current_index -= 1
        return True
    
    @_locked
    def is_exhausted(self) -> bool:
        """Check if all segments have been pasted"""
        return self.current_index >= len(self.segments)
    
    @_locked
    def get_position(self) -> tuple:
        """Get current position as (current, total)"""
        return (self.current_index, len(self.segments))
    
    @_locked
    def get_remaining_count(self) -> int:
        """Get number of segments remaining"""
        return max(0, len(self.segments) - self.current_index)
    
    @property
    def total_segments(self) -> int:
        """Total number of segments"""
        return len(self.segments)
    
    @property
    def has_content(self) -> bool:
        """Check if there is any content loaded"""
        return len(self.segments) > 0
