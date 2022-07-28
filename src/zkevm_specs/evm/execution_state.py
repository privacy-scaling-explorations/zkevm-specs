from enum import IntEnum, auto
from typing import Sequence, Tuple, Union

from ..util import FQ
from .opcode import (
    Opcode,
    invalid_opcodes,
    stack_overflow_pairs,
    stack_underflow_pairs,
    state_write_opcodes,
)


class ExecutionState(IntEnum):
    """
    All possible execution results an EVM step could encounter.
    """

    BeginTx = auto()
    EndTx = auto()
    EndBlock = auto()
    CopyToMemory = auto()
    CopyToLog = auto()
    CopyCodeToMemory = auto()

    # Opcode's successful cases
    STOP = auto()
    ADD = auto()  # ADD, SUB
    MUL = auto()  # MUL, DIV, MOD
    SDIV = auto()
    SMOD = auto()
    ADDMOD = auto()
    MULMOD = auto()
    EXP = auto()
    SIGNEXTEND = auto()
    CMP = auto()  # LT, GT, EQ
    SCMP = auto()  # SLT, SGT
    ISZERO = auto()
    BITWISE = auto()  # AND, OR, XOR
    NOT = auto()
    BYTE = auto()
    SHL_SHR = auto()
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
    BlockCtx = auto()
    SELFBALANCE = auto()
    POP = auto()
    MEMORY = auto()  # MLOAD, MSTORE, MSTORE8
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
    LOG = auto()  # LOG0, LOG1, LOG2, LOG3, LOG4
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
    ErrorInvalidOpcode = auto()
    # For opcodes which triggers stackoverflow by doing push more than pop,
    # or stackunderflow by doing pop and DUP, SWAP which peek deeper element directly
    ErrorStack = auto()
    # For SSTORE, LOG0, LOG1, LOG2, LOG3, LOG4, CREATE, CALL, CREATE2, SELFDESTRUCT
    ErrorWriteProtection = auto()
    # For CALL, CALLCODE, DELEGATECALL, STATICCALL
    ErrorDepth = auto()
    # For CALL, CALLCODE
    ErrorInsufficientBalance = auto()
    # For CREATE, CREATE2
    ErrorContractAddressCollision = auto()
    ErrorInvalidCreationCode = auto()
    # For opcode RETURN which needs to store code when it's is creation
    ErrorMaxCodeSizeExceeded = auto()
    # For JUMP, JUMPI
    ErrorInvalidJump = auto()
    # For RETURNDATACOPY
    ErrorReturnDataOutOfBound = auto()
    # For opcodes which have non-zero constant gas cost
    ErrorOutOfGasConstant = auto()
    # For opcodes MLOAD, MSTORE, MSTORE8, which have static size memory expansion gas cost
    ErrorOutOfGasStaticMemoryExpansion = auto()
    # For opcodes CREATE, RETURN, REVERT, which have dynamic size memory expansion gas cost
    ErrorOutOfGasDynamicMemoryExpansion = auto()
    # For opcode CALLDATACOPY, CODECOPY, RETURNDATACOPY, which copies a specified chunk of memory
    ErrorOutOfGasMemoryCopy = auto()
    # For opcodes BALANCE, EXTCODESIZE, EXTCODEHASH, which possibly touches an extra account
    ErrorOutOfGasAccountAccess = auto()
    # For opcode RETURN which has code storing gas cost when it's is creation
    ErrorOutOfGasCodeStore = auto()
    # For opcodes LOG0, LOG1, LOG2, LOG3, LOG4
    ErrorOutOfGasLOG = auto()
    # For opcodes which have their own gas calculation
    ErrorOutOfGasEXP = auto()
    ErrorOutOfGasSHA3 = auto()
    ErrorOutOfGasEXTCODECOPY = auto()
    ErrorOutOfGasSLOAD = auto()
    ErrorOutOfGasSSTORE = auto()
    ErrorOutOfGasCALL = auto()
    ErrorOutOfGasCALLCODE = auto()
    ErrorOutOfGasDELEGATECALL = auto()
    ErrorOutOfGasCREATE2 = auto()
    ErrorOutOfGasSTATICCALL = auto()
    ErrorOutOfGasSELFDESTRUCT = auto()

    # TODO: Precompile success and error cases

    def expr(self) -> FQ:
        return FQ(self)

    def responsible_opcode(self) -> Union[Sequence[int], Sequence[Tuple[int, int]]]:
        if self == ExecutionState.STOP:
            return [Opcode.STOP]
        elif self == ExecutionState.ADD:
            return [
                Opcode.ADD,
                Opcode.SUB,
            ]
        elif self == ExecutionState.MUL:
            return [Opcode.MUL, Opcode.DIV, Opcode.MOD]
        elif self == ExecutionState.SDIV:
            return [Opcode.SDIV]
        elif self == ExecutionState.SMOD:
            return [Opcode.SMOD]
        elif self == ExecutionState.ADDMOD:
            return [Opcode.ADDMOD]
        elif self == ExecutionState.MULMOD:
            return [Opcode.MULMOD]
        elif self == ExecutionState.EXP:
            return [Opcode.EXP]
        elif self == ExecutionState.SIGNEXTEND:
            return [Opcode.SIGNEXTEND]
        elif self == ExecutionState.CMP:
            return [
                Opcode.LT,
                Opcode.GT,
                Opcode.EQ,
            ]
        elif self == ExecutionState.SCMP:
            return [
                Opcode.SLT,
                Opcode.SGT,
            ]
        elif self == ExecutionState.ISZERO:
            return [Opcode.ISZERO]
        elif self == ExecutionState.BITWISE:
            return [
                Opcode.AND,
                Opcode.OR,
                Opcode.XOR,
            ]
        elif self == ExecutionState.NOT:
            return [Opcode.NOT]
        elif self == ExecutionState.BYTE:
            return [Opcode.BYTE]
        elif self == ExecutionState.SHL_SHR:
            return [Opcode.SHL, Opcode.SHR]
        elif self == ExecutionState.SAR:
            return [Opcode.SAR]
        elif self == ExecutionState.SHA3:
            return [Opcode.SHA3]
        elif self == ExecutionState.ADDRESS:
            return [Opcode.ADDRESS]
        elif self == ExecutionState.BALANCE:
            return [Opcode.BALANCE]
        elif self == ExecutionState.ORIGIN:
            return [Opcode.ORIGIN]
        elif self == ExecutionState.CALLER:
            return [Opcode.CALLER]
        elif self == ExecutionState.CALLVALUE:
            return [Opcode.CALLVALUE]
        elif self == ExecutionState.CALLDATALOAD:
            return [Opcode.CALLDATALOAD]
        elif self == ExecutionState.CALLDATASIZE:
            return [Opcode.CALLDATASIZE]
        elif self == ExecutionState.CALLDATACOPY:
            return [Opcode.CALLDATACOPY]
        elif self == ExecutionState.CODESIZE:
            return [Opcode.CODESIZE]
        elif self == ExecutionState.CODECOPY:
            return [Opcode.CODECOPY]
        elif self == ExecutionState.GASPRICE:
            return [Opcode.GASPRICE]
        elif self == ExecutionState.EXTCODESIZE:
            return [Opcode.EXTCODESIZE]
        elif self == ExecutionState.EXTCODECOPY:
            return [Opcode.EXTCODECOPY]
        elif self == ExecutionState.RETURNDATASIZE:
            return [Opcode.RETURNDATASIZE]
        elif self == ExecutionState.RETURNDATACOPY:
            return [Opcode.RETURNDATACOPY]
        elif self == ExecutionState.EXTCODEHASH:
            return [Opcode.EXTCODEHASH]
        elif self == ExecutionState.BLOCKHASH:
            return [Opcode.BLOCKHASH]
        elif self == ExecutionState.BlockCtx:
            return [
                Opcode.COINBASE,
                Opcode.TIMESTAMP,
                Opcode.NUMBER,
                Opcode.DIFFICULTY,
                Opcode.GASLIMIT,
                Opcode.BASEFEE,
                Opcode.CHAINID,
            ]
        elif self == ExecutionState.SELFBALANCE:
            return [Opcode.SELFBALANCE]
        elif self == ExecutionState.POP:
            return [Opcode.POP]
        elif self == ExecutionState.MEMORY:
            return [
                Opcode.MLOAD,
                Opcode.MSTORE,
                Opcode.MSTORE8,
            ]
        elif self == ExecutionState.SLOAD:
            return [Opcode.SLOAD]
        elif self == ExecutionState.SSTORE:
            return [Opcode.SSTORE]
        elif self == ExecutionState.JUMP:
            return [Opcode.JUMP]
        elif self == ExecutionState.JUMPI:
            return [Opcode.JUMPI]
        elif self == ExecutionState.PC:
            return [Opcode.PC]
        elif self == ExecutionState.MSIZE:
            return [Opcode.MSIZE]
        elif self == ExecutionState.GAS:
            return [Opcode.GAS]
        elif self == ExecutionState.JUMPDEST:
            return [Opcode.JUMPDEST]
        elif self == ExecutionState.PUSH:
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
        elif self == ExecutionState.DUP:
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
        elif self == ExecutionState.SWAP:
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
        elif self == ExecutionState.LOG:
            return [
                Opcode.LOG0,
                Opcode.LOG1,
                Opcode.LOG2,
                Opcode.LOG3,
                Opcode.LOG4,
            ]
        elif self == ExecutionState.CREATE:
            return [Opcode.CREATE]
        elif self == ExecutionState.CALL:
            return [Opcode.CALL]
        elif self == ExecutionState.CALLCODE:
            return [Opcode.CALLCODE]
        elif self == ExecutionState.RETURN:
            return [Opcode.RETURN]
        elif self == ExecutionState.DELEGATECALL:
            return [Opcode.DELEGATECALL]
        elif self == ExecutionState.CREATE2:
            return [Opcode.CREATE2]
        elif self == ExecutionState.STATICCALL:
            return [Opcode.STATICCALL]
        elif self == ExecutionState.REVERT:
            return [Opcode.REVERT]
        elif self == ExecutionState.SELFDESTRUCT:
            return [Opcode.SELFDESTRUCT]
        elif self == ExecutionState.ErrorInvalidOpcode:
            return invalid_opcodes()
        elif self == ExecutionState.ErrorStack:
            return stack_overflow_pairs() + stack_underflow_pairs()
        elif self == ExecutionState.ErrorWriteProtection:
            return state_write_opcodes()
        return []

    def halts(self) -> bool:
        return self.halts_in_success() or self.halts_in_exception() or self == ExecutionState.REVERT

    def halts_in_success(self) -> bool:
        return self in [
            ExecutionState.STOP,
            ExecutionState.RETURN,
            ExecutionState.SELFDESTRUCT,
        ]

    def halts_in_exception(self) -> bool:
        return self in [
            ExecutionState.ErrorInvalidOpcode,
            ExecutionState.ErrorStack,
            ExecutionState.ErrorWriteProtection,
            ExecutionState.ErrorDepth,
            ExecutionState.ErrorInsufficientBalance,
            ExecutionState.ErrorContractAddressCollision,
            ExecutionState.ErrorInvalidCreationCode,
            ExecutionState.ErrorMaxCodeSizeExceeded,
            ExecutionState.ErrorInvalidJump,
            ExecutionState.ErrorReturnDataOutOfBound,
            ExecutionState.ErrorOutOfGasConstant,
            ExecutionState.ErrorOutOfGasStaticMemoryExpansion,
            ExecutionState.ErrorOutOfGasDynamicMemoryExpansion,
            ExecutionState.ErrorOutOfGasMemoryCopy,
            ExecutionState.ErrorOutOfGasAccountAccess,
            ExecutionState.ErrorOutOfGasCodeStore,
            ExecutionState.ErrorOutOfGasLOG,
            ExecutionState.ErrorOutOfGasEXP,
            ExecutionState.ErrorOutOfGasSHA3,
            ExecutionState.ErrorOutOfGasEXTCODECOPY,
            ExecutionState.ErrorOutOfGasSLOAD,
            ExecutionState.ErrorOutOfGasSSTORE,
            ExecutionState.ErrorOutOfGasCALL,
            ExecutionState.ErrorOutOfGasCALLCODE,
            ExecutionState.ErrorOutOfGasDELEGATECALL,
            ExecutionState.ErrorOutOfGasCREATE2,
            ExecutionState.ErrorOutOfGasSTATICCALL,
            ExecutionState.ErrorOutOfGasSELFDESTRUCT,
        ]
