import pytest

TESTING_DATA = (
    (
        Transaction(caller_address=rand_address(), callee_address=rand_address()),
        bytes([i for i in range(32, 0, -1)]),
    ),
)

@pytest.mark.parametrize("tx, slot_be_bytes", TESTING_DATA)
def test_sload(tx: Transaction, slot_be_bytes: bytes):
    rlc_store = RLCStore()

    storage_slot = rlc_store.to_rlc(bytes(reversed(slot_be_bytes)))

    # PUSH32 STORAGE_SLOT SLOAD STOP
    bytecode = Bytecode(f"7f{slot_be_bytes.hex()}5400")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    tables = Tables(
        tx_table=set(tx.table_assignments(rlc_store)),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        # TODO:
        rw_table=set(
            [
                (1, RW.Read, RWTableTag.Stack, 1, 1023, storage_slot, 0, 0),
                (2, RW.Read, RWTableTag.AccountStorage, 1, 1023, storage_slot, 0, 0),
                (3, RW.Write, RWTableTag.TxAccessListStorageSlot, 1, 1023, storage_slot, 0, 0),
                (4, RW.Write, RWTableTag.Stack, 1, 1023, 0, 0, 0),
            ]
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        tables=tables,
        # TODO:
        steps=[
        ],
    )
