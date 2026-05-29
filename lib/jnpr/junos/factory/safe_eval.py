import ast
import re

from jinja2 import Template, meta


class UnsafeExpressionError(ValueError):
    pass


SAFE_FUNCTIONS = {
    "sum": sum,
    "len": len,
    "min": min,
    "max": max,
    "abs": abs,
    "isinstance": isinstance,
    "dict": dict,
}

SAFE_METHODS = {"values", "items", "keys", "endswith", "get"}

SAFE_BINOPS = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
)
SAFE_UNARYOPS = (ast.UAdd, ast.USub, ast.Not)
SAFE_BOOLOPS = (ast.And, ast.Or)
SAFE_CMPOPS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn)


def _extract_target_names(target):
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names = set()
        for elt in target.elts:
            names.update(_extract_target_names(elt))
        return names
    return set()


class _ExpressionValidator(ast.NodeVisitor):
    def __init__(self, allowed_names):
        self.allowed_names = set(allowed_names)
        self._locals = []

    def _is_local(self, name):
        return any(name in local_names for local_names in self._locals)

    def _is_allowed_load_name(self, name):
        return (
            name in self.allowed_names or name in SAFE_FUNCTIONS or self._is_local(name)
        )

    def visit_Expression(self, node):
        self.visit(node.body)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and not self._is_allowed_load_name(node.id):
            raise UnsafeExpressionError("Unsafe name in eval expression")

    def visit_Constant(self, node):
        return

    def visit_List(self, node):
        for elt in node.elts:
            self.visit(elt)

    def visit_Tuple(self, node):
        for elt in node.elts:
            self.visit(elt)

    def visit_Set(self, node):
        for elt in node.elts:
            self.visit(elt)

    def visit_Dict(self, node):
        for key in node.keys:
            if key is not None:
                self.visit(key)
        for value in node.values:
            self.visit(value)

    def visit_BinOp(self, node):
        if not isinstance(node.op, SAFE_BINOPS):
            raise UnsafeExpressionError("Unsafe binary operator in eval expression")
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node):
        if not isinstance(node.op, SAFE_UNARYOPS):
            raise UnsafeExpressionError("Unsafe unary operator in eval expression")
        self.visit(node.operand)

    def visit_BoolOp(self, node):
        if not isinstance(node.op, SAFE_BOOLOPS):
            raise UnsafeExpressionError("Unsafe boolean operator in eval expression")
        for value in node.values:
            self.visit(value)

    def visit_Compare(self, node):
        if any(not isinstance(op, SAFE_CMPOPS) for op in node.ops):
            raise UnsafeExpressionError("Unsafe comparison in eval expression")
        self.visit(node.left)
        for comparator in node.comparators:
            self.visit(comparator)

    def visit_IfExp(self, node):
        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.visit(node.slice)

    def visit_Slice(self, node):
        if node.lower is not None:
            self.visit(node.lower)
        if node.upper is not None:
            self.visit(node.upper)
        if node.step is not None:
            self.visit(node.step)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id not in SAFE_FUNCTIONS:
                raise UnsafeExpressionError("Unsafe call in eval expression")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr not in SAFE_METHODS:
                raise UnsafeExpressionError("Unsafe method call in eval expression")
            if node.func.attr.startswith("_"):
                raise UnsafeExpressionError("Unsafe method call in eval expression")
            if isinstance(node.func.value, ast.Attribute):
                raise UnsafeExpressionError("Unsafe attribute chain in eval expression")
            self.visit(node.func.value)
        else:
            raise UnsafeExpressionError("Unsafe call in eval expression")

        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            if keyword.arg is None:
                raise UnsafeExpressionError("Unsafe call arguments in eval expression")
            self.visit(keyword.value)

    def visit_ListComp(self, node):
        self._visit_comprehension(node, node.elt)

    def visit_SetComp(self, node):
        self._visit_comprehension(node, node.elt)

    def visit_GeneratorExp(self, node):
        self._visit_comprehension(node, node.elt)

    def visit_DictComp(self, node):
        self._visit_comprehension(node, (node.key, node.value))

    def _visit_comprehension(self, node, body):
        local_names = set()
        for generator in node.generators:
            local_names.update(_extract_target_names(generator.target))

        self._locals.append(local_names)
        try:
            for generator in node.generators:
                if generator.is_async:
                    raise UnsafeExpressionError("Async comprehensions are not allowed")
                self.visit(generator.iter)
                for condition in generator.ifs:
                    self.visit(condition)

            if isinstance(body, tuple):
                for item in body:
                    self.visit(item)
            else:
                self.visit(body)
        finally:
            self._locals.pop()

    def visit_Attribute(self, node):
        raise UnsafeExpressionError("Unsafe attribute access in eval expression")

    def generic_visit(self, node):
        raise UnsafeExpressionError(
            "Unsafe expression element: %s" % node.__class__.__name__
        )


def coerce_expression_value(value):
    if isinstance(value, str):
        stripped = value.strip()
        if re.match(r"^-?\d+$", stripped):
            return int(stripped)
        if re.match(r"^-?(\d+\.\d*|\d*\.\d+)$", stripped):
            return float(stripped)
        return value
    if isinstance(value, list):
        return [coerce_expression_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(coerce_expression_value(item) for item in value)
    if isinstance(value, set):
        return {coerce_expression_value(item) for item in value}
    if isinstance(value, dict):
        return {
            coerce_expression_value(key): coerce_expression_value(val)
            for key, val in value.items()
        }
    return value


def eval_expression(expression, names=None):
    names = names or {}
    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError as ex:
        raise UnsafeExpressionError(str(ex))

    _ExpressionValidator(names.keys()).visit(parsed)
    scope = dict(SAFE_FUNCTIONS)
    scope.update(names)
    # Comprehensions in Python 3 resolve names from globals, not locals.
    # Provide the same safe scope in globals to keep behavior consistent.
    safe_globals = {"__builtins__": {}}
    safe_globals.update(scope)
    return eval(compile(parsed, "<safe-eval>", "eval"), safe_globals, scope)


def eval_jinja_expression(expression, context):
    template = Template(expression)
    if isinstance(expression, str):
        variables = sorted(
            meta.find_undeclared_variables(template.environment.parse(expression))
        )
    else:
        variables = sorted(meta.find_undeclared_variables(expression))

    placeholder_context = {}
    eval_names = {}
    for index, var_name in enumerate(variables):
        placeholder = "__val_%s" % index
        placeholder_context[var_name] = placeholder
        if callable(context):
            value = context(var_name)
        else:
            value = context.get(var_name)
        eval_names[placeholder] = coerce_expression_value(value)

    rendered_expression = template.render(placeholder_context)
    # Preserve legacy patterns like "'{{ cpu }}'[:-1]" by converting
    # quoted placeholders to bare variable names bound in eval_names.
    rendered_expression = re.sub(r"([\"'])(__val_\d+)\1", r"\2", rendered_expression)
    return eval_expression(rendered_expression, names=eval_names)
