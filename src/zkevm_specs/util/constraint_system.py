from .arithmetic import Expression, FQ


class ConstraintUnsatFailure(Exception):
    def __init__(self, message: str) -> None:
        self.message = message



def constrain_zero(self, value: Expression):
        assert value.expr() == 0, ConstraintUnsatFailure(f"Expected value to be 0, but got {value}")

def constrain_equal(self, lhs: Expression, rhs: Expression):
    assert lhs.expr() == rhs.expr(), ConstraintUnsatFailure(
        f"Expected values to be equal, but got {lhs} and {rhs}"
    )

def constrain_bool(self, num: Expression):
    assert num.expr() in [0, 1], ConstraintUnsatFailure(
        f"Expected value to be a bool, but got {num}"
    )

# class ConstraintUnsatFailure(Exception):
#     def __init__(self, message: str) -> None:
#         self.message = message


class ConstraintSystem:
    condition: Expression

    def __init__(self, condition: Expression = None):
        self.cond = condition

    def __enter__(self):
        print('enter')
        return self

    def __exit__(self, type, value, traceback):
        self.cond = None
        return self

    def _eval(self, expr: Expression):
        if self.cond:
            return self.cond.expr() * expr.expr()
        return expr.expr()

    def constrain_equal(self, lhs: Expression, rhs: Expression):
        assert self._eval(lhs - rhs) == 0, ConstraintUnsatFailure(
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

    def condition(self, condition: Expression) -> FQ:
        assert self.cond is None, "Don't support recursive conditions"
        self.cond = condition
        print('here', self)
        return self
