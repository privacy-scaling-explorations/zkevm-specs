from typing import Optional

from .arithmetic import Expression, FQ
from .param import MAX_N_BYTES


class ConstraintUnsatFailure(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class ConstraintSystem:
    cond: Optional[Expression]

    def __init__(self, cond: Optional[Expression] = None):
        self.cond = cond

    def __enter__(self):
        return self

    def __exit__(self, e_type, e_value, traceback):
        if e_type is not None:
            raise e_value
        self.cond = None
        return self

    def _eval(self, expr: Expression):
        if self.cond:
            return self.cond.expr() * expr.expr()
        return expr.expr()

    def constrain_equal(self, lhs: Expression, rhs: Expression):
        assert self._eval(lhs.expr() - rhs.expr()) == 0, ConstraintUnsatFailure(
            f"Expected values to be equal, but got {lhs} and {rhs}"
        )

    def constrain_zero(self, value: Expression):
        assert self._eval(value) == 0, ConstraintUnsatFailure(
            f"Expected value to be 0, but got {value}"
        )

    def constrain_bool(self, value: Expression):
        assert self._eval(value) in [0, 1], ConstraintUnsatFailure(
            f"Expected value to be a bool, but got {value}"
        )

    def is_zero(self, value: Expression) -> FQ:
        return FQ(value.expr() == 0)

    def is_equal(self, lhs: Expression, rhs: Expression) -> FQ:
        return self.is_zero(lhs.expr() - rhs.expr())

    def range_check(self, value: Expression, n_bytes: int) -> bytes:
        assert n_bytes <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
        try:
            return value.expr().n.to_bytes(n_bytes, "little")
        except OverflowError:
            raise ConstraintUnsatFailure(f"Value {value} has too many bytes to fit {n_bytes} bytes")

    def condition(self, cond: Expression):
        assert self.cond is None, "Don't support recursive conditions"
        self.cond = cond
        return self
