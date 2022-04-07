
We denote `X.curr()` and `X.prev()` for current row and previous row for column X. If curr or prev is unspecified for a column, we refer to the cell at the current row.

```python
# state: 25 cols/words that the current keccak_f works on
# input: 17 cols/words that the current keccak_f works on
def keccak_f(state_tag):
    # if the previous keccak_f is marked as finalized, we need to initialize the state
    state_base13 = (state_tag.prev() == Tag.Finalize) * convert_base(
        input.curr(), _from=2, _to=13
    )

    # if the previous keccak_f is NOT marked as finalized, we need to absorb the current input from the previous output
    # if we are at the finalize step, use the padded input, otherwise, simply use the current input.
    _input = input.curr() + (state_tag.curr() == Tag.Finalize) * padded_input.curr()
    state_base9 = (state_tag.prev() != Tag.Finalize) * absorb(state_base9.prev(), _input)
    state_base13 = (state_tag.prev() != Tag.Finalize) * convert_base(state_base9, _from=9, _to=13)
    # apply 24th of the round constant which was not completed in previous round
    state_base13 = (state_tag != Tag.Init) * iota_base13(state_base13)

    # The core permutation
    # first 23 rounds
    for _ in range(23):
        state_base13 = theta(state_base13)
        state_base9 = rho(state_base13)
        state_base9 = pi(state_base9)
        state_base9 = xi(state_base9)
        state_base9 = iota_base9(state_base9)
        state_base13 = convert_base(state_b9, _from=9, _to=13)
    # The 24-th round we do iota different
    state_base13 = theta(state_base13)
    state_base9 = rho(state_base13)
    state_base9 = pi(state_base9)
    state_base9 = xi(state_base9)
    # The case of Finalize
    state_base9 = (state_tag == Tag.Finalize) * iota_base9(state_base9) 
    curr.out_state_base2 = (state_tag == Tag.Finalize) * convert_base(
        state_base9, _from=9, _to=2
    )
    # In the case of not finalizing, we leave the next round to complete the last iota
```
