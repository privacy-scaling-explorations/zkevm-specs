from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, TxLogFieldTag, TxContextFieldTag
from ..opcode import Opcode
from ...util.param import LOG_STATIC_GAS


def log(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    # constrain op in [log0, log4] range
    instruction.range_lookup(opcode - Opcode.LOG0, 5)
    # pop `mstart`, `msize` from stack
    mstart = instruction.rlc_to_int_exact(instruction.stack_pop(), 8)
    msize = instruction.rlc_to_int_exact(instruction.stack_pop(), 8)
    topics = []
    # tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    # rw_counter_end_of_reversion = instruction.call_context_lookup(
    #     CallContextFieldTag.RwCounterEndOfReversion
    # )
    # is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)

    for i in range(opcode - Opcode.LOG0):
        stack_topic = instruction.stack_pop()
        topics.append(stack_topic)
        # instruction.tx_log_write_with_reversion(TxLogFieldTag.Topics,is_persistent,
        #     rw_counter_end_of_reversion, i)

    # check memory copy
    memory_data = []
    for i in range(msize):
        address = mstart + i + 1
        data_byte = instruction.memory_read(address, instruction.curr.call_id)
        memory_data.append(data_byte)

    # constrain topics in logs
    for i in range(len(topics)):
        topic_in_log = instruction.tx_log_lookup(TxLogFieldTag.Topics, i)
        instruction.constrain_equal(topic_in_log, topics[i])

    # constrain data in logs
    for i in range(len(memory_data)):
        byte_in_log = instruction.tx_log_lookup(TxLogFieldTag.Data, i)
        instruction.constrain_equal(byte_in_log, memory_data[i])

    # check contract address validity, use call context's  callee address as contract address when it is
    # contract call, if in contract creation, constructing it as creating address in witness generation process. .
    # contract_address = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CalleeAddress)
    contract_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)
    address = instruction.tx_log_lookup(TxLogFieldTag.Address)
    instruction.constrain_equal(contract_address, address)

    # omit block number constraint even it is set within op code explicitly, because by default the circuit only handle
    # current block, otherwise, block context lookup is required.
    # calculate dynamic gas cost
    _, memory_expansion_cost = instruction.memory_expansion_constant_length(mstart, msize)
    dynamic_gas = LOG_STATIC_GAS * (opcode - Opcode.LOG0) + 8 * msize + memory_expansion_cost

    rw_counter_diff = 2 + opcode - Opcode.LOG0 + 1
    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(rw_counter_diff),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2 + opcode - Opcode.LOG0),
        state_write_counter=Transition.delta(1),
        dynamic_gas_cost=dynamic_gas,
    )
