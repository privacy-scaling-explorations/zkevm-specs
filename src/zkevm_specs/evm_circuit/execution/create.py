from zkevm_specs.evm_circuit.opcode import Opcode
from zkevm_specs.util.arithmetic import FQ, Word, WordOrValue
from zkevm_specs.util.hash import EMPTY_CODE_HASH
from zkevm_specs.util.param import (
    GAS_COST_COPY_SHA3,
    GAS_COST_CREATE,
    MAX_U64,
    N_BYTES_ACCOUNT_ADDRESS,
    N_BYTES_GAS,
    N_BYTES_MEMORY_ADDRESS,
    N_BYTES_MEMORY_WORD_SIZE,
    N_BYTES_STACK,
    N_BYTES_U64,
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
    caller_address_word = instruction.call_context_lookup_word(CallContextFieldTag.CallerAddress)
    caller_address = instruction.word_to_address(caller_address_word)
    nonce, nonce_prev = instruction.account_write(caller_address, AccountFieldTag.Nonce)
    balance = instruction.account_read(caller_address, AccountFieldTag.Balance)
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    reversion_info = instruction.reversion_info()

    has_init_code = size != FQ(0)

    ### Gas cost calculation
    # gas cost of memory expansion
    (
        next_memory_size,
        memory_expansion_gas_cost,
    ) = instruction.memory_expansion(
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
        memory_size, _ = instruction.constant_divmod(
            size + FQ(31), FQ(32), N_BYTES_MEMORY_WORD_SIZE
        )
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

    ### Do stack depth, nonce and balance pre-check
    # ErrDepth constraint
    is_depth_ok, _ = instruction.compare(depth, FQ(1025), N_BYTES_STACK)
    # ErrInsufficientBalance constraint
    is_insufficient_balance, _ = instruction.compare_word(Word(balance.expr().n), value_word)
    # ErrNonceUintOverflow constraint
    is_nonce_in_range, _ = instruction.compare(nonce_prev, FQ(MAX_U64), N_BYTES_U64)

    # pass the pre-check if none of above errors happen
    is_precheck_ok = (
        is_depth_ok == FQ(1) and is_insufficient_balance == FQ(0) and is_nonce_in_range == FQ(1)
    )

    not_address_collision = False
    if is_precheck_ok:
        # calculate contract address
        code_hash = instruction.curr.aux_data if has_init_code else Word(EMPTY_CODE_HASH)
        contract_address = (
            instruction.generate_contract_address(caller_address, nonce)
            if is_create == 1
            else instruction.generate_CREAET2_contract_address(caller_address, salt_word, code_hash)
        )
        contract_address_word = instruction.address_to_word(contract_address)

        # add contract address to access list
        instruction.add_account_to_access_list(tx_id, contract_address)

        # ErrContractAddressCollision, if any one of following criteria meets.
        # Nonce is not zero or account code hash is not either 0 or EMPTY_CODE_HASH.
        callee_code_hash = instruction.account_read_word(contract_address, AccountFieldTag.CodeHash)
        callee_nonce = instruction.account_read(contract_address, AccountFieldTag.Nonce)
        is_zero_nonce = instruction.is_zero(callee_nonce)
        is_empty_hash = instruction.is_equal_word(callee_code_hash, Word(EMPTY_CODE_HASH))
        is_zero_hash = instruction.is_equal_word(callee_code_hash, Word(0))
        if is_zero_nonce == FQ(1) and (is_empty_hash == FQ(1) or is_zero_hash == FQ(1)):
            not_address_collision = True

        if not_address_collision:
            # verify return contract address
            instruction.constrain_equal(
                instruction.word_to_fq(return_contract_address_word, N_BYTES_ACCOUNT_ADDRESS),
                is_success.expr() * contract_address.expr(),
            )

            # Propagate is_persistent
            callee_reversion_info = instruction.reversion_info(call_id=callee_call_id)
            instruction.constrain_equal(
                callee_reversion_info.is_persistent,
                reversion_info.is_persistent * is_success.expr(),
            )

            # transfer value from caller to contract address
            instruction.transfer(
                caller_address, contract_address, value_word, callee_reversion_info
            )

            # EIP 161, the nonce of a newly created contract is 1
            nonce, _ = instruction.account_write(contract_address, AccountFieldTag.Nonce)
            instruction.constrain_equal(nonce, FQ(1))

            # CREATE:  3 pops and 1 push, stack delta = 2
            # CREATE2: 4 pops and 1 push, stack delta = 3
            stack_pointer_delta = 2 + is_create2

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

                # verify the equality of input `size` and length of calldata
                code_size = instruction.bytecode_length(instruction.next.code_hash)
                instruction.constrain_equal(code_size, size)

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
                for field_tag, expected_word_or_value in [
                    (CallContextFieldTag.CallerId, instruction.curr.call_id),
                    (CallContextFieldTag.TxId, tx_id),
                    (CallContextFieldTag.Depth, depth.expr() + 1),
                    (CallContextFieldTag.CallerAddress, caller_address_word),
                    (CallContextFieldTag.CalleeAddress, contract_address_word),
                    (CallContextFieldTag.IsSuccess, is_success),
                    (CallContextFieldTag.IsStatic, FQ(False)),
                    (CallContextFieldTag.IsRoot, FQ(False)),
                    (CallContextFieldTag.IsCreate, FQ(True)),
                ]:
                    assert isinstance(expected_word_or_value, FQ) or isinstance(
                        expected_word_or_value, Word
                    )
                    instruction.constrain_equal_word(
                        instruction.call_context_lookup_word(field_tag, call_id=callee_call_id),
                        WordOrValue(expected_word_or_value),
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
                    memory_word_size=Transition.to(next_memory_size),
                    # Always stay same
                    call_id=Transition.same(),
                    is_root=Transition.same(),
                    is_create=Transition.same(),
                    code_hash=Transition.same_word(),
                )

    # error cases
    if not is_precheck_ok or not not_address_collision:
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
            stack_pointer=Transition.delta(2 + is_create2),
            reversible_write_counter=Transition.delta(1),
            gas_left=Transition.delta(-gas_cost),
            memory_word_size=Transition.to(next_memory_size),
            # Always stay same
            call_id=Transition.same(),
            is_root=Transition.same(),
            is_create=Transition.same(),
            code_hash=Transition.same_word(),
        )
