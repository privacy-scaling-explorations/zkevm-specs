from enum import IntEnum, auto


class ExecutionResult(IntEnum):
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
    LT = auto()  # LT, GT
    SLT = auto()  # SLT, SGT
    EQ = auto()
    ISZERO = auto()
    AND = auto()
    OR = auto()
    XOR = auto()
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
    MLOAD = auto()
    MSTORE = auto()
    MSTORE8 = auto()
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
