import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clipboard_manager import ClipboardManager
from config import DelimiterType


def split(text, delimiter):
    manager = ClipboardManager()
    manager.set_delimiter(delimiter)
    manager.load_text(text)
    return manager.segments


class SentenceSplittingTest(unittest.TestCase):
    CASES = {
        'Hello. How are you? Fine!': ['Hello.', 'How are you?', 'Fine!'],
        'The answer is no. We move on.': ['The answer is no.', 'We move on.'],
        'Mr. Smith went to Washington. He arrived.':
            ['Mr. Smith went to Washington.', 'He arrived.'],
        'Visit www.example.com. Then go.': ['Visit www.example.com.', 'Then go.'],
        'See https://x.com/a.html, then stop. Ok.':
            ['See https://x.com/a.html, then stop.', 'Ok.'],
        'Email me at a.b@x.com. Thanks.': ['Email me at a.b@x.com.', 'Thanks.'],
        'Pi is 3.14. Cool.': ['Pi is 3.14.', 'Cool.'],
        'I bought 5. Then I left.': ['I bought 5.', 'Then I left.'],
        'J.K. Rowling wrote it. Yes.': ['J.K. Rowling wrote it.', 'Yes.'],
        'Wait... really? Yes.': ['Wait... really?', 'Yes.'],
        'Use e.g. this one. Done.': ['Use e.g. this one.', 'Done.'],
        'It was working.I am sure.': ['It was working.', 'I am sure.'],
        '1. Buy milk\n2. Buy eggs': ['1. Buy milk\n2. Buy eggs'],
        '你好。我很好。': ['你好。', '我很好。'],
        'नमस्ते। आप कैसे हैं?': ['नमस्ते।', 'आप कैसे हैं?'],
    }

    def test_cases(self):
        for text, expected in self.CASES.items():
            with self.subTest(text=text):
                self.assertEqual(split(text, DelimiterType.SENTENCE), expected)


class OtherDelimitersTest(unittest.TestCase):
    def test_lines(self):
        self.assertEqual(split('a\r\nb\n\n  c  ', DelimiterType.LINE), ['a', 'b', 'c'])

    def test_commas(self):
        self.assertEqual(split('apple, banana,cherry,', DelimiterType.COMMA),
                         ['apple', 'banana', 'cherry'])

    def test_paragraphs(self):
        self.assertEqual(split('p1\nx\r\n\r\np2', DelimiterType.PARAGRAPH), ['p1\nx', 'p2'])

    def test_tabs_split_cells_row_by_row(self):
        # What Excel / Google Sheets put on the clipboard for a 2x3 range
        text = 'Name\tCity\tAge\r\nPriya\tBengaluru\t31\r\n'
        self.assertEqual(split(text, DelimiterType.TAB),
                         ['Name', 'City', 'Age', 'Priya', 'Bengaluru', '31'])

    def test_tabs_keep_empty_cells_drop_blank_rows(self):
        text = 'a\t\tc\n\n\td\n'
        self.assertEqual(split(text, DelimiterType.TAB), ['a', '', 'c', '', 'd'])

    def test_changing_delimiter_resplits_and_restarts(self):
        manager = ClipboardManager()
        manager.load_text('a, b\nc')
        manager.get_next_segment()
        manager.set_delimiter(DelimiterType.COMMA)
        self.assertEqual(manager.segments, ['a', 'b\nc'])
        self.assertEqual(manager.get_position(), (0, 2))


class NavigationTest(unittest.TestCase):
    def setUp(self):
        self.manager = ClipboardManager()
        self.manager.load_text('one\ntwo\nthree')

    def test_walks_through_then_stops(self):
        got = [self.manager.get_next_segment() for _ in range(4)]
        self.assertEqual(got, ['one', 'two', 'three', None])
        self.assertTrue(self.manager.is_exhausted())

    def test_skip_back_reset(self):
        self.assertTrue(self.manager.skip_segment())
        self.assertEqual(self.manager.peek_next_segment(), 'two')
        self.assertTrue(self.manager.go_back())
        self.assertFalse(self.manager.go_back())
        self.manager.get_next_segment()
        self.manager.reset()
        self.assertEqual(self.manager.get_position(), (0, 3))

    def test_new_copy_restarts(self):
        self.manager.get_next_segment()
        self.manager.load_text('x\ny')
        self.assertEqual(self.manager.get_position(), (0, 2))

    def test_empty_text_is_ignored(self):
        self.manager.load_text('')
        self.assertEqual(self.manager.total_segments, 3)


if __name__ == '__main__':
    unittest.main()
