from ....util import FQ, Expression, MAX_N_BYTES, N_BYTES_WORD


def lt(lhs: Expression, rhs: Expression, n_bytes: int) -> FQ:
    assert n_bytes <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
    assert lhs.expr().n < 256**n_bytes, f"lhs {lhs} exceeds the range of {n_bytes} bytes"
    assert rhs.expr().n < 256**n_bytes, f"rhs {rhs} exceeds the range of {n_bytes} bytes"
    return FQ(lhs.expr().n < rhs.expr().n)


def lt_word(lhs: Expression, rhs: Expression, n_bytes: int) -> FQ:
    assert n_bytes <= N_BYTES_WORD, "Too many bytes to composite an integer in field"
    assert lhs.expr().n < 256**n_bytes, f"lhs {lhs} exceeds the range of {n_bytes} bytes"
    assert rhs.expr().n < 256**n_bytes, f"rhs {rhs} exceeds the range of {n_bytes} bytes"
    return FQ(lhs.expr().n < rhs.expr().n)
