# MUL, DIV, and MOD opcodes

## Procedure

### EVM behavior

Pop two EVM words `a` and `b` from the stack, and push `c` to the stack, where `c` is computed as

- for opcode `MUL`, compute `c = (a * b) % 2^256`
- for opcode `DIV`, compute `c = a // b` when `b != 0` otherwise `c = 0`
- for opcode `MOD`, compute `c = a mod b` when `b != 0` otherwise `c = 0`

### Circuit behavior

To prove the `MUL/DIV/MOD` opcode, we first construct a `MulAddWordsGadget` that proves `a * b + c = d (mod 2^256)` where `a, b, c, d` are all 256-bit words.
As usual, we use 32 cells to represent each word shown as the table below, where
each cell holds a 8-bit value.

| 0  |  1 |  2 | 3  |  $\dots$  | 8  | $\dots$ |  31 |
|:---:|:---:|:---:|:---:|:--:|:--:|:--:|:--:|
|$a_0$|$a_1$|$a_2$|$a_3$| $\dots$ |$a_8$| $\dots$ |$a_{31}$|
|$b_0$|$b_1$|$b_2$|$b_3$| $\dots$ |$b_8$| $\dots$ |$b_{31}$|
|$c_0$|$c_1$|$c_2$|$c_3$| $\dots$ |$c_8$| $\dots$ |$c_{31}$|
|$d_0$|$d_1$|$d_2$|$d_3$| $\dots$ |$d_8$| $\dots$ |$d_{31}$|

We then combine $a$ and $b$ into four 64-bit limbs, denoted by $A_i, B_i$ ($i \in \{0, 1, 2, 3\}$), and split $c$ and $d$ into two 128-bit limbs, denoted by $C_{lo}, C_{hi}$ and $D_{lo}, D_{hi}$.

|      A limbs       |    B limbs          |    C limbs         |  D limbs   |
|--------------------|---------------------|--------------------|------------|
|$A_0 = \sum_0^7 {a_i \cdot 256^i}$ | $B_0 = \sum_0^7 {b_i \cdot 256^i}$ | $C_{lo} = \sum_0^{15} {c_i \cdot 256^i}$ | $D_{lo} = \sum_0^{15} {d_i \cdot 256^i}$ |
|$A_1 = \sum_0^7 {a_{i+8} \cdot 256^i}$ | $B_1 = \sum_0^7 {b_{i+8} \cdot 256^i}$ | $C_{hi} = \sum_0^{15} {c_{i+16} \cdot 256^i}$ | $D_{hi} = \sum_0^{15} {d_{i+16} \cdot 256^i}$ |
|$A_2 = \sum_0^7 {a_{i+16} \cdot 256^i}$ | $B_2 = \sum_0^7 {b_{i+16} \cdot 256^i}$ | | |
|$A_3 = \sum_0^7 {a_{i+24} \cdot 256^i}$ | $B_3 = \sum_0^7 {b_{i+24} \cdot 256^i}$ | | |

The gadget computes four intermediate values as follows:

$$
\begin{align*}
t_0 &= A_0B_0 \\
t_1 &= A_0B_1 + A_1B_0 \\
t_2 &= A_0B_2 + A_1B_1 + A_2B_0\\
t_3 &= A_0B_3 + A_1B_2 + A_2B_1 + A_3B_0
\end{align*}
$$

, and the constraints are:

- $ t_0 + t_1 \cdot 2^{64} + C_{lo} == D_{lo} + carry_{lo} \cdot 2^{128} $
- $ t_2 + t_3 \cdot 2^{64} + C_{hi} + carry_{lo} == D_{hi} + carry_{hi} \cdot 2^{128} $ *v1 ⋅ 2¹²⁸ == v0 + t₂ + t₃ ⋅ 2⁶⁴ - C₂ - C₃ ⋅ 2⁶⁴*
- $ carry_{lo} \in [0, 2^{66}) $
- $ carry_{hi} \in [0, 2^{66}) $

Note that the $carry_{lo}, carry_{hi}$ should be in the range of $[0, 2^{66})$.
To make it easy to check the range, we relax the range to $[0, 2^{72})$ and use
9 byte cells to check the range of $carry_{lo}$ and $carry_{hi}$.
In addition, the `MulAddWordsGadget` returns an `overflow` expression that sums
up all parts that are over 256-bit value in `a * b + c`.

$$
overflow = carry_{hi} + A_1B_3 + A_2B_2 + A_3B_1 + A_2B_3 + A_3B_2 + A_3B_3
$$

Now back to the opcode circuit for `MUL`, `DIV`, and `MOD`, we first construct
the `MulAddWordsGadget` with four EVM words `a, b, c, d`.
Based on different opcode cases, we constrain the stack pops and pushes as follows

- for `MUL`, two stack pops are `a` and `b`, and the stack push is `d`
- for `DIV`, two stack pops are `d` and `b`, and the stack push is `a` if `b != 0`; otherwise 0.
- for `MOD`, two stack pops are `d` and `b`, and the stack push is `c` if `b != 0`; otherwise 0.

The opcode circuit also adds extra constraints for different opcodes:

- if the opcode is `MUL`, constrain `c == 0`.
- if the opcode is not `MUL`,
    - use a `LtWordGadget` to constrain `c < b` when `b != 0`
    - constrain `overflow == 0`

## Constraints

1. opcodeId checks
   1. opId === OpcodeId(0x02) for `MUL`
   2. opId === OpcodeId(0x04) for `DIV`
   3. opId === OpcodeId(0x06) for `MOD`
2. state transition:
   - gc + 3
   - stack_pointer + 1
   - pc + 1
   - gas + 5
3. Lookups: 3 busmapping lookups
   1. top of the stack :
      - when it's `MUL`, `a` is at the top of the stack
      - when it's `DIV`, `d` is at the top of the stack.
      - when it's `MOD`, `d` is at the top of the stack.
   2. `b` is at the second position of the stack
   3. new top of the stack
      - when it's `MUL`, `d` is at the new top of the stack
      - when it's `DIV`, `a` is at the new top of the stack when `b != 0`, otherwise 0
      - when it's `MOD`, `c` is at the new top of the stack when `b != 0`, otherwise 0

## Exceptions

1. stack underflow: `1023 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/evm/execution/mul_div_mod.py`
