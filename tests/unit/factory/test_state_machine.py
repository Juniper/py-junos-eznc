import unittest
import warnings

import pyparsing as pp

from jnpr.junos.factory.state_machine import (
    Identifiers,
    convert_to_data_type,
    data_type,
)


class TestIdentifiersNumbers(unittest.TestCase):
    """Tests for Identifiers.numbers (set_parse_action joining integer/float parts)."""

    def test_numbers_parses_integer(self):
        result = Identifiers.numbers.parseString("42", parseAll=True)
        self.assertEqual(result[0], "42")

    def test_numbers_parses_float(self):
        result = Identifiers.numbers.parseString("3.14", parseAll=True)
        self.assertEqual(result[0], "3.14")

    def test_numbers_parse_action_joins_parts(self):
        # "1.5" is tokenised as ["1", ".", "5"]; parse action must join to "1.5"
        result = Identifiers.numbers.parseString("1.5", parseAll=True)
        self.assertIsInstance(result[0], str)
        self.assertEqual(result[0], "1.5")

    def test_numbers_parse_action_single_token(self):
        # Integer: only one token, join should be a no-op
        result = Identifiers.numbers.parseString("0", parseAll=True)
        self.assertEqual(result[0], "0")

    def test_numbers_rejects_non_numeric(self):
        with self.assertRaises(pp.ParseException):
            Identifiers.numbers.parseString("abc", parseAll=True)

    def test_numbers_no_deprecation_warning(self):
        """Ensure no PyparsingDeprecationWarning is raised when using the identifier."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Identifiers.numbers.parseString("99", parseAll=True)
        pyparsing_warnings = [
            w
            for w in caught
            if issubclass(w.category, DeprecationWarning)
            and "setParseAction" in str(w.message)
        ]
        self.assertEqual(pyparsing_warnings, [])


class TestIdentifiersWords(unittest.TestCase):
    """Tests for Identifiers.words (set_parse_action joining tokens with spaces)."""

    def test_words_parses_single_word(self):
        result = Identifiers.words.parseString("hello", parseAll=True)
        self.assertEqual(result[0], "hello")

    def test_words_parses_multiple_words(self):
        result = Identifiers.words.parseString("hello world", parseAll=True)
        self.assertEqual(result[0], "hello world")

    def test_words_parse_action_joins_with_space(self):
        result = Identifiers.words.parseString("foo bar baz", parseAll=True)
        self.assertIsInstance(result[0], str)
        self.assertEqual(result[0], "foo bar baz")

    def test_words_no_deprecation_warning(self):
        """Ensure no PyparsingDeprecationWarning is raised when using the identifier."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Identifiers.words.parseString("test words", parseAll=True)
        pyparsing_warnings = [
            w
            for w in caught
            if issubclass(w.category, DeprecationWarning)
            and "setParseAction" in str(w.message)
        ]
        self.assertEqual(pyparsing_warnings, [])


class TestDataType(unittest.TestCase):
    """Tests for data_type() which relies on Identifiers.numbers internally."""

    def test_data_type_integer(self):
        self.assertEqual(data_type("42"), int)

    def test_data_type_float(self):
        self.assertEqual(data_type("3.14"), float)

    def test_data_type_hex_string(self):
        self.assertEqual(data_type("1a2b"), str)

    def test_data_type_plain_string(self):
        self.assertEqual(data_type("hello"), str)


class TestConvertToDataType(unittest.TestCase):
    """Tests for convert_to_data_type() which uses data_type() internally."""

    def test_converts_integer_item(self):
        result = convert_to_data_type(["5"])
        self.assertEqual(result, [5])

    def test_converts_mixed_items(self):
        result = convert_to_data_type(["10", "host"])
        self.assertEqual(result, [10, "host"])

    def test_converts_string_items(self):
        result = convert_to_data_type(["hello", "world"])
        self.assertEqual(result, ["hello", "world"])


if __name__ == "__main__":
    unittest.main()
