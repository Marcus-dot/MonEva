"""
Safe formula evaluator for FORMULA-type indicators.

Supports: +  -  *  /  //  %  **  ( )  and numeric literals.
Variables must be {uuid} placeholders resolved before calling evaluate().

Usage:
    from indicators.formula import evaluate_formula, validate_formula, resolve_formula

    # Resolve {indicator_id} placeholders to their latest values
    result = resolve_formula(formula_str, target, project)

    # Pure evaluation with a pre-resolved expression like "12.5 + 7"
    value = evaluate_formula("12.5 + 7")

    # Validate a formula string before saving
    ok, error = validate_formula("{abc} + {def}", ["{abc}", "{def}"])
"""

import re
import ast
import operator

# ── Safe AST evaluator ────────────────────────────────────────────────────────

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_MAX_RESULT = 1e15   # Sanity cap — prevents absurd indicator values


def evaluate_formula(expression: str) -> float:
    """
    Safely evaluate a numeric arithmetic expression string.
    Only allows numbers and the operators above — no builtins, no names.

    Raises:
        ValueError: If expression is invalid or unsafe.
        ZeroDivisionError: On division by zero.
    """
    expression = expression.strip()
    if not expression:
        raise ValueError("Empty expression")

    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as e:
        raise ValueError(f"Syntax error in formula: {e}")

    result = _eval_node(tree.body)

    if abs(result) > _MAX_RESULT:
        raise ValueError(f"Formula result {result} exceeds allowed maximum")

    return result


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"Unsupported constant type: {type(node.value)}")
        return float(node.value)

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _ALLOWED_OPS[op_type](left, right)

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _eval_node(node.operand)
        return _ALLOWED_OPS[op_type](operand)

    else:
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


# ── Placeholder resolution ────────────────────────────────────────────────────

_UUID_PATTERN = re.compile(r'\{([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\}')


def resolve_formula(formula: str, target, project) -> float:
    """
    Replace {indicator_uuid} placeholders in formula with their latest
    verified result values (or baseline if no results yet), then evaluate.

    Args:
        formula: Raw formula string e.g. "{uuid1} / {uuid2} * 100"
        target: IndicatorTarget instance (the owner of this formula indicator)
        project: Project instance

    Returns:
        float: Calculated value

    Raises:
        ValueError: On formula error or missing indicators
    """
    from .models import IndicatorTarget

    placeholders = _UUID_PATTERN.findall(formula)
    if not placeholders:
        return evaluate_formula(formula)

    # Fetch all targets for this project in one query
    all_targets = IndicatorTarget.objects.filter(
        project=project
    ).select_related('indicator').prefetch_related('results')

    target_map = {str(t.indicator.id): t for t in all_targets}

    resolved = formula
    for ind_id in placeholders:
        ref_target = target_map.get(ind_id)
        if ref_target is None or str(ref_target.id) == str(target.id):
            val = 0.0
        else:
            latest = ref_target.results.filter(status='VERIFIED').order_by('-date').first()
            val = float(latest.value) if latest else float(ref_target.baseline_value)
        resolved = resolved.replace(f'{{{ind_id}}}', str(val))

    return evaluate_formula(resolved)


# ── Validation helper ─────────────────────────────────────────────────────────

def validate_formula(formula: str, known_placeholder_ids: list[str] | None = None) -> tuple[bool, str]:
    """
    Validate a formula string for syntax and placeholder correctness.

    Returns:
        (True, '') on success
        (False, error_message) on failure
    """
    if not formula.strip():
        return False, "Formula cannot be empty."

    placeholders = _UUID_PATTERN.findall(formula)

    # Replace all placeholders with a dummy value and try to evaluate
    test_expr = formula
    for ph in placeholders:
        test_expr = test_expr.replace(f'{{{ph}}}', '1')

    # Remove any remaining braces (non-UUID placeholders = error)
    if '{' in test_expr or '}' in test_expr:
        return False, "Formula contains invalid placeholder format. Use {uuid} notation."

    try:
        evaluate_formula(test_expr)
    except ValueError as e:
        return False, str(e)
    except ZeroDivisionError:
        pass  # Division by zero is only an issue at runtime with real values

    return True, ''
