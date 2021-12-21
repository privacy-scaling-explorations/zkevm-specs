# MUL op code

## Procedure

[Multi-Limbs Multiplication](https://hackmd.io/HL0QhGUeQoSgIBt2el6fHA)

If we are handling $\texttt{MUL}$ in notation $c = a \cdot b$, layout could be like the below table if we got 32 columns to use. In table, $a_0, \cdots, a_{31}$ as well as $b$ and $c$ are evm words on stack through bus mapping lookup. Each limb in evm word will be range lookup check to fit 8-bit.

$c$ here is $r$ in the note, and $t$, $v$ are notations following [Aztec's note](https://hackmd.io/@arielg/B13JoihA8). 

$$
\begin{array}{|c|c|}
\hline
a_0 & a_1 & a_2 & a_3 & a_4 & a_5 & \cdots & a_{29} & a_{30} & a_{31} \\\hline
b_0 & b_1 & b_2 & b_3 & b_4 & b_5 & \cdots & b_{29} & b_{30} & b_{31} \\\hline
c_0 & c_1 & c_2 & c_3 & c_4 & c_5 & \cdots & c_{29} & c_{30} & c_{31} \\\hline
t_0 & t_1 & t_2 & t_3 & v_0 & v_1 &        &        &        &        \\\hline
\end{array}
$$

$A$, $B$, and $C$ are linear combination and no need to be stored as witness.

$$
\cases{
    A_0 = \sum_{0}^{7} a_i \cdot 2^{8 \cdot i} \\
    A_1 = \sum_{0}^{7} a_{i+8} \cdot 2^{8 \cdot i} \\
    A_2 = \sum_{0}^{7} a_{i+16} \cdot 2^{8 \cdot i} \\
    A_3 = \sum_{0}^{7} a_{i+24} \cdot 2^{8 \cdot i} \\
}
\qquad
\cases{
    B_0 = \sum_{0}^{7} b_i \cdot 2^{8 \cdot i} \\
    B_1 = \sum_{0}^{7} b_{i+8} \cdot 2^{8 \cdot i} \\
    B_2 = \sum_{0}^{7} b_{i+16} \cdot 2^{8 \cdot i} \\
    B_3 = \sum_{0}^{7} b_{i+24} \cdot 2^{8 \cdot i} \\
}
\qquad
\cases{
    C_0 = \sum_{0}^{7} c_i \cdot 2^{8 \cdot i} \\
    C_1 = \sum_{0}^{7} c_{i+8} \cdot 2^{8 \cdot i} \\
    C_2 = \sum_{0}^{7} c_{i+16} \cdot 2^{8 \cdot i} \\
    C_3 = \sum_{0}^{7} c_{i+24} \cdot 2^{8 \cdot i} \\
}
$$

The constraints would be:

$$
\begin{aligned}
\cases{
    t_0 \stackrel{?}{=} A_0B_0 \\
    t_1 \stackrel{?}{=} A_0B_1 + A_1B_0 \\
    t_2 \stackrel{?}{=} A_0B_2 + A_1B_1 + A_2B_0 \\
    t_3 \stackrel{?}{=} A_0B_3 + A_1B_2 + A_2B_1 + A_3B_0 \\
    v_0 \cdot 2^{128} \stackrel{?}{=} t_0 + t_1 \cdot 2^{64} - C_0 - C_1 \cdot 2^{64} \\
    v_1 \cdot 2^{128} \stackrel{?}{=} v_0 + t_2 + t_3 \cdot 2^{64} - C_2 - C_3 \cdot 2^{64} \\
    v_0 \stackrel{?}{\in} [0, 2^{64}] \\
    v_1 \stackrel{?}{\in} [0, 2^{64}] \\
}
\end{aligned}
$$

We can use the [running sum range check](https://github.com/zcash/orchard/blob/main/src/circuit/gadget/utilities/lookup_range_check.rs) for $v_0$ and $v_1$ with 3 extra cells for each if we have 16-bit range table.

This approach needs 3 evm words and 12 cells, so 108 cells in total.

### EVM behavior

Pop two EVM words `a` and `b` from the stack. Compute `c = (a * b) % 2**256`, and push `c` back to the stack

### Circuit behavior

The MulGadget takes argument of `a: [u8;32]`, `x: [u8;32]`, `y: [u8;32]`.

It always computes `y = (a * x) % 2**256`, annotate stack as \[a, x, ...\] and \[y, ...\]

## Constraints

1. state transition:
   - gc + 3
   - stack_pointer + 1
   - pc + 1
   - gas + 5
2. Lookups: 3 busmapping lookups
   - `a` is at the top of the stack
   - `b` is at the second position of the stack
   - `c`, the result, is at the new top of the stack

## Exceptions

1. stack underflow: `1023 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/opcode/mul.py`
