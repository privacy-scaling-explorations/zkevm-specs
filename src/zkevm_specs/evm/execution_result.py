from enum import IntEnum, auto
from typing import Sequence

from .opcode import Opcode


class ExecutionResult(IntEnum):
    """
    All possible execution results an EVM step could encounter.
    """

    BEGIN_TX = auto()

    # Opcode's successful cases
    STOP = auto()
    ADD = auto()  # ADD, SUB
    MUL = auto()
    DIV = auto()
    SDIV = auto()
    MOD = auto()
    SMOD = auto()
    ADDMOD = auto()
    MULMOD = auto()
    EXP = auto()
    SIGNEXTEND = auto()
    LT = auto()  # LT, GT, EQ
    SLT = auto()  # SLT, SGT
    ISZERO = auto()
    AND = auto()  # AND, OR, XOR
    NOT = auto()
    BYTE = auto()
    SHL = auto()
    SHR = auto()
    SAR = auto()
    SHA3 = auto()
    ADDRESS = auto()
    BALANCE = auto()
    ORIGIN = auto()
    CALLER = auto()
    CALLVALUE = auto()
    CALLDATALOAD = auto()
    CALLDATASIZE = auto()
    CALLDATACOPY = auto()
    CODESIZE = auto()
    CODECOPY = auto()
    GASPRICE = auto()
    EXTCODESIZE = auto()
    EXTCODECOPY = auto()
    RETURNDATASIZE = auto()
    RETURNDATACOPY = auto()
    EXTCODEHASH = auto()
    BLOCKHASH = auto()
    COINBASE = auto()
    TIMESTAMP = auto()
    NUMBER = auto()
    DIFFICULTY = auto()
    GASLIMIT = auto()
    CHAINID = auto()
    SELFBALANCE = auto()
    BASEFEE = auto()
    POP = auto()
    MLOAD = auto()  # MLOAD, MSTORE, MSTORE8
    SLOAD = auto()
    SSTORE = auto()
    JUMP = auto()
    JUMPI = auto()
    PC = auto()
    MSIZE = auto()
    GAS = auto()
    JUMPDEST = auto()
    PUSH = auto()  # PUSH1, PUSH2, ..., PUSH32
    DUP = auto()  # DUP1, DUP2, ..., DUP16
    SWAP = auto()  # SWAP1, SWAP2, ..., SWAP16
    LOG = auto()  # LOG1, LOG2, ..., LOG5
    CREATE = auto()
    CALL = auto()
    CALLCODE = auto()
    RETURN = auto()
    DELEGATECALL = auto()
    CREATE2 = auto()
    STATICCALL = auto()
    REVERT = auto()
    SELFDESTRUCT = auto()

    # Error cases
    ERROR_INVALID_OPCODE = auto()
    # For opcodes who push more than pop
    ERROR_STACK_OVERFLOW = auto()
    # For opcodes who pop and DUP, SWAP who peek deeper element directly
    ERROR_STACK_UNDERFLOW = auto()
    # For opcodes who have non-zero constant gas cost
    ERROR_OOG_CONSTANT = auto()
    # For opcodes MLOAD, MSTORE, MSTORE8, CREATE, RETURN, REVERT, who have pure memory expansion gas cost
    ERROR_OOG_PURE_MEMORY = auto()
    # For opcodes who have dynamic gas usage rather than pure memory expansion
    ERROR_OOG_SHA3 = auto()
    ERROR_OOG_CALLDATACOPY = auto()
    ERROR_OOG_CODECOPY = auto()
    ERROR_OOG_EXTCODECOPY = auto()
    ERROR_OOG_RETURNDATACOPY = auto()
    ERROR_OOG_LOG = auto()
    ERROR_OOG_CALL = auto()
    ERROR_OOG_CALLCODE = auto()
    ERROR_OOG_DELEGATECALL = auto()
    ERROR_OOG_CREATE2 = auto()
    ERROR_OOG_STATICCALL = auto()
    # For SSTORE, LOG0, LOG1, LOG2, LOG3, LOG4, CREATE, CALL, CREATE2, SELFDESTRUCT
    ERROR_WRITE_PROTECTION = auto()
    # For CALL, CALLCODE, DELEGATECALL, STATICCALL
    ERROR_DEPTH = auto()
    # For CALL, CALLCODE
    ERROR_INSUFFICIENT_BALANCE = auto()
    # For CREATE, CREATE2
    ERROR_CONTRACT_ADDRESS_COLLISION = auto()
    ERROR_MAX_CODE_SIZE_EXCEEDED = auto()
    ERROR_INVALID_CODE = auto()
    # For REVERT
    ERROR_EXECUTION_REVERTED = auto()
    # For JUMP, JUMPI
    ERROR_INVALID_JUMP = auto()
    # For RETURNDATACOPY
    ERROR_RETURN_DATA_OUT_OF_BOUNDS = auto()

    # TODO: Precompile success and error cases

    def responsible_opcode(self) -> Sequence[Opcode]:
        if self == ExecutionResult.STOP:
            return [Opcode.STOP]
        elif self == ExecutionResult.ADD:
            return [
                Opcode.ADD,
                Opcode.SUB,
            ]
        elif self == ExecutionResult.MUL:
            return [Opcode.MUL]
        elif self == ExecutionResult.DIV:
            return [Opcode.DIV]
        elif self == ExecutionResult.SDIV:
            return [Opcode.SDIV]
        elif self == ExecutionResult.MOD:
            return [Opcode.MOD]
        elif self == ExecutionResult.SMOD:
            return [Opcode.SMOD]
        elif self == ExecutionResult.ADDMOD:
            return [Opcode.ADDMOD]
        elif self == ExecutionResult.MULMOD:
            return [Opcode.MULMOD]
        elif self == ExecutionResult.EXP:
            return [Opcode.EXP]
        elif self == ExecutionResult.SIGNEXTEND:
            return [Opcode.SIGNEXTEND]
        elif self == ExecutionResult.LT:
            return [
                Opcode.LT,
                Opcode.GT,
                Opcode.EQ,
            ]
        elif self == ExecutionResult.SLT:
            return [
                Opcode.SLT,
                Opcode.SGT,
            ]
        elif self == ExecutionResult.ISZERO:
            return [Opcode.ISZERO]
        elif self == ExecutionResult.AND:
            return [
                Opcode.AND,
                Opcode.OR,
                Opcode.XOR,
            ]
        elif self == ExecutionResult.NOT:
            return [Opcode.NOT]
        elif self == ExecutionResult.BYTE:
            return [Opcode.BYTE]
        elif self == ExecutionResult.SHL:
            return [Opcode.SHL]
        elif self == ExecutionResult.SHR:
            return [Opcode.SHR]
        elif self == ExecutionResult.SAR:
            return [Opcode.SAR]
        elif self == ExecutionResult.SHA3:
            return [Opcode.SHA3]
        elif self == ExecutionResult.ADDRESS:
            return [Opcode.ADDRESS]
        elif self == ExecutionResult.BALANCE:
            return [Opcode.BALANCE]
        elif self == ExecutionResult.ORIGIN:
            return [Opcode.ORIGIN]
        elif self == ExecutionResult.CALLER:
            return [Opcode.CALLER]
        elif self == ExecutionResult.CALLVALUE:
            return [Opcode.CALLVALUE]
        elif self == ExecutionResult.CALLDATALOAD:
            return [Opcode.CALLDATALOAD]
        elif self == ExecutionResult.CALLDATASIZE:
            return [Opcode.CALLDATASIZE]
        elif self == ExecutionResult.CALLDATACOPY:
            return [Opcode.CALLDATACOPY]
        elif self == ExecutionResult.CODESIZE:
            return [Opcode.CODESIZE]
        elif self == ExecutionResult.CODECOPY:
            return [Opcode.CODECOPY]
        elif self == ExecutionResult.GASPRICE:
            return [Opcode.GASPRICE]
        elif self == ExecutionResult.EXTCODESIZE:
            return [Opcode.EXTCODESIZE]
        elif self == ExecutionResult.EXTCODECOPY:
            return [Opcode.EXTCODECOPY]
        elif self == ExecutionResult.RETURNDATASIZE:
            return [Opcode.RETURNDATASIZE]
        elif self == ExecutionResult.RETURNDATACOPY:
            return [Opcode.RETURNDATACOPY]
        elif self == ExecutionResult.EXTCODEHASH:
            return [Opcode.EXTCODEHASH]
        elif self == ExecutionResult.BLOCKHASH:
            return [Opcode.BLOCKHASH]
        elif self == ExecutionResult.COINBASE:
            return [Opcode.COINBASE]
        elif self == ExecutionResult.TIMESTAMP:
            return [Opcode.TIMESTAMP]
        elif self == ExecutionResult.NUMBER:
            return [Opcode.NUMBER]
        elif self == ExecutionResult.DIFFICULTY:
            return [Opcode.DIFFICULTY]
        elif self == ExecutionResult.GASLIMIT:
            return [Opcode.GASLIMIT]
        elif self == ExecutionResult.CHAINID:
            return [Opcode.CHAINID]
        elif self == ExecutionResult.SELFBALANCE:
            return [Opcode.SELFBALANCE]
        elif self == ExecutionResult.BASEFEE:
            return [Opcode.BASEFEE]
        elif self == ExecutionResult.POP:
            return [Opcode.POP]
        elif self == ExecutionResult.MLOAD:
            return [
                Opcode.MLOAD,
                Opcode.MSTORE,
                Opcode.MSTORE8,
            ]
        elif self == ExecutionResult.SLOAD:
            return [Opcode.SLOAD]
        elif self == ExecutionResult.SSTORE:
            return [Opcode.SSTORE]
        elif self == ExecutionResult.JUMP:
            return [Opcode.JUMP]
        elif self == ExecutionResult.JUMPI:
            return [Opcode.JUMPI]
        elif self == ExecutionResult.PC:
            return [Opcode.PC]
        elif self == ExecutionResult.MSIZE:
            return [Opcode.MSIZE]
        elif self == ExecutionResult.GAS:
            return [Opcode.GAS]
        elif self == ExecutionResult.JUMPDEST:
            return [Opcode.JUMPDEST]
        elif self == ExecutionResult.PUSH:
            return [
                Opcode.PUSH1,
                Opcode.PUSH2,
                Opcode.PUSH3,
                Opcode.PUSH4,
                Opcode.PUSH5,
                Opcode.PUSH6,
                Opcode.PUSH7,
                Opcode.PUSH8,
                Opcode.PUSH9,
                Opcode.PUSH10,
                Opcode.PUSH11,
                Opcode.PUSH12,
                Opcode.PUSH13,
                Opcode.PUSH14,
                Opcode.PUSH15,
                Opcode.PUSH16,
                Opcode.PUSH17,
                Opcode.PUSH18,
                Opcode.PUSH19,
                Opcode.PUSH20,
                Opcode.PUSH21,
                Opcode.PUSH22,
                Opcode.PUSH23,
                Opcode.PUSH24,
                Opcode.PUSH25,
                Opcode.PUSH26,
                Opcode.PUSH27,
                Opcode.PUSH28,
                Opcode.PUSH29,
                Opcode.PUSH30,
                Opcode.PUSH31,
                Opcode.PUSH32,
            ]
        elif self == ExecutionResult.DUP:
            return [
                Opcode.DUP1,
                Opcode.DUP2,
                Opcode.DUP3,
                Opcode.DUP4,
                Opcode.DUP5,
                Opcode.DUP6,
                Opcode.DUP7,
                Opcode.DUP8,
                Opcode.DUP9,
                Opcode.DUP10,
                Opcode.DUP11,
                Opcode.DUP12,
                Opcode.DUP13,
                Opcode.DUP14,
                Opcode.DUP15,
                Opcode.DUP16,
            ]
        elif self == ExecutionResult.SWAP:
            return [
                Opcode.SWAP1,
                Opcode.SWAP2,
                Opcode.SWAP3,
                Opcode.SWAP4,
                Opcode.SWAP5,
                Opcode.SWAP6,
                Opcode.SWAP7,
                Opcode.SWAP8,
                Opcode.SWAP9,
                Opcode.SWAP10,
                Opcode.SWAP11,
                Opcode.SWAP12,
                Opcode.SWAP13,
                Opcode.SWAP14,
                Opcode.SWAP15,
                Opcode.SWAP16,
            ]
        elif self == ExecutionResult.LOG:
            return [
                Opcode.LOG0,
                Opcode.LOG1,
                Opcode.LOG2,
                Opcode.LOG3,
                Opcode.LOG4,
            ]
        elif self == ExecutionResult.CREATE:
            return [Opcode.CREATE]
        elif self == ExecutionResult.CALL:
            return [Opcode.CALL]
        elif self == ExecutionResult.CALLCODE:
            return [Opcode.CALLCODE]
        elif self == ExecutionResult.RETURN:
            return [Opcode.RETURN]
        elif self == ExecutionResult.DELEGATECALL:
            return [Opcode.DELEGATECALL]
        elif self == ExecutionResult.CREATE2:
            return [Opcode.CREATE2]
        elif self == ExecutionResult.STATICCALL:
            return [Opcode.STATICCALL]
        elif self == ExecutionResult.REVERT:
            return [Opcode.REVERT]
        elif self == ExecutionResult.SELFDESTRUCT:
            return [Opcode.SELFDESTRUCT]
        return []
