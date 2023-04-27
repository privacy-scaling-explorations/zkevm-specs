from zkevm_specs.evm_circuit.opcode import Opcode
from zkevm_specs.util.arithmetic import FQ, Word, WordOrValue
from zkevm_specs.util.hash import EMPTY_CODE_HASH
from zkevm_specs.util.param import (
    GAS_COST_COPY_SHA3,
    GAS_COST_CREATE,
    N_BYTES_ACCOUNT_ADDRESS,
    N_BYTES_GAS,
    N_BYTES_MEMORY_ADDRESS,
    N_BYTES_MEMORY_SIZE,
    N_BYTES_U64,
)
from ...util import (
    CALL_CREATE_DEPTH,
)
from ..instruction import Instruction, Transition
from ..table import RW, CallContextFieldTag, AccountFieldTag, CopyDataTypeTag


def create(instruction: Instruction):
    # check opcode is CREATE or CREATE2
    opcode = instruction.opcode_lookup(True)
    is_create, is_create2 = instruction.pair_select(opcode, Opcode.CREATE, Opcode.CREATE2)
    instruction.responsible_opcode_lookup(opcode)

    # set the caller_id to the current rw_counter
    callee_call_id = instruction.curr.rw_counter

    # Stack parameters and result
    value_word = instruction.stack_pop()
    offset_word = instruction.stack_pop()
    size_word = instruction.stack_pop()
    salt_word = instruction.stack_pop() if is_create2 == FQ(1) else Word(0)
    return_contract_address_word = instruction.stack_push()

    offset = instruction.word_to_fq(offset_word, N_BYTES_MEMORY_ADDRESS)  # src_addr
    size = instruction.word_to_fq(size_word, N_BYTES_MEMORY_ADDRESS)

    depth = instruction.call_context_lookup(CallContextFieldTag.Depth)
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    caller_address = instruction.call_context_lookup(CallContextFieldTag.CallerAddress)
    nonce, nonce_prev = instruction.account_write(caller_address, AccountFieldTag.Nonce)
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    is_static = instruction.call_context_lookup(CallContextFieldTag.IsStatic)
    reversion_info = instruction.reversion_info()

    has_init_code = size != FQ(0)

    # calculate contract address
    code_hash = instruction.next.code_hash if has_init_code else Word(EMPTY_CODE_HASH)
    contract_address = (
        instruction.generate_contract_address(caller_address, nonce)
        if is_create == 1
        else instruction.generate_CREAET2_contract_address(caller_address, salt_word, code_hash)
    )

    if has_init_code:
        # verify the equality of input `size` and length of calldata
        code_size = instruction.bytecode_length(instruction.next.code_hash)
        instruction.constrain_equal(code_size, size)

    # verify return contract address
    instruction.constrain_equal(
        instruction.word_to_fq(return_contract_address_word, N_BYTES_ACCOUNT_ADDRESS),
        is_success * contract_address,
    )

    # Verify depth is less than 1024
    instruction.range_lookup(depth, CALL_CREATE_DEPTH)

    # ErrNonceUintOverflow constraint
    (is_not_overflow, _) = instruction.compare(nonce, nonce_prev, N_BYTES_U64)
    instruction.is_zero(is_not_overflow)

    # add contract address to access list
    instruction.add_account_to_access_list(tx_id, contract_address)

    # ErrContractAddressCollision constraint
    # code_hash_prev could be either 0 or EMPTY_CODE_HASH
    # code_hash should be EMPTY_CODE_HASH to make sure the account is created properly
    code_hash, code_hash_prev = instruction.account_write_word(
        contract_address, AccountFieldTag.CodeHash
    )
    instruction.constrain_in_word(
        code_hash_prev,
        [Word(0), Word(EMPTY_CODE_HASH)],
    )
    instruction.constrain_equal_word(code_hash, Word(EMPTY_CODE_HASH))

    # Propagate is_persistent
    callee_reversion_info = instruction.reversion_info(call_id=callee_call_id)
    instruction.constrain_equal(
        callee_reversion_info.is_persistent,
        reversion_info.is_persistent * is_success.expr(),
    )

    # can't be a STATICCALL
    instruction.is_zero(is_static)

    # transfer value from caller to contract address
    instruction.transfer(caller_address, contract_address, value_word, callee_reversion_info)

    # gas cost of memory expansion
    (next_memory_size, memory_expansion_gas_cost,) = instruction.memory_expansion(
        offset,
        size,
    )

    # CREATE = GAS_COST_CREATE + memory expansion + GAS_COST_CODE_DEPOSIT * len(byte_code)
    # CREATE2 = gas cost of CREATE + GAS_COST_COPY_SHA3 * memory_size
    # byte_code is only available in `return_revert`,
    # so the last part (GAS_COST_CODE_DEPOSIT * len(byte_code)) won't be calculated here
    gas_left = instruction.curr.gas_left
    gas_cost = GAS_COST_CREATE + memory_expansion_gas_cost
    if is_create2 == 1:
        memory_size, _ = instruction.constant_divmod(size + FQ(31), FQ(32), N_BYTES_MEMORY_SIZE)
        gas_cost += GAS_COST_COPY_SHA3 * memory_size
    gas_available = gas_left - gas_cost

    # Apply EIP 150
    one_64th_gas, _ = instruction.constant_divmod(gas_available, FQ(64), N_BYTES_GAS)
    all_but_one_64th_gas = gas_available - one_64th_gas
    is_u64_gas = instruction.is_zero(
        instruction.sum(WordOrValue(gas_left).to_le_bytes()[N_BYTES_GAS:])
    )
    callee_gas_left = instruction.select(
        is_u64_gas,
        instruction.min(all_but_one_64th_gas, gas_left, N_BYTES_GAS),
        all_but_one_64th_gas,
    )

    if has_init_code:
        # copy init_code from memory to bytecode
        copy_rwc_inc, _ = instruction.copy_lookup(
            instruction.curr.call_id,  # src_id
            CopyDataTypeTag.Memory,  # src_type
            instruction.next.code_hash,  # dst_id
            CopyDataTypeTag.Bytecode,  # dst_type
            offset,  # src_addr
            offset + size,  # src_addr_boundary
            FQ(0),  # dst_addr
            size,  # length
            instruction.curr.rw_counter + instruction.rw_counter_offset,
        )
        instruction.rw_counter_offset += int(copy_rwc_inc)

    # CREATE:  3 pops and 1 push, stack delta = 2
    # CREATE2: 4 pops and 1 push, stack delta = 3
    stack_pointer_delta = 2 + is_create2

    if has_init_code:
        # Save caller's call state
        for field_tag, expected_value in [
            (CallContextFieldTag.ProgramCounter, instruction.curr.program_counter + 1),
            (
                CallContextFieldTag.StackPointer,
                instruction.curr.stack_pointer + stack_pointer_delta,
            ),
            (CallContextFieldTag.GasLeft, gas_left - gas_cost - callee_gas_left),
            (CallContextFieldTag.MemorySize, next_memory_size),
            (
                CallContextFieldTag.ReversibleWriteCounter,
                instruction.curr.reversible_write_counter + 1,
            ),
        ]:
            instruction.constrain_equal(
                instruction.call_context_lookup(field_tag, RW.Write),
                expected_value,
            )
        # Setup next call's context.
        for field_tag, expected_value in [
            (CallContextFieldTag.CallerId, instruction.curr.call_id),
            (CallContextFieldTag.TxId, tx_id),
            (CallContextFieldTag.Depth, depth + 1),
            (CallContextFieldTag.CallerAddress, caller_address),
            (CallContextFieldTag.CalleeAddress, contract_address),
            (CallContextFieldTag.IsSuccess, is_success),
            (CallContextFieldTag.IsStatic, FQ(False)),
            (CallContextFieldTag.IsRoot, FQ(False)),
            (CallContextFieldTag.IsCreate, FQ(True)),
        ]:
            instruction.constrain_equal(
                instruction.call_context_lookup(field_tag, call_id=callee_call_id),
                expected_value,
            )
        instruction.constrain_equal_word(
            instruction.call_context_lookup_word(
                CallContextFieldTag.CodeHash, call_id=callee_call_id
            ),
            code_hash,
        )

        instruction.step_state_transition_to_new_context(
            rw_counter=Transition.delta(instruction.rw_counter_offset),
            call_id=Transition.to(callee_call_id),
            is_root=Transition.to(False),
            is_create=Transition.to(True),
            code_hash=Transition.to_word(instruction.next.code_hash),
            gas_left=Transition.to(callee_gas_left),
            # `transfer` includes two balance updates
            reversible_write_counter=Transition.to(2),
            log_id=Transition.same(),
        )
    else:
        for field_tag, expected_value in [
            (CallContextFieldTag.LastCalleeId, FQ(0)),
            (CallContextFieldTag.LastCalleeReturnDataOffset, FQ(0)),
            (CallContextFieldTag.LastCalleeReturnDataLength, FQ(0)),
        ]:
            instruction.constrain_equal(
                instruction.call_context_lookup(field_tag, RW.Write),
                expected_value,
            )

        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(instruction.rw_counter_offset),
            program_counter=Transition.delta(1),
            stack_pointer=Transition.delta(stack_pointer_delta),
            gas_left=Transition.delta(-gas_cost),
            reversible_write_counter=Transition.delta(3),
            # Always stay same
            memory_word_size=Transition.same(),
            call_id=Transition.same(),
            is_root=Transition.same(),
            is_create=Transition.same(),
            code_hash=Transition.same_word(),
        )
