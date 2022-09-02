import traceback
from typing import Union, List, Callable
from eth_keys import keys
from eth_utils import keccak
import rlp
from zkevm_specs.public_inputs import *
from zkevm_specs.util import FQ, RLC, U64, U256, U160
import random
from random import randrange, randbytes

random.seed(1234)
randomness = FQ(randrange(FQ.field_modulus))
rand_rpi = randomness  # Simulate a randomness for now


def verify(
    public_data_or_witness: Union[PublicData, Witness],
    MAX_TXS: int,
    MAX_CALLDATA_BYTES: int,
    rand_rpi: FQ,
    success: bool = True,
):
    """
    Verify the circuit with the assigned witness (or the witness calculated
    from the PublicData).  If `success` is False, expect the verification to
    fail.
    """
    witness = public_data_or_witness
    if isinstance(public_data_or_witness, Witness):
        pass
    else:
        witness = public_data2witness(public_data_or_witness, MAX_TXS, MAX_CALLDATA_BYTES, rand_rpi)

    ok = True
    if success:
        verify_circuit(
            witness,
            MAX_TXS,
            MAX_CALLDATA_BYTES,
        )
    else:
        try:
            verify_circuit(
                witness,
                MAX_TXS,
                MAX_CALLDATA_BYTES,
            )
        except AssertionError as e:
            ok = False
    assert ok == success


def rand_u256() -> U256:
    return U256(randrange(0, 2**256))


def rand_u160() -> U160:
    return U160(randrange(0, 2**160))


def rand_u64() -> U64:
    return U64(randrange(0, 2**64))


def rand_block() -> Block:
    return Block(
        hash=rand_u256(),
        parent_hash=rand_u256(),
        uncle_hash=rand_u256(),
        coinbase=rand_u160(),
        state_root=rand_u256(),
        tx_hash=rand_u256(),
        receipt_hash=rand_u256(),
        bloom=randbytes(256),
        difficulty=rand_u256(),
        number=rand_u64(),
        gas_limit=rand_u64(),
        gas_used=rand_u64(),
        time=rand_u64(),
        extra=bytes([]),
        mix_digest=rand_u256(),
        nonce=rand_u64(),
        base_fee=U256(0),
    )


def rand_tx(calldata_len: int) -> Transaction:
    return Transaction(
        nonce=rand_u64(),
        gas_price=rand_u256(),
        gas=rand_u64(),
        from_addr=rand_u160(),
        to_addr=rand_u160(),
        value=rand_u256(),
        data=randbytes(calldata_len),
        tx_sign_hash=rand_u256(),
    )


def rand_public_data(txs_len: int, MAX_CALLDATA_BYTES: int) -> PublicData:
    chain_id = U64(randrange(1, 128))
    block = rand_block()
    state_root_prev = rand_u256()
    block_hashes = [rand_u256() for _ in range(256)]
    txs = []
    for i in range(txs_len):
        txs.append(rand_tx(randrange(0, MAX_CALLDATA_BYTES // txs_len)))
    return PublicData(chain_id, block, state_root_prev, block_hashes, txs)


def test_basic():
    random.seed(0)

    MAX_TXS = 2
    MAX_CALLDATA_BYTES = 8

    public_data = rand_public_data(MAX_TXS - 1, MAX_CALLDATA_BYTES)
    verify(public_data, MAX_TXS, MAX_CALLDATA_BYTES, rand_rpi)


def override_not_success(override: Callable[Witness, None]):
    random.seed(0)

    MAX_TXS = 2
    MAX_CALLDATA_BYTES = 8

    public_data = rand_public_data(MAX_TXS - 1, MAX_CALLDATA_BYTES)
    witness = public_data2witness(public_data, MAX_TXS, MAX_CALLDATA_BYTES, rand_rpi)
    override(witness)
    verify(witness, MAX_TXS, MAX_CALLDATA_BYTES, rand_rpi, success=False)


def test_bad_rpi_rlc_acc():
    def override(witness):
        witness.rows[10].rpi_rlc_acc = FQ(123)

    override_not_success(override)


def test_bad_rand_rpi_col():
    def override(witness):
        witness.rows[10].rand_rpi = FQ(123)

    override_not_success(override)


def test_bad_block_table():
    def override(witness):
        witness.rows[5].block_table.value = FQ(123)

    override_not_success(override)


def test_bad_tx_table_tx_id():
    def override(witness):
        witness.rows[5].tx_table.tx_id = FQ(123)

    override_not_success(override)


def test_bad_tx_table_index():
    def override(witness):
        witness.rows[5].tx_table.index = FQ(123)

    override_not_success(override)


def test_bad_tx_table_value():
    def override(witness):
        witness.rows[5].tx_table.value = FQ(123)

    override_not_success(override)


def test_bad_rand_rpi_pub():
    def override(witness):
        witness.public_inputs.rand_rpi = FQ(123)

    override_not_success(override)


def test_bad_rand_rpi_rlc_pub():
    def override(witness):
        witness.public_inputs.rpi_rlc = FQ(123)

    override_not_success(override)


def test_bad_rand_rpi_chain_id_pub():
    def override(witness):
        witness.public_inputs.chain_id = FQ(123)

    override_not_success(override)


def test_bad_rand_rpi_state_root_pub():
    def override(witness):
        witness.public_inputs.state_root = FQ(123)

    override_not_success(override)


def test_bad_rand_rpi_state_root_prev_pub():
    def override(witness):
        witness.public_inputs.state_root_prev = FQ(123)

    override_not_success(override)


def test_bad_rand_rpi_state_root_prev_pub():
    def override(witness):
        witness.public_inputs.state_root_prev = FQ(123)

    override_not_success(override)
