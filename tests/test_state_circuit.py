import traceback
from typing import Union, List

from zkevm_specs.state import *
from zkevm_specs.util import rand_fq, FQ, RLC

randomness = rand_fq()
r = randomness

# Verify the state circuit with the given data
def verify(ops_or_rows: Union[List[Operation], List[Row]], randomness: FQ, success: bool = True):
    rows = ops_or_rows
    if isinstance(ops_or_rows[0], Operation):
        rows = assign_state_circuit(ops_or_rows, randomness)
    ok = True
    for (idx, row) in enumerate(rows):
        row_prev = rows[(idx - 1) % len(rows)]
        try:
            check_state_row(row, row_prev, randomness)
        except AssertionError as e:
            if success:
                traceback.print_exc()
            print(f"row[{(idx-1) % len(rows)}]: {row_prev}")
            print(f"row[{idx}]: {row}")
            ok = False
            break
    assert ok == success


def test_state_ok():
    # fmt: off
    ops = [
        StartOp(),
        StartOp(),
        StartOp(),

        MemoryOp(rw_counter=1, rw=RW.Read,  call_id=1, mem_addr=0, value=0),
        MemoryOp(rw_counter=2, rw=RW.Write, call_id=1, mem_addr=0, value=42),
        MemoryOp(rw_counter=3, rw=RW.Read,  call_id=1, mem_addr=0, value=42),

        StackOp(rw_counter=4, rw=RW.Write, call_id=1, stack_ptr=1022, value=RLC(4321 ,r).expr()),
        StackOp(rw_counter=5, rw=RW.Write, call_id=1, stack_ptr=1023, value=RLC(533 ,r).expr()),
        StackOp(rw_counter=6, rw=RW.Read,  call_id=1, stack_ptr=1023, value=RLC(533 ,r).expr()),

        StorageOp(rw_counter=0, rw=RW.Write, addr=0x12345678, key=0x1516, value=RLC(789, r).expr()),
        StorageOp(rw_counter=7, rw=RW.Read,  addr=0x12345678, key=0x1516, value=RLC(789, r).expr()),
        StorageOp(rw_counter=0, rw=RW.Write, addr=0x12345678, key=0x4959, value=RLC(98765, r).expr()),
        StorageOp(rw_counter=8, rw=RW.Write, addr=0x12345678, key=0x4959, value=RLC(38491, r).expr()),

        CallContextOp(rw_counter= 9, rw=RW.Read, call_id=1, field_tag=CallContextFieldTag.IsStatic, value=FQ(0)),
        CallContextOp(rw_counter=10, rw=RW.Read, call_id=2, field_tag=CallContextFieldTag.IsStatic, value=FQ(0)),

        AccountOp(rw_counter= 0, rw=RW.Write, addr=0x12345678, field_tag=AccountFieldTag.Nonce, value=FQ(0)),
        AccountOp(rw_counter=12, rw=RW.Write, addr=0x12345678, field_tag=AccountFieldTag.Nonce, value=FQ(1)),
        AccountOp(rw_counter=13, rw=RW.Read,  addr=0x12345678, field_tag=AccountFieldTag.Nonce, value=FQ(1)),

        TxRefundOp(rw_counter=14, rw=RW.Write, tx_id=1, value=FQ(1)),
        TxRefundOp(rw_counter=15, rw=RW.Write, tx_id=1, value=FQ(1)),

        TxAccessListAccountOp(rw_counter=16, rw=RW.Read, tx_id=1, addr=0x12345678, value=FQ(1)),
        TxAccessListAccountOp(rw_counter=17, rw=RW.Read, tx_id=1, addr=0x12345678, value=FQ(1)),

        TxAccessListAccountStorageOp(rw_counter=18, rw=RW.Read, tx_id=1, addr=0x12345678, key=0x1516, value=FQ(1)),
        TxAccessListAccountStorageOp(rw_counter=19, rw=RW.Read, tx_id=1, addr=0x12345678, key=0x1516, value=FQ(1)),

        AccountDestructedOp(rw_counter=20, rw=RW.Read, addr=0x12345678, value=FQ(1)),
        AccountDestructedOp(rw_counter=21, rw=RW.Read, addr=0x12345678, value=FQ(1)),
        TxLogOp(rw_counter=22, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Address, index=0, value=FQ(124)),
        TxLogOp(rw_counter=23, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=0, value=FQ(10)),
        TxLogOp(rw_counter=24, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=1,  value=FQ(5)),
        TxLogOp(rw_counter=25, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=2,  value=FQ(200)),
        TxLogOp(rw_counter=26, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=3,  value=FQ(278)),
        TxLogOp(rw_counter=27, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Data,  index=0,  value=FQ(10)),
        TxLogOp(rw_counter=28, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Data,  index=1,  value=FQ(255)),
        TxLogOp(rw_counter=29, rw=RW.Write, tx_id=1, log_id=1, field_tag=TxLogFieldTag.Address, index=0,  value=FQ(255)),
        TxLogOp(rw_counter=30, rw=RW.Write, tx_id=1, log_id=1, field_tag=TxLogFieldTag.Data, index=0,  value=FQ(88)),
        TxLogOp(rw_counter=31, rw=RW.Write, tx_id=2, log_id=0, field_tag=TxLogFieldTag.Address, index=0,  value=FQ(210)),
        TxLogOp(rw_counter=32, rw=RW.Write, tx_id=2, log_id=0, field_tag=TxLogFieldTag.Topic, index=0,  value=FQ(255)),
        TxLogOp(rw_counter=33, rw=RW.Write, tx_id=2, log_id=0, field_tag=TxLogFieldTag.Data, index=0,  value=FQ(10)),

        TxReceiptOp(rw_counter=34, rw=RW.Read, tx_id=1, field_tag=TxReceiptFieldTag.PostStateOrStatus, value=FQ(1)),
        TxReceiptOp(rw_counter=35, rw=RW.Read, tx_id=1, field_tag=TxReceiptFieldTag.CumulativeGasUsed, value=FQ(200)),
        TxReceiptOp(rw_counter=36, rw=RW.Read, tx_id=2, field_tag=TxReceiptFieldTag.PostStateOrStatus, value=FQ(1)),
        TxReceiptOp(rw_counter=37, rw=RW.Read, tx_id=2, field_tag=TxReceiptFieldTag.CumulativeGasUsed, value=FQ(500)),
    ]
    # fmt: on
    verify(ops, randomness)


def test_state_bad_key2():
    # fmt: off
    ops = [
        StartOp(),
        MemoryOp(rw_counter=1, rw=RW.Read,  call_id=2, mem_addr=123, value=0),
    ]
    # fmt: on
    rows = assign_state_circuit(ops, r)
    rows[1] = rows[1]._replace(key2_limbs=(FQ(1),) * 10)
    verify(rows, randomness, success=False)


def test_state_bad_key4():
    # fmt: off
    ops = [
        StartOp(),
        StorageOp(rw_counter=0, rw=RW.Write, addr=0x12345678, key=0x15161718, value=RLC(789, r).expr()),
    ]
    # fmt: on
    rows = assign_state_circuit(ops, r)
    rows[1] = rows[1]._replace(key4_bytes=(FQ(1),) * 10)
    verify(rows, randomness, success=False)


def test_state_bad_is_write():
    # fmt: off
    ops = [
        StartOp(),
        StorageOp(rw_counter=0, rw=RW.Write, addr=0x12345678, key=0x15161718, value=RLC(789, r).expr()),
    ]
    # fmt: on
    rows = assign_state_circuit(ops, r)
    rows[1] = rows[1]._replace(is_write=FQ(2))
    verify(rows, randomness, success=False)


def test_state_keys_non_lexicographic_order():
    # fmt: off
    ops = [
        StartOp(),
        StorageOp(rw_counter=0, rw=RW.Write, addr=0x12345678, key=0x1112, value=RLC(98765, r).expr()),
        StorageOp(rw_counter=0, rw=RW.Write, addr=0x12345678, key=0x1111, value=RLC(789, r).expr()),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    ops = [
        StartOp(),
        StorageOp(rw_counter=0, rw=RW.Write, addr=0x12345678, key=2 << 250, value=RLC(98765, r).expr()),
        StorageOp(rw_counter=0, rw=RW.Write, addr=0x12345678, key=1 << 250, value=RLC(789, r).expr()),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    ops = [
        StartOp(),
        StorageOp(rw_counter=0, rw=RW.Write, addr=0x12345678, key=123, value=RLC(98765, r).expr()),
        StorageOp(rw_counter=1, rw=RW.Write, addr=0x12345678, key=123, value=RLC(789, r).expr()),
        MemoryOp(rw_counter=2, rw=RW.Read,  call_id=1, mem_addr=0, value=0),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    ops = [
        StartOp(),
        MemoryOp(rw_counter=1, rw=RW.Read,  call_id=2, mem_addr=0, value=0),
        MemoryOp(rw_counter=2, rw=RW.Read,  call_id=1, mem_addr=0, value=0),
    ]
    # fmt: on
    verify(ops, randomness, success=False)


def test_state_bad_rwc():
    # fmt: off
    ops = [
        StartOp(),
        MemoryOp(rw_counter=2, rw=RW.Read,  call_id=2, mem_addr=123, value=0),
        MemoryOp(rw_counter=1, rw=RW.Read,  call_id=2, mem_addr=123, value=0),
    ]
    # fmt: on
    verify(ops, randomness, success=False)


def test_state_bad_read_consistency():
    # fmt: off
    ops = [
        StartOp(),
        MemoryOp(rw_counter=1, rw=RW.Read,  call_id=2, mem_addr=123, value=0),
        MemoryOp(rw_counter=2, rw=RW.Write, call_id=2, mem_addr=123, value=8),
        MemoryOp(rw_counter=3, rw=RW.Read,  call_id=2, mem_addr=123, value=0),
    ]
    # fmt: on
    verify(ops, randomness, success=False)


def test_start_bad():
    # fmt: off
    ops = [
        StartOp(),
        MemoryOp(rw_counter=1, rw=RW.Read,  call_id=2, mem_addr=123, value=0),
    ]
    # fmt: on
    rows = assign_state_circuit(ops, r)
    rows[0] = rows[0]._replace(rw_counter=FQ(1))
    verify(rows, randomness, success=False)


def first_memory_op(rw_counter=1, rw=RW.Write, call_id=1, mem_addr=2**32 - 1, value=3):
    return MemoryOp(rw_counter, rw, call_id, mem_addr, value)


def test_first_memory_op_ok():
    ops = [StartOp(), first_memory_op()]
    verify(ops, randomness, success=True)


def test_memory_bad_address():
    ops = [StartOp(), first_memory_op(mem_addr=2**32)]
    verify(ops, randomness, success=False)


def test_memory_bad_first_access():
    ops = [StartOp(), first_memory_op(rw=RW.Read)]
    verify(ops, randomness, success=False)


def test_memory_bad_value_range():
    ops = [StartOp(), first_memory_op(value=2**8)]
    verify(ops, randomness, success=False)


def test_stack_bad_first_access():
    # fmt: off
    ops = [
        StartOp(),
        StackOp(rw_counter=1, rw=RW.Read, call_id=1, stack_ptr=1023, value=RLC(4321 ,r).expr()),
    ]
    # fmt: on
    verify(ops, randomness, success=False)


def test_stack_bad_stack_ptr_range():
    # fmt: off
    ops = [
        StartOp(),
        StackOp(rw_counter=1, rw=RW.Write, call_id=1, stack_ptr=1024, value=RLC(4321 ,r).expr()),
    ]
    # fmt: on
    verify(ops, randomness, success=False)


def test_stack_bad_stack_ptr_inc():
    # fmt: off
    ops = [
        StartOp(),
        StackOp(rw_counter=1, rw=RW.Write, call_id=1, stack_ptr=1021, value=RLC(4321 ,r).expr()),
        StackOp(rw_counter=2, rw=RW.Write, call_id=1, stack_ptr=1023, value=RLC(4321 ,r).expr()),
    ]
    # fmt: on
    verify(ops, randomness, success=False)


def test_storage_bad_first_access():
    # fmt: off
    ops = [
        StartOp(),
        StorageOp(rw_counter=0, rw=RW.Read, addr=0x12345678, key=0x1516, value=RLC(789, r).expr()),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    ops = [
        StartOp(),
        StorageOp(rw_counter=1, rw=RW.Write, addr=0x12345678, key=0x1516, value=RLC(789, r).expr()),
    ]
    # fmt: on
    verify(ops, randomness, success=False)


def test_account_bad_first_access():
    # fmt: off
    ops = [
        StartOp(),
        AccountOp(rw_counter= 0, rw=RW.Read, addr=0x12345678, field_tag=AccountFieldTag.Nonce, value=FQ(0)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    ops = [
        StartOp(),
        AccountOp(rw_counter=1, rw=RW.Write, addr=0x12345678, field_tag=AccountFieldTag.Nonce, value=FQ(0)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)


def test_tx_log_bad():
    # fmt: off
    # topic index is not increasing
    ops = [
        StartOp(),
        TxLogOp(rw_counter=1, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Address, index=0, value=FQ(124)),
        TxLogOp(rw_counter=2, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=0, value=FQ(10)),
        TxLogOp(rw_counter=3, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=0, value=FQ(5)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    # topic index out of range >= 4
    ops = [
        StartOp(),
        TxLogOp(rw_counter=1, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Address, index=0, value=FQ(124)),
        TxLogOp(rw_counter=2, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=0, value=FQ(10)),
        TxLogOp(rw_counter=3, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=1, value=FQ(5)),
        TxLogOp(rw_counter=4, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=2, value=FQ(5)),
        TxLogOp(rw_counter=5, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=3, value=FQ(5)),
        TxLogOp(rw_counter=6, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Topic, index=4, value=FQ(5)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    # Data index is not increasing
    ops = [
        StartOp(),
        TxLogOp(rw_counter=1, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Address, index=0, value=FQ(124)),
        TxLogOp(rw_counter=2, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Data, index=0, value=FQ(10)),
        TxLogOp(rw_counter=3, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Data, index=0, value=FQ(255)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    # log id is decreasing
    ops = [
        StartOp(),
        TxLogOp(rw_counter=1, rw=RW.Write, tx_id=1, log_id=1, field_tag=TxLogFieldTag.Address, index=0, value=FQ(124)),
        TxLogOp(rw_counter=2, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Data, index=0, value=FQ(10)),
        TxLogOp(rw_counter=3, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Data, index=0, value=FQ(255)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    # TxLogFieldTag is decreasing
    ops = [
        StartOp(),
        TxLogOp(rw_counter=2, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Data, index=0, value=FQ(10)),
        TxLogOp(rw_counter=1, rw=RW.Write, tx_id=1, log_id=1, field_tag=TxLogFieldTag.Address, index=0, value=FQ(124)),
        TxLogOp(rw_counter=3, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Data, index=0, value=FQ(255)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    # when tx_id change, log_id is not reset
    ops = [
        StartOp(),
        TxLogOp(rw_counter=2, rw=RW.Write, tx_id=1, log_id=0, field_tag=TxLogFieldTag.Data, index=0, value=FQ(10)),
        TxLogOp(rw_counter=1, rw=RW.Write, tx_id=1, log_id=1, field_tag=TxLogFieldTag.Address, index=0, value=FQ(124)),
        TxLogOp(rw_counter=3, rw=RW.Write, tx_id=2, log_id=1, field_tag=TxLogFieldTag.Data, index=0, value=FQ(255)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)


def test_tx_receipt_bad():
    # fmt: off
    # PostStateOrStatus is invalid
    ops = [
        StartOp(),
        TxReceiptOp(rw_counter=1, rw=RW.Read, tx_id=1, field_tag=TxReceiptFieldTag.PostStateOrStatus, value=FQ(3)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    # tx_id is decreasing when changes
    ops = [
        StartOp(),
        TxReceiptOp(rw_counter=1, rw=RW.Read, tx_id=2, field_tag=TxReceiptFieldTag.PostStateOrStatus, value=FQ(3)),
        TxReceiptOp(rw_counter=2, rw=RW.Read, tx_id=1, field_tag=TxReceiptFieldTag.CumulativeGasUsed, value=FQ(200)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)

    # fmt: off
    # tx_id is not increasing by one
    ops = [
        StartOp(),
        TxReceiptOp(rw_counter=1, rw=RW.Read, tx_id=1, field_tag=TxReceiptFieldTag.PostStateOrStatus, value=FQ(3)),
        TxReceiptOp(rw_counter=2, rw=RW.Read, tx_id=5, field_tag=TxReceiptFieldTag.CumulativeGasUsed, value=FQ(200)),
    ]
    # fmt: on
    verify(ops, randomness, success=False)
