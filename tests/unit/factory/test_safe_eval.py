import unittest

from jnpr.junos.factory.safe_eval import (
    UnsafeExpressionError,
    eval_expression,
    eval_jinja_expression,
)


class TestSafeEval(unittest.TestCase):
    def test_eval_expression_allows_arithmetic(self):
        self.assertEqual(eval_expression("(a + b) * 2", {"a": 3, "b": 4}), 14)

    def test_eval_expression_blocks_import(self):
        with self.assertRaises(UnsafeExpressionError):
            eval_expression("__import__('os').system('id')")

    def test_eval_jinja_expression_supports_items_isinstance_and_in(self):
        expr = (
            "sum([v['total'] for k, v in {{ data }}.items() "
            "if isinstance(v, dict) and 'total' in v])"
        )
        data = {"a": {"total": 2}, "b": {"total": 5}, "skip": "x"}
        self.assertEqual(eval_jinja_expression(expr, {"data": data}), 7)

    def test_eval_jinja_expression_supports_endswith_filter(self):
        expr = "sum([v['n'] for k, v in {{ data }}.items() if k.endswith('_0')])"
        data = {"wan_0": {"n": 3}, "fab_1": {"n": 8}, "fab_0": {"n": 4}}
        self.assertEqual(eval_jinja_expression(expr, {"data": data}), 7)


if __name__ == "__main__":
    unittest.main()
