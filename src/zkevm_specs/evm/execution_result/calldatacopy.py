from ...util import linear_combine, le_to_int, EMPTY_CODE_HASH
from ..common_assert import assert_bool
from ..step import Step
from ..table import FixedTableTag, RWTableTag, CallContextTag, TxTableTag
from ..opcode import Opcode
from .execution_result import ExecutionResult

MAX_COPY_LENGTH = 64

def calldatacopy(curr: Step, next: Step, r: int, opcode: Opcode):
    assert opcode == Opcode.CALLDATACOPY

    first = curr.allocate(1)[0]
    assert_bool(first)
    # Verify the first == 1 for the first CallDataCopy slot
    prev_opcode = curr.bytecode_lookup(
        [curr.call.opcode_source, curr.call.program_counter-1])
    is_calldatacopy = curr.is_zero(prev_opcode - Opcode.CALLDATACOPY)
    assert (1 - is_calldatacopy) * (1 - first) == 0

    # get the memory offset, data offset, and remaining length
    if first:
        bytes_mem_offset = curr.decompress(curr.stack_pop_lookup(), 32, r)
        bytes_data_offset = curr.decompress(curr.stack_pop_lookup(), 32, r)
        bytes_length = curr.decompress(curr.stack_pop_lookup(), 5, r)

        mem_offset = le_to_int(bytes_mem_offset[:5])
        data_offset = le_to_int(bytes_mem_offset[:5])
        length = le_to_int(length)

        next_memory_words = curr.calc_memory_words(bytes_mem_offset, bytes_length)
        memory_gas_cost = curr.calc_memory_gas_cost(next_memory_words)
    else:
        mem_offset, data_offset, length = curr.allocate(3)
        memory_gas_cost = 0

    # allocate data, selectors, boundary check witness
    data = curr.allocate_byte(MAX_COPY_LENGTH)
    selectors = curr.allocate(MAX_COPY_LENGTH)
    # bound_dist[i] = max(call_data_length - data_offset - i, 0)
    # when data_offset+i is out of bound, bound_dist should be 0
    bound_dist = curr.allocate(MAX_COPY_LENGTH)
    bound_dist_iszero = [curr.is_zero(diff) for diff in bound_diff]
    # get call data length
    tx_id = curr.call_context_lookup(CallContextTag.TxId)
    cd_length = curr.tx_lookup(tx_id, TxTableTag.CalldataLength) if curr.call.is_root \
        else curr.call_context_lookup(CallContextTag.CalldataLength)

    # Constraints for selectors
    # 1. selectors need to be boolean
    # 2. selectors sequence is non-increasing
    for s in selectors:
        assert_bool(s)
    for i in range(1, MAX_COPY_LENGTH):
        diff = selectors[i-1] - selectors[i]
        assert_bool(diff)

    # Verify that the number of bytes copied doesn't not exceed the remaining length
    # We assume that length can be up to 5 bytes
    num_bytes = sum(selectors)
    lt, eq = curr.compare(num_bytes, length, 5)
    assert (1-lt) * (1-eq) == 0
    finished = eq

    # The constraints for the first boundary distance:
    # 1. bound_dist[0] == 0 || bound_dist[0] == cd_length - data_offset
    # 2. bound_dist[0] \in 0..2^40-1
    assert bound_dist[0] * (cd_length-data_offset-bound_dist[0]) == 0
    self.bytes_range_lookup(bound_dist[0], 4)
    # We can simplify the constraints for the rest boundary distance by checking the diff
    # 1. diff == 0 or 1
    # 2. diff == 1 when bound_dist[i-1] != 0 & bound_dist_iszero[i-1] == 0
    # 3. diff == 0 when bound_dist[i-1] == 0 & bound_dist_iszero[i-1] == 1
    for i in range(1, MAX_COPY_LENGTH):
        diff = bound_dist[i-1] - bound_dist[i]
        assert_bool(diff)
        assert (1-bound_dist_iszero[i-1]) * (1-diff) == 0
        assert bound_dist_iszero[i-1] * diff == 0

    if curr.call.is_root:
        for i in range(MAX_COPY_LENGTH):
            if selectors[i]:
                # Address is out of bound
                assert bound_dist_iszero[i] * data[i] == 0
                if bound_dist_iszero[i] == 0:
                    assert data[i] == curr.tx_lookup(tx_id, TxTableTag.Calldata, data_offset+i)
                    assert data[i] == curr.memory_w_lookup(mem_offset+i)
            else:
                assert data[i] == 0
    else:
        cd_offset = curr.call_context_lookup(CallContextTag.CalldataOffset)
        for i in range(MAX_COPY_LENGTH):
            if selectors[i]:
                # Address is out of bound
                assert bound_dist_iszero[i] * data[i] == 0
                if bound_dist_iszero[i] == 0:
                    assert data[i] == curr.memory_r_lookup(cd_offset+data_offset+i)
                    assert data[i] == curr.memory_w_lookup(mem_offset+i)
            else:
                assert data[i] == 0

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

    # 3 stack pops in the first step of CallDataCopy
    # num_bytes read from memory in the internal call
    assert curr.rw_counter_diff == first * (3 + num_bytes * (2 - curr.call.is_root))
    assert curr.stack_pointer_diff == first * 3
    next_gas_left = curr.call.gas_left - first * (GAS_FASTEST_STEP + memory_gas_cost)
    curr.bytes_range_lookup(next_gas_left, 8)

    curr.assert_step_transition(
        next,
        rw_counter_diff=curr.rw_counter_diff,
        execution_result_not=ExecutionResult.BEGIN_TX,
        program_counter_diff=finished,
        stack_pointer_diff=curr.stack_pointer_diff,
        gas_left=next_gas_left,
    )
