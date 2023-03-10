from zkevm_specs.evm.opcode import Opcode
from zkevm_specs.util.arithmetic import FQ, RLC
from zkevm_specs.util.hash import EMPTY_CODE_HASH
from zkevm_specs.util.param import (
    GAS_COST_COPY_SHA3,
    GAS_COST_CREATE,
    N_BYTES_ACCOUNT_ADDRESS,
    N_BYTES_GAS,
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
    value = instruction.stack_pop()
    offset_rlc = instruction.stack_pop()
    size_rlc = instruction.stack_pop()
    salt_rlc = instruction.stack_pop() if is_create2 == FQ(1) else RLC(0)
    return_contract_address = instruction.stack_push()

    offset = instruction.rlc_to_fq(offset_rlc, N_BYTES_U64)
    size = instruction.rlc_to_fq(size_rlc, N_BYTES_U64)

    depth = instruction.call_context_lookup(CallContextFieldTag.Depth)
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    caller_address = instruction.call_context_lookup(CallContextFieldTag.CallerAddress)
    nonce, nonce_prev = instruction.account_write(caller_address, AccountFieldTag.Nonce)
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    is_static = instruction.call_context_lookup(CallContextFieldTag.IsStatic)
    reversion_info = instruction.reversion_info()

    # calculate contract address
    contract_address = (
        instruction.generate_contract_address(caller_address, nonce)
        if is_create == 1
        else instruction.generate_CREAET2_contract_address(
            caller_address, salt_rlc.le_bytes, instruction.next.code_hash
        )
    )

    # verify return contract address
    instruction.constrain_equal(
        instruction.rlc_to_fq(return_contract_address, N_BYTES_ACCOUNT_ADDRESS),
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
    code_hash, code_hash_prev = instruction.account_write(
        contract_address, AccountFieldTag.CodeHash
    )
    instruction.constrain_in(code_hash_prev, [FQ(0), RLC(EMPTY_CODE_HASH).expr()])
    instruction.constrain_equal(code_hash, RLC(EMPTY_CODE_HASH))

    # Propagate is_persistent
    callee_reversion_info = instruction.reversion_info(call_id=callee_call_id)
    instruction.constrain_equal(
        callee_reversion_info.is_persistent,
        reversion_info.is_persistent * is_success,
    )

    # can't be a STATICCALL
    instruction.is_zero(is_static)

    # transfer value from caller to contract address
    instruction.transfer(caller_address, contract_address, value, callee_reversion_info)

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
        memory_size, _ = instruction.constant_divmod(size.expr() + 31, FQ(32), N_BYTES_MEMORY_SIZE)
        gas_cost += GAS_COST_COPY_SHA3 * memory_size
    gas_available = gas_left - gas_cost

    # Apply EIP 150
    one_64th_gas, _ = instruction.constant_divmod(gas_available, FQ(64), N_BYTES_GAS)
    all_but_one_64th_gas = gas_available - one_64th_gas
    is_u64_gas = instruction.is_zero(
        instruction.sum(instruction.rlc_encode(gas_left, N_BYTES_GAS).le_bytes[N_BYTES_GAS:])
    )
    callee_gas_left = instruction.select(
        is_u64_gas,
        instruction.min(all_but_one_64th_gas, gas_left, N_BYTES_GAS),
        all_but_one_64th_gas,
    )

    # copy init_code from memory to bytecode
    copy_rwc_inc, _ = instruction.copy_lookup(
        instruction.curr.call_id,  # src_id
        CopyDataTypeTag.Memory,  # src_type
        instruction.next.code_hash.expr(),  # dst_id
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
        (CallContextFieldTag.TxId, tx_id.expr()),
        (CallContextFieldTag.Depth, depth.expr() + 1),
        (CallContextFieldTag.CallerAddress, caller_address.expr()),
        (CallContextFieldTag.CalleeAddress, contract_address.expr()),
        (CallContextFieldTag.IsSuccess, FQ(True)),
        (CallContextFieldTag.IsStatic, FQ(False)),
        (CallContextFieldTag.IsRoot, FQ(False)),
        (CallContextFieldTag.IsCreate, FQ(False)),
        (CallContextFieldTag.CodeHash, code_hash),
    ]:
        instruction.constrain_equal(
            instruction.call_context_lookup(field_tag, call_id=callee_call_id),
            expected_value,
        )

    instruction.step_state_transition_to_new_context(
        rw_counter=Transition.delta(instruction.rw_counter_offset),
        call_id=Transition.to(callee_call_id),
        is_root=Transition.to(False),
        is_create=Transition.to(False),
        code_hash=Transition.to(instruction.next.code_hash),
        gas_left=Transition.to(callee_gas_left),
        # `transfer` includes two balance updates
        reversible_write_counter=Transition.to(2),
        log_id=Transition.same(),
    )
