from typing import NamedTuple, Tuple, List, Sequence, Set, Union, cast
from enum import IntEnum
from math import log, ceil

from .util import FQ, RLC, U160, U256, Expression
from .encoding import U8, is_circuit_code
from .evm import (
    RW,
    AccountFieldTag,
    CallContextFieldTag,
    TxLogFieldTag,
    TxReceiptFieldTag,
    MPTTableRow,
    MPTTableTag,
    lookup,
)

MAX_MEMORY_ADDRESS = 2**32 - 1
MAX_KEY_DIFF = 2**32 - 1
MAX_STACK_PTR = 1023
MAX_KEY0 = 12  # Number of Tag variants
MAX_KEY1 = 2**16 - 1  # Maximum number of calls in a block
MAX_KEY2 = 2**160 - 1  # Ethereum Address size
MAX_KEY3 = 24  # Max(# of CallContextFieldTag, # of AccountFieldTag) - 1
KEY0_BITS = ceil(log(MAX_KEY0 + 1, 2))  # 4
KEY1_BITS = ceil(log(MAX_KEY1 + 1, 2))  # 16
KEY2_BITS = ceil(log(MAX_KEY2 + 1, 2))  # 160
KEY3_BITS = ceil(log(MAX_KEY3 + 1, 2))  # 6


class Tag(IntEnum):
    """
    Tag used as first key in the State Circuit Rows to "select" the operation target.
    """

    # Start Tag is used both as padding before the rest of the operations and
    # also to discard constraints with the previous row that would fail due to
    # wrapping around with the end of the table.
    Start = 1
    Memory = 2
    Stack = 3
    Storage = 4
    CallContext = 5
    Account = 6
    TxRefund = 7
    TxAccessListAccount = 8
    TxAccessListAccountStorage = 9
    AccountDestructed = 10
    TxLog = 11
    TxReceipt = 12


class Row(NamedTuple):
    """
    State circuit row
    """

    # fmt: off
    rw_counter: FQ
    is_write: FQ # boolean
    # key0 takes the Tag value used to select the constraints of a particular
    # operation; the rest of they keys are used differently for each operation.
    # See the meaning of each key for each operation in ../../specs/tables.md
    # key2 is 160bit Address.  key4 is RLC encoded
    keys: Tuple[FQ, FQ, FQ, FQ, FQ]
    key2_limbs: Tuple[FQ, FQ, FQ, FQ, FQ, # key2 in Little-Endian (limbs in base 2**16)
                      FQ, FQ, FQ, FQ, FQ]
    key4_bytes: Tuple[FQ,FQ,FQ,FQ,FQ,FQ,FQ,FQ, # key4 in Little-Endian (limbs in base 2**8)
                      FQ,FQ,FQ,FQ,FQ,FQ,FQ,FQ,
                      FQ,FQ,FQ,FQ,FQ,FQ,FQ,FQ,
                      FQ,FQ,FQ,FQ,FQ,FQ,FQ,FQ]
    value: FQ
    auxs: Tuple[FQ]
    mpt_counter: FQ
    # fmt: on

    def tag(self):
        return self.keys[0]


class Tables:
    """
    Tables used for lookup from the state circuit.
    """

    mpt_table: Set[MPTTableRow]

    def __init__(self, mpt_table: Set[MPTTableRow]):
        self.mpt_table = mpt_table

    def mpt_account_lookup(
        self,
        counter: Expression,
        target: Expression,
        address: Expression,
        value: Expression,
        value_prev: Expression,
    ) -> MPTTableRow:
        query = {
            "counter": counter,
            "target": target,
            "address": address,
            "key": FQ(0),
            "value": value,
            "value_prev": value_prev,
        }
        return lookup(MPTTableRow, self.mpt_table, query)

    def mpt_storage_lookup(
        self,
        counter: Expression,
        address: Expression,
        key: Expression,
        value: Expression,
        value_prev: Expression,
    ) -> MPTTableRow:
        query = {
            "counter": counter,
            "target": FQ(MPTTableTag.Storage),
            "address": address,
            "key": key,
            "value": value,
            "value_prev": value_prev,
        }
        return lookup(MPTTableRow, self.mpt_table, query)


def linear_combine(limbs: Sequence[FQ], base: FQ) -> FQ:
    ret = FQ.zero()
    for limb in reversed(limbs):
        ret = ret * base + limb
    return ret


# Boolean Expression builder
def all_keys_eq(row: Row, row_prev: Row) -> bool:
    eq = True
    for i in range(len(row.keys)):
        eq = eq and (row.keys[i] == row_prev.keys[i])
    return eq


# Comparison gadget.  Returns:
# - eq = (lhs == rhs)
# - lt = (lhs < rhs)
class ComparisonGadget:
    eq: bool
    lt: bool

    def __init__(self, lhs: FQ, rhs: FQ):
        self.eq = lhs.n == rhs.n
        self.lt = lhs.n < rhs.n

    def __repr__(self):
        return f"ComparisonGadget(eq: {self.eq}, lt: {self.lt})"


@is_circuit_code
def assert_in_range(x: FQ, min_val: int, max_val: int) -> None:
    assert min_val <= x.n and x.n <= max_val


@is_circuit_code
def check_start(row: Row, row_prev: Row):
    # 0. rw_counter is 0
    assert row.rw_counter == 0

    # 1. mpt_counter is 0
    assert row.mpt_counter == 0


@is_circuit_code
def check_memory(row: Row, row_prev: Row):
    get_call_id = lambda row: row.keys[1]
    get_memory_address = lambda row: row.keys[2]

    # 0. Unused keys are 0
    assert row.keys[3] == 0
    assert row.keys[4] == 0

    # 1. First access for a set of all keys
    #
    # When the set of all keys changes (first access of an address in a call)
    # - If READ, value must be 0
    if not all_keys_eq(row, row_prev) and row.is_write == 0:
        assert row.value == 0

    # 2. mem_addr in range
    assert_in_range(get_memory_address(row), 0, MAX_MEMORY_ADDRESS)

    # 3. value is a byte
    assert_in_range(row.value, 0, 2**8 - 1)


@is_circuit_code
def check_stack(row: Row, row_prev: Row):
    get_call_id = lambda row: row.keys[1]
    get_stack_ptr = lambda row: row.keys[2]

    # 0. Unused keys are 0
    assert row.keys[3] == 0
    assert row.keys[4] == 0

    # 1. First access for a set of all keys
    #
    # The first stack operation in a stack position is always a write (can't
    # read if it isn't written before)
    #
    # When the set of all keys changes (first access of a stack position in a call)
    # - It must be a WRITE
    if not all_keys_eq(row, row_prev):
        assert row.is_write == 1

    # 2. stack_ptr in range
    stack_ptr = get_stack_ptr(row)
    assert_in_range(stack_ptr, 0, MAX_STACK_PTR)

    # 3. stack_ptr only increases by 0 or 1
    if row.tag() == row_prev.tag() and get_call_id(row) == get_call_id(row_prev):
        stack_ptr_diff = get_stack_ptr(row) - get_stack_ptr(row_prev)
        assert_in_range(stack_ptr_diff, 0, 1)


@is_circuit_code
def check_storage(row: Row, row_prev: Row, tables: Tables):
    get_addr = lambda row: row.keys[2]
    get_storage_key = lambda row: row.keys[4]
    get_committed_value = lambda row: row.auxs[0]

    # 0. Unused keys are 0
    assert row.keys[3] == 0

    # 1. When keys don't change, committed_value must be kept equal
    if all_keys_eq(row, row_prev):
        assert get_committed_value(row) == get_committed_value(row_prev)

    # TODO: The current spec does an MPT lookup for every storage update.  The
    # next optimization consists on doing a single lookup merging all updates
    # for a given key, using the first and last access values.

    # 2. MPT storage lookup with incremental counter
    #
    # When the keys are equal in the previous row, the value_prev must be the
    # value in previous row.  When the keys change, value_prev is loaded from
    # committed_value, which holds the storage value before the tx began.
    value_prev = row_prev.value if all_keys_eq(row, row_prev) else get_committed_value(row)
    tables.mpt_storage_lookup(
        row.mpt_counter, get_addr(row), get_storage_key(row), row.value, value_prev
    )


@is_circuit_code
def check_call_context(row: Row, row_prev: Row):
    get_call_id = lambda row: row.keys[1]
    get_field_tag = lambda row: row.keys[3]

    # 0. Unused keys are 0
    assert row.keys[2] == 0
    assert row.keys[4] == 0

    # TODO: Missing constraints


@is_circuit_code
def check_account(row: Row, row_prev: Row, tables: Tables):
    get_addr = lambda row: row.keys[2]
    get_field_tag = lambda row: row.keys[3]
    get_committed_value = lambda row: row.auxs[0]

    # 0. Unused keys are 0
    assert row.keys[1] == 0
    assert row.keys[4] == 0

    # 1. When keys don't change, committed_value must be kept equal
    if all_keys_eq(row, row_prev):
        assert get_committed_value(row) == get_committed_value(row_prev)

    # TODO: The current spec does an MPT lookup for every storage update.  The
    # next optimization consists on doing a single lookup merging all updates
    # for a given key, using the first and last access values.

    # 2. MPT storage lookup with incremental counter
    #
    # When the keys are equal in the previous row, the value_prev must be the
    # value in previous row.  When the keys change, value_prev is loaded from
    # committed_value, which holds the account value before the block began.
    value_prev = row_prev.value if all_keys_eq(row, row_prev) else get_committed_value(row)
    tables.mpt_account_lookup(
        row.mpt_counter, get_field_tag(row), get_addr(row), row.value, value_prev
    )

    # NOTE: Value transition rules are constrained via the EVM circuit: for example,
    # Nonce only increases by 1 or decreases by 1 (on revert).


@is_circuit_code
def check_tx_refund(row: Row, row_prev: Row):
    get_tx_id = lambda row: row.keys[1]

    # 0. Unused keys are 0
    assert row.keys[2] == 0
    assert row.keys[3] == 0
    assert row.keys[4] == 0

    # TODO: Missing constraints
    # - When keys change, value must be 0


@is_circuit_code
def check_tx_access_list_account(row: Row, row_prev: Row):
    get_tx_id = lambda row: row.keys[1]
    get_addr = lambda row: row.keys[2]

    # 0. Unused keys are 0
    assert row.keys[3] == 0
    assert row.keys[4] == 0

    # TODO: Missing constraints
    # - When keys change, value must be 0


@is_circuit_code
def check_tx_access_list_account_storage(row: Row, row_prev: Row):
    get_tx_id = lambda row: row.keys[1]
    get_addr = lambda row: row.keys[2]
    get_storage_key = lambda row: row.keys[4]

    # 0. Unused keys are 0
    assert row.keys[3] == 0

    # TODO: Missing constraints
    # - When keys change, value must be 0


@is_circuit_code
def check_account_destructed(row: Row, row_prev: Row):
    get_addr = lambda row: row.keys[2]

    # 0. Unused keys are 0
    assert row.keys[1] == 0
    assert row.keys[3] == 0
    assert row.keys[4] == 0

    # TODO: Missing constraints
    # - When keys change, value must be 0


@is_circuit_code
def check_tx_log(row: Row, row_prev: Row):
    # tx_id | log_id | field_tag | index | value
    tx_id = row.keys[1]
    pre_tx_id = row_prev.keys[1]
    log_id = row.keys[2]
    pre_field_tag = row_prev.keys[3]
    field_tag = row.keys[3]
    index = row.keys[4]
    pre_index = row_prev.keys[4]

    # is_write is always true
    assert row.is_write == 1
    # reset log_id when tx_id increases
    if row.tag() == row_prev.tag():
        if tx_id != pre_tx_id:
            assert tx_id == pre_tx_id + 1
            assert log_id == 0
        else:
            # increase log_id when tag changes to Address, make sure tag can only increase(Non-Decreasing),
            # when log_index stays same,
            if pre_field_tag == U256(TxLogFieldTag.Address):
                assert (field_tag - pre_field_tag).n > 0
            # make sure if tag Data appear, data_index can only increase by one when tag stays same.
            # make sure if tag Topic appear, topic_index in range [0,4),can only increase by one when tag stays same.
            if field_tag == U256(TxLogFieldTag.Topic):
                assert_in_range(index, 0, 3)
            if field_tag not in [U256(TxLogFieldTag.Topic), U256(TxLogFieldTag.Data)]:
                assert index == 0
            elif pre_field_tag == field_tag:
                assert index == pre_index + 1

    # make sure if log set is not empty within receipt/tx, tx must be successful status because failed execution will revert the log data,
    # in other words, logs section must be empty list for failed tx


@is_circuit_code
def check_tx_receipt(row: Row, row_prev: Row):
    tx_id = row.keys[1]
    pre_tx_id = row_prev.keys[1]
    field_tag = row.keys[3]
    # 0. Unused keys are 0
    assert row.keys[2] == 0
    assert row.keys[4] == 0

    # value for tag `PostStateOrStatus` is bool (0 or 1) according to EIP#658
    if field_tag == U256(TxReceiptFieldTag.PostStateOrStatus):
        assert row.value in [0, 1]

    # when tx id changes, must be increasing by one , the CumulativeGasUsed must be increasing as well
    if tx_id != pre_tx_id and row.tag() == row_prev.tag():
        assert tx_id == pre_tx_id + 1
        if field_tag == U256(TxReceiptFieldTag.CumulativeGasUsed):
            assert row.value.n > row_prev.value.n

    # tx id starts with 1
    if row.tag() != row_prev.tag():
        # first row the tx id is 1
        assert tx_id == FQ(1)

    assert_in_range(tx_id, 1, 2**11)


@is_circuit_code
def check_state_row(row: Row, row_prev: Row, tables: Tables, randomness: FQ):
    #
    # Constraints that affect all rows, no matter which Tag they use
    #

    # 0. key0, key1, key3 are in the expected range
    assert_in_range(row.keys[0], 1, MAX_KEY0)
    assert_in_range(row.keys[1], 0, MAX_KEY1)
    assert_in_range(row.keys[3], 0, MAX_KEY3)

    # 1. key2 is linear combination of 10 x 16bit limbs and also in range
    for limb in row.key2_limbs:
        assert_in_range(limb, 0, 2**16 - 1)
    assert row.keys[2] == linear_combine(row.key2_limbs, FQ(2**16))

    # 2. key4 is RLC encoded
    for limb in row.key4_bytes:
        assert_in_range(limb, 0, 2**8 - 1)
    assert row.keys[4] == linear_combine(row.key4_bytes, randomness)

    # 3. is_write is boolean
    assert row.is_write in [0, 1]

    # 4. Keys are sorted in lexicographic order for same Tag
    #
    # This check also ensures that Tag monotonically increases for all values
    # except for Start
    #
    # When in two consecutive rows the keys are equal in a column:
    # - The corresponding keys in the following column must be increasing.
    #
    # key4 is RLC encoded, so it doesn't keep the order.  We use the key4 bytes
    # decomposition instead.  Since we will use a chain of comparison gadgets,
    # we try to merge multiple keys together to reduce the number of required
    # gadgets.

    # Assert that key0, key1, key2, key3, 4 bytes from key4 fit inside an element
    assert KEY0_BITS + KEY1_BITS + KEY2_BITS + KEY3_BITS + 4 * 8 < log(FQ(-1).n + 1, 2)

    def get_keys_compressed_in_order(row: Row) -> List[FQ]:
        k0 = row.keys[0]
        k0 = k0 * 2**KEY1_BITS + row.keys[1]
        k0 = k0 * 2**KEY2_BITS + row.keys[2]
        k0 = k0 * 2**KEY3_BITS + row.keys[3]
        k0 = k0 * 2 ** (4 * 8) + linear_combine(row.key4_bytes[-4:], FQ(2**8))
        k1 = linear_combine(row.key4_bytes[:-4], FQ(2**8))
        return [k0, k1]

    keys = get_keys_compressed_in_order(row)
    keys_prev = get_keys_compressed_in_order(row_prev)
    keys_eq = True
    cmps = [ComparisonGadget(keys_prev[i], keys[i]) for i in range(len(keys))]
    if row.tag() != Tag.Start:
        assert cmps[0].lt or (cmps[0].eq and cmps[1].lt) or (cmps[0].eq and cmps[1].eq)

    # 5. RWC is monotonically strictly increasing for a set of all keys
    #
    # When tag is not Start and all the keys are equal in two consecutive a rows:
    # - The corresponding rwc must be strictly increasing.
    if row.tag() != Tag.Start and all_keys_eq(row, row_prev):
        rw_diff = row.rw_counter - row_prev.rw_counter
        assert_in_range(rw_diff, 1, MAX_KEY_DIFF)

    # 6. Read consistency
    #
    # When a row is READ
    # AND When all the keys are equal in two consecutive a rows:
    # - The corresponding value must be equal to the previous row
    if row.is_write == 0 and all_keys_eq(row, row_prev):
        assert row.value == row_prev.value

    # 7. Increment mpt_counter
    #
    # When row is Storage or Account, increment the mpt_counter by
    # one, otherwise maintain the same value
    if row.tag() != Tag.Start:
        if row.tag() == Tag.Storage or row.tag() == Tag.Account:
            assert row.mpt_counter == row_prev.mpt_counter + 1
        else:
            assert row.mpt_counter == row_prev.mpt_counter

    # 8. RWC !=0 except for Tag.Start
    if row.tag() != Tag.Start:
        assert row.rw_counter != 0

    #
    # Constraints specific to each Tag
    #
    if row.tag() == Tag.Start:
        check_start(row, row_prev)
    elif row.tag() == Tag.Memory:
        check_memory(row, row_prev)
    elif row.tag() == Tag.Stack:
        check_stack(row, row_prev)
    elif row.tag() == Tag.Storage:
        check_storage(row, row_prev, tables)
    elif row.tag() == Tag.CallContext:
        check_call_context(row, row_prev)
    elif row.tag() == Tag.Account:
        check_account(row, row_prev, tables)
    elif row.tag() == Tag.TxRefund:
        check_tx_refund(row, row_prev)
    elif row.tag() == Tag.TxAccessListAccountStorage:
        check_tx_access_list_account_storage(row, row_prev)
    elif row.tag() == Tag.TxAccessListAccount:
        check_tx_access_list_account(row, row_prev)
    elif row.tag() == Tag.AccountDestructed:
        check_account_destructed(row, row_prev)
    elif row.tag() == Tag.TxReceipt:
        check_tx_receipt(row, row_prev)
    elif row.tag() == Tag.TxLog:
        check_tx_log(row, row_prev)
    else:
        raise ValueError("Unreacheable")


# State circuit operation superclass
class Operation(NamedTuple):
    """
    State circuit operation
    """

    rw_counter: int
    rw: RW
    key0: U256
    key1: U256
    key2: U256
    key3: U256
    key4: U256
    value: FQ
    aux0: FQ


class StartOp(Operation):
    """
    Start Operation
    """

    def __new__(self):
        # fmt: off
        return super().__new__(self, 0, 0,
                U256(Tag.Start), U256(0), U256(0), U256(0), U256(0), # keys
                FQ(0), FQ(0)) # values
        # fmt: on


class MemoryOp(Operation):
    """
    Memory Operation
    """

    # The yellow paper allows memory addresses to have up to 256 bits, but the
    # gas cost for memory operations is quadratic in the maximum memory address
    # touched. From equation 326 in the yellow paper, for C_mem(a), the maximum
    # memory address touched will fit in to 32 bits until the gas limit is over
    # 3.6e16.
    def __new__(self, rw_counter: int, rw: RW, call_id: int, mem_addr: U160, value: U8):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.Memory), U256(call_id), U256(mem_addr), U256(0), U256(0), # keys
                FQ(value), FQ(0)) # values
        # fmt: on


class StackOp(Operation):
    """
    Stack Operation
    """

    def __new__(self, rw_counter: int, rw: RW, call_id: int, stack_ptr: int, value: FQ):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.Stack), U256(call_id), U256(stack_ptr), U256(0), U256(0), # keys
                value, FQ(0)) # values
        # fmt: on


class StorageOp(Operation):
    """
    Storage Operation
    """

    def __new__(
        self,
        rw_counter: int,
        rw: RW,
        tx_id: int,
        addr: U160,
        key: U256,
        value: FQ,
        committed_value: FQ,
    ):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.Storage), U256(tx_id), U256(addr), U256(0), U256(key), # keys
                value, committed_value) # values
        # fmt: on


class CallContextOp(Operation):
    """
    CallContext Operation
    """

    def __new__(
        self, rw_counter: int, rw: RW, call_id: int, field_tag: CallContextFieldTag, value: FQ
    ):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.CallContext), U256(call_id), U256(0), U256(field_tag), U256(0), # keys
                value, FQ(0)) # values
        # fmt: on


class AccountOp(Operation):
    """
    Account Operation
    """

    def __new__(
        self,
        rw_counter: int,
        rw: RW,
        addr: U160,
        field_tag: AccountFieldTag,
        value: FQ,
        committed_value: FQ,
    ):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.Account), U256(0), U256(addr), U256(field_tag), U256(0), # keys
                value, committed_value) # values
        # fmt: on


class TxRefundOp(Operation):
    """
    TxRefund Operation
    """

    def __new__(self, rw_counter: int, rw: RW, tx_id: int, value: FQ):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.TxRefund), U256(tx_id), U256(0), U256(0), U256(0), # keys
                value, FQ(0)) # values
        # fmt: on


class TxAccessListAccountOp(Operation):
    """
    TxAccessListAccount Operation
    """

    def __new__(self, rw_counter: int, rw: RW, tx_id: int, addr: U160, value: FQ):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.TxAccessListAccount), U256(tx_id), U256(addr), U256(0), U256(0), # keys
                value, FQ(0)) # values
        # fmt: on


class TxAccessListAccountStorageOp(Operation):
    """
    TxAccessListAccountStorage Operation
    """

    def __new__(self, rw_counter: int, rw: RW, tx_id: int, addr: U160, key: U256, value: FQ):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.TxAccessListAccountStorage),
                U256(tx_id), U256(addr), U256(0), U256(key), # keys
                value, FQ(0)) # values
        # fmt: on


class AccountDestructedOp(Operation):
    """
    AccountDestructed Operation
    """

    def __new__(self, rw_counter: int, rw: RW, addr: U160, value: FQ):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.AccountDestructed), U256(0), U256(addr), U256(0), U256(0), # keys
                value, FQ(0)) # values
        # fmt: on


class TxLogOp(Operation):
    """
    TxLog Operation
    """

    def __new__(
        self,
        rw_counter: int,
        rw: RW,
        tx_id: int,
        log_id: int,
        field_tag: TxLogFieldTag,
        index: int,
        value: FQ,
    ):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.TxLog),U256(tx_id), U256(log_id), U256(field_tag), U256(index), # keys
                value, FQ(0)) # values
        # fmt: on


class TxReceiptOp(Operation):
    """
    TxReceipt Operation
    """

    def __new__(self, rw_counter: int, rw: RW, tx_id: int, field_tag: TxReceiptFieldTag, value: FQ):
        # fmt: off
        return super().__new__(self, rw_counter, rw,
                U256(Tag.TxReceipt), U256(tx_id),  U256(0), U256(field_tag), U256(0), # keys
                value, FQ(0)) # values
        # fmt: on


class Assigner:
    mpt_counter: FQ

    def __init__(self):
        self.mpt_counter = FQ(0)

    def op2row(self, op: Operation, randomness: FQ) -> Row:
        rw_counter = FQ(op.rw_counter)
        is_write = FQ(0) if op.rw == RW.Read else FQ(1)
        key0 = FQ(op.key0)
        key1 = FQ(op.key1)
        key2 = FQ(op.key2)
        key2_bytes = op.key2.to_bytes(20, "little")
        key2_limbs = tuple(
            [FQ(key2_bytes[i] + 2**8 * key2_bytes[i + 1]) for i in range(0, 20, 2)]
        )
        key3 = FQ(op.key3)
        key4_rlc = RLC(op.key4, randomness)
        key4 = key4_rlc.expr()
        key4_bytes = tuple([FQ(x) for x in key4_rlc.le_bytes])
        value = FQ(op.value)
        aux0 = FQ(op.aux0)

        if key0 == FQ(Tag.Storage) or key0 == FQ(Tag.Account):
            self.mpt_counter += 1

        # fmt: off
        return Row(rw_counter, is_write,
                # keys
                (key0, key1, key2, key3, key4), key2_limbs, key4_bytes, # type: ignore
                value, (aux0,), # values
                self.mpt_counter)
        # fmt: on


# def rw_table_tag2tag(tag: RWTableTag) -> FQ:
#     ret = None
#     if tag == RWTableTag.Memory:
#         ret = Tag.Memory
#     elif tag == RWTableTag.Stack:
#         ret = Tag.Stack
#     elif tag == RWTableTag.Storage:
#         ret = Tag.Storage
#     elif tag == RWTableTag.CallContext:
#         ret = Tag.CallContext
#     elif tag == RWTableTag.Account:
#         ret = Tag.Account
#     elif tag == RWTableTag.TxRefund:
#         ret = Tag.TxRefund
#     elif tag == RWTableTag.TxAccessListAccount:
#         ret = Tag.TxAccessListAccount
#     elif tag == RWTableTag.TxAccessListAccountStorage:
#         ret = Tag.TxAccessListAccountStorage
#     elif tag == RWTableTag.AccountDestructed:
#         ret = Tag.AccountDestructed
#     else:
#         raise ValueError("Unreacheable")
#
#     return FQ(ret)

# Generate the advice Rows from a list of Operations
def assign_state_circuit(ops: List[Operation], randomness: FQ) -> List[Row]:
    assigner = Assigner()
    rows = [assigner.op2row(op, randomness) for op in ops]
    return rows


def mpt_table_from_ops(
    ops_or_rows: Union[List[Operation], List[Row]], randomness: FQ
) -> Set[MPTTableRow]:
    if isinstance(ops_or_rows[0], Operation):
        rows = assign_state_circuit(cast(List[Operation], ops_or_rows), randomness)
    else:
        rows = cast(List[Row], ops_or_rows)

    mpt_rows = []
    for (idx, row) in enumerate(rows):
        value_prev = row.auxs[0]
        if idx > 0:
            row_prev = rows[idx - 1]
            if all_keys_eq(row, row_prev):
                value_prev = row_prev.value

        if row.keys[0] == FQ(Tag.Storage):
            mpt_rows.append(
                MPTTableRow(
                    row.mpt_counter,
                    FQ(MPTTableTag.Storage),
                    row.keys[2],
                    row.keys[4],
                    row.value,
                    value_prev,
                )
            )
        elif row.keys[0] == FQ(Tag.Account):
            mpt_rows.append(
                MPTTableRow(
                    row.mpt_counter, row.keys[3], row.keys[2], row.keys[4], row.value, value_prev
                )
            )
    return set(mpt_rows)
