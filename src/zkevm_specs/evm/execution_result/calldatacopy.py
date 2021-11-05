from ...util import linear_combine, le_to_int, EMPTY_CODE_HASH
from ..common_assert import assert_bool
from ..step import Step
from ..table import FixedTableTag, RWTableTag, CallContextTag, TxTableTag
from ..opcode import Opcode
from .execution_result import ExecutionResult

MAX_COPY_LENGTH = 64

def calldatacopy(curr: Step, next: Step, r: int, opcode: Opcode):
    assert opcode == Opcode.CALLDATACOPY

    first, mem_offset, data_offset, length = curr.allocate(4)
    data = curr.allocate(MAX_COPY_LENGTH)
    selectors = curr.allocate(MAX_COPY_LENGTH)
    # bound_dist[i] = max(call_data_length - data_offset - i, 0)
    # when data_offset+i is out of bound, bound_dist should be 0
    bound_dist = curr.allocate(MAX_COPY_LENGTH)
    bound_dist_iszero = [curr.is_zero(diff) for diff in bound_diff]
    # call data length
    cd_length = curr.tx_lookup(tx_id, TxTableTag.CalldataLength) if curr.call.is_root \
        else curr.call_context_lookup(CallContextTag.CalldataLength)

    assert_bool(first)
    # byte within [0, 256)
    for byte in data:
        curr.byte_range_lookup(byte)
    # selectors need to be boolean
    for s in selectors:
        assert_bool(s)
    # prove selectors are non-increasing
    for i in range(1, MAX_COPY_LENGTH):
        diff = selectors[i-1] - selectors[i]
        assert_bool(diff)
    # make sure the number of bytes copied not exceed the remaining length
    # here we assume that length can be up to 5 bytes
    lt, eq = curr.compare(sum(selectors), length, 5)
    assert (1-lt) * (1-eq) == 0
    finished = eq

    # bound_dist[0] == 0 || bound_dist[0] == cd_length - data_offset
    # TODO: check bound_dist[0] is within a certain range
    assert bound_dist[0] * (cd_length-data_offset-bound_dist[0]) == 0
    for i in range(1, MAX_COPY_LENGTH):
        diff = bound_dist[i-1] - bound_dist[i]
        assert_bool(diff)
        # diff == 1 when bound_dist[i-1] != 0 & bound_dist_iszero[i-1] == 0
        # diff == 0 when bound_dist[i-1] == 0 & bound_dist_iszero[i-1] == 1
        assert (1-bound_dist_iszero[i-1]) * (1-diff) == 0
        assert bound_dist_iszero[i-1] * diff == 0

    if first == 1:
        # Previous opcode cannot be CallDataCopy
        prev_opcode = curr.bytecode_lookup(
            [curr.call.opcode_source, curr.call.program_counter-1])
        not_calldatacopy = curr.is_zero(prev_opcode - Opcode.CALLDATACOPY)
        assert not_calldatacopy == 0

        bytes_mem_offset = curr.decompress(curr.stack_pop_lookup(), 32, r)
        bytes_data_offset = curr.decompress(curr.stack_pop_lookup(), 32, r)
        bytes_length = curr.decompress(curr.stack_pop_lookup(), 8, r)

        assert mem_offset == le_to_int(bytes_mem_offset[:8])
        # TODO: handle data_offset overflow case
        assert data_offset == le_to_int(bytes_mem_offset[:8])
        assert length == le_to_int(length)

    if curr.call.is_root:
        tx_id = curr.call_context_lookup(CallContextTag.TxId)
        call_data_length = curr.tx_lookup(tx_id, TxTableTag.CalldataLength)

        for i in range(MAX_COPY_LENGTH):
            if selectors[i] == 1:
                # Address is out of bound
                assert bound_dist_iszero[i] * data[i] == 0
                if bound_dist_iszero[i] == 0:
                    assert data[i] == curr.tx_lookup(tx_id, TxTableTag.Calldata, data_offset+i)
                    assert data[i] == curr.memory_w_lookup(mem_offset+i)
    else:
        cd_offset = curr.call_context_lookup(CallContextTag.CalldataOffset)
        cd_length = curr.call_context_lookup(CallContextTag.CalldataLength)

        for i in range(MAX_COPY_LENGTH):
            if selectors[i] == 1:
                # Address is out of bound
                assert bound_dist_iszero[i] * data[i] == 0
                if bound_dist_iszero[i] == 0:
                    assert data[i] == curr.memory_r_lookup(cd_offset+data_offset+i)
                    assert data[i] == curr.memory_w_lookup(mem_offset+i)

    # check the state in the next step if CallDataCopy has not finished
    if not finished:
        next_first = next.peek_allocation(0)
        next_mem_offset = next.peek_allocation(1)
        next_data_offset = next.peek_allocation(2)
        next_length = next.peek_allocation(3)
        assert next_first == 0
        assert next_mem_offset == mem_offset + MAX_COPY_LENGTH
        assert next_data_offset == data_offset + MAX_COPY_LENGTH
        assert next_length == length - MAX_COPY_LENGTH

    # TODO: step transition
