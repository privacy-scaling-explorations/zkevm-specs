## MainRLPGadget

To verify the RLP encoding, MPT circuit uses `MainRLPGadget`:
```
pub struct MainRLPGadget<F> {
    bytes: Vec<Cell<F>>,
    rlp: RLPItemGadget<F>,
    num_bytes: Cell<F>,
    len: Cell<F>,
    mult_diff: Cell<F>,
    rlc_content: Cell<F>,
    rlc_rlp: Cell<F>,
    tag: Cell<F>,
}
```

The field `rlp` is of type `RLPItemGadget`:

```
pub(crate) struct RLPItemGadget<F> {
    pub(crate) value: RLPValueGadget<F>,
    pub(crate) list: RLPListGadget<F>,
}
```

`RLPItemGadget` is an abstraction over two types of the RLP item.
An RLP item is either a string (i.e. byte array) or a list of items.
The abstraction provides functions `is_short`, `is_long`, `is_very_long` that gives
information on the type of the stream - whether the number of RLP bytes is short or long.

Furthermore, it provides functions `num_rlp_bytes`, `num_bytes`, `len` that gives information
about the number of RLP bytes, number of bytes in total (including RLP bytes), and
length of value (excluding RLP bytes) respectively.

Finally, it provides functions `rlc_rlp` and `rlc_content` which provide the RLC of the whole
stream (including RLP bytes) and the RLC of the values (excluding RLP values) respectively.

TODO: fixed table lookup for `is_long` ...

### Constraints

`MainRLPGadget` ensures that the values stored in the cells `num_bytes`, `len`, `mult_diff`,
`rlc_content`, `rlc_rlp`, `tag` correspond to the bytes stored in `bytes`.

TODO

```
num_bytes == config.rlp.num_bytes()
config.len => config.rlp.len()
config.rlc_content = config.rlp.rlc_content(r)
config.rlc_rlp = config.rlp.rlc_rlp(cb, r)
let mult_diff = config.mult_diff.expr();
(FixedTableTag::RMult, config.rlp.num_bytes(), mult_diff) in @FIXED
```


## ListKeyGadget