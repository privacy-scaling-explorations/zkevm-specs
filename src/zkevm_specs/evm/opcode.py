from enum import IntEnum
from typing import Final, Dict, Sequence, Tuple, Union


class Opcode(IntEnum):
    STOP = 0x00
    ADD = 0x01
    MUL = 0x02
    SUB = 0x03
    DIV = 0x04
    SDIV = 0x05
    MOD = 0x06
    SMOD = 0x07
    ADDMOD = 0x08
    MULMOD = 0x09
    EXP = 0x0a
    SIGNEXTEND = 0x0b
    LT = 0x10
    GT = 0x11
    SLT = 0x12
    SGT = 0x13
    EQ = 0x14
    ISZERO = 0x15
    AND = 0x16
    OR = 0x17
    XOR = 0x18
    NOT = 0x19
    BYTE = 0x1a
    SHL = 0x1b
    SHR = 0x1c
    SAR = 0x1d
    SHA3 = 0x20
    ADDRESS = 0x30
    BALANCE = 0x31
    ORIGIN = 0x32
    CALLER = 0x33
    CALLVALUE = 0x34
    CALLDATALOAD = 0x35
    CALLDATASIZE = 0x36
    CALLDATACOPY = 0x37
    CODESIZE = 0x38
    CODECOPY = 0x39
    GASPRICE = 0x3a
    EXTCODESIZE = 0x3b
    EXTCODECOPY = 0x3c
    RETURNDATASIZE = 0x3d
    RETURNDATACOPY = 0x3e
    EXTCODEHASH = 0x3f
    BLOCKHASH = 0x40
    COINBASE = 0x41
    TIMESTAMP = 0x42
    NUMBER = 0x43
    DIFFICULTY = 0x44
    GASLIMIT = 0x45
    CHAINID = 0x46
    SELFBALANCE = 0x47
    BASEFEE = 0x48
    POP = 0x50
    MLOAD = 0x51
    MSTORE = 0x52
    MSTORE8 = 0x53
    SLOAD = 0x54
    SSTORE = 0x55
    JUMP = 0x56
    JUMPI = 0x57
    PC = 0x58
    MSIZE = 0x59
    GAS = 0x5a
    JUMPDEST = 0x5b
    PUSH1 = 0x60
    PUSH2 = 0x61
    PUSH3 = 0x62
    PUSH4 = 0x63
    PUSH5 = 0x64
    PUSH6 = 0x65
    PUSH7 = 0x66
    PUSH8 = 0x67
    PUSH9 = 0x68
    PUSH10 = 0x69
    PUSH11 = 0x6a
    PUSH12 = 0x6b
    PUSH13 = 0x6c
    PUSH14 = 0x6d
    PUSH15 = 0x6e
    PUSH16 = 0x6f
    PUSH17 = 0x70
    PUSH18 = 0x71
    PUSH19 = 0x72
    PUSH20 = 0x73
    PUSH21 = 0x74
    PUSH22 = 0x75
    PUSH23 = 0x76
    PUSH24 = 0x77
    PUSH25 = 0x78
    PUSH26 = 0x79
    PUSH27 = 0x7a
    PUSH28 = 0x7b
    PUSH29 = 0x7c
    PUSH30 = 0x7d
    PUSH31 = 0x7e
    PUSH32 = 0x7f
    DUP1 = 0x80
    DUP2 = 0x81
    DUP3 = 0x82
    DUP4 = 0x83
    DUP5 = 0x84
    DUP6 = 0x85
    DUP7 = 0x86
    DUP8 = 0x87
    DUP9 = 0x88
    DUP10 = 0x89
    DUP11 = 0x8a
    DUP12 = 0x8b
    DUP13 = 0x8c
    DUP14 = 0x8d
    DUP15 = 0x8e
    DUP16 = 0x8f
    SWAP1 = 0x90
    SWAP2 = 0x91
    SWAP3 = 0x92
    SWAP4 = 0x93
    SWAP5 = 0x94
    SWAP6 = 0x95
    SWAP7 = 0x96
    SWAP8 = 0x97
    SWAP9 = 0x98
    SWAP10 = 0x99
    SWAP11 = 0x9a
    SWAP12 = 0x9b
    SWAP13 = 0x9c
    SWAP14 = 0x9d
    SWAP15 = 0x9e
    SWAP16 = 0x9f
    LOG0 = 0xa0
    LOG1 = 0xa1
    LOG2 = 0xa2
    LOG3 = 0xa3
    LOG4 = 0xa4
    CREATE = 0xf0
    CALL = 0xf1
    CALLCODE = 0xf2
    RETURN = 0xf3
    DELEGATECALL = 0xf4
    CREATE2 = 0xf5
    STATICCALL = 0xfa
    REVERT = 0xfd
    SELFDESTRUCT = 0xff

    def hex(self) -> str:
        return '{:02x}'.format(self)

    def constant_gas_cost(self) -> int:
        return OPCODE_INFO_MAP[self].constant_gas_cost

    def has_dynamic_gas(self) -> bool:
        return OPCODE_INFO_MAP[self].has_dynamic_gas


class OpcodeInfo:
    """
    Opcode information.
    """

    min_stack_pointer: int
    max_stack_pointer: int
    constant_gas_cost: int
    has_dynamic_gas: bool
    pure_memory_expansion_info: Tuple[
        int,  # offset stack_pointer_offset
        int,  # length stack_pointer_offset
        int,  # constant length
    ]

    def __init__(
        self,
        min_stack_pointer: int,
        max_stack_pointer: int,
        constant_gas_cost: int,
        has_dynamic_gas: bool = False,
        pure_memory_expansion_info: Union[Tuple[int, int, int], None] = None,
    ) -> None:
        self.min_stack_pointer = min_stack_pointer
        self.max_stack_pointer = max_stack_pointer
        self.constant_gas_cost = constant_gas_cost
        self.has_dynamic_gas = has_dynamic_gas
        self.pure_memory_expansion_info = pure_memory_expansion_info


OPCODE_INFO_MAP: Final[Dict[Opcode, OpcodeInfo]] = dict({
    Opcode.STOP: OpcodeInfo(0, 1024, 0),
    Opcode.ADD: OpcodeInfo(-1, 1022, 3),
    Opcode.MUL: OpcodeInfo(-1, 1022, 5),
    Opcode.SUB: OpcodeInfo(-1, 1022, 3),
    Opcode.DIV: OpcodeInfo(-1, 1022, 5),
    Opcode.SDIV: OpcodeInfo(-1, 1022, 5),
    Opcode.MOD: OpcodeInfo(-1, 1022, 5),
    Opcode.SMOD: OpcodeInfo(-1, 1022, 5),
    Opcode.ADDMOD: OpcodeInfo(-2, 1021, 8),
    Opcode.MULMOD: OpcodeInfo(-2, 1021, 8),
    Opcode.EXP: OpcodeInfo(-1, 1022, 0, True),
    Opcode.SIGNEXTEND: OpcodeInfo(-1, 1022, 5),
    Opcode.LT: OpcodeInfo(-1, 1022, 3),
    Opcode.GT: OpcodeInfo(-1, 1022, 3),
    Opcode.SLT: OpcodeInfo(-1, 1022, 3),
    Opcode.SGT: OpcodeInfo(-1, 1022, 3),
    Opcode.EQ: OpcodeInfo(-1, 1022, 3),
    Opcode.ISZERO: OpcodeInfo(0, 1023, 3),
    Opcode.AND: OpcodeInfo(-1, 1022, 3),
    Opcode.OR: OpcodeInfo(-1, 1022, 3),
    Opcode.XOR: OpcodeInfo(-1, 1022, 3),
    Opcode.NOT: OpcodeInfo(0, 1023, 3),
    Opcode.BYTE: OpcodeInfo(-1, 1022, 3),
    Opcode.SHL: OpcodeInfo(-1, 1022, 3),
    Opcode.SHR: OpcodeInfo(-1, 1022, 3),
    Opcode.SAR: OpcodeInfo(-1, 1022, 3),
    Opcode.SHA3: OpcodeInfo(-1, 1022, 30, True),
    Opcode.ADDRESS: OpcodeInfo(1, 1024, 2),
    Opcode.BALANCE: OpcodeInfo(0, 1023, 100, True),
    Opcode.ORIGIN: OpcodeInfo(1, 1024, 2),
    Opcode.CALLER: OpcodeInfo(1, 1024, 2),
    Opcode.CALLVALUE: OpcodeInfo(1, 1024, 2),
    Opcode.CALLDATALOAD: OpcodeInfo(0, 1023, 3),
    Opcode.CALLDATASIZE: OpcodeInfo(1, 1024, 2),
    Opcode.CALLDATACOPY: OpcodeInfo(-3, 1021, 3, True),
    Opcode.CODESIZE: OpcodeInfo(1, 1024, 2),
    Opcode.CODECOPY: OpcodeInfo(-3, 1021, 3, True),
    Opcode.GASPRICE: OpcodeInfo(1, 1024, 2),
    Opcode.EXTCODESIZE: OpcodeInfo(0, 1023, 100, True),
    Opcode.EXTCODECOPY: OpcodeInfo(-4, 1020, 100, True),
    Opcode.RETURNDATASIZE: OpcodeInfo(1, 1024, 2),
    Opcode.RETURNDATACOPY: OpcodeInfo(-3, 1021, 3, True),
    Opcode.EXTCODEHASH: OpcodeInfo(0, 1023, 100, True),
    Opcode.BLOCKHASH: OpcodeInfo(0, 1023, 20),
    Opcode.COINBASE: OpcodeInfo(1, 1024, 2),
    Opcode.TIMESTAMP: OpcodeInfo(1, 1024, 2),
    Opcode.NUMBER: OpcodeInfo(1, 1024, 2),
    Opcode.DIFFICULTY: OpcodeInfo(1, 1024, 2),
    Opcode.GASLIMIT: OpcodeInfo(1, 1024, 2),
    Opcode.CHAINID: OpcodeInfo(1, 1024, 2),
    Opcode.SELFBALANCE: OpcodeInfo(1, 1024, 5),
    Opcode.BASEFEE: OpcodeInfo(1, 1024, 2),
    Opcode.POP: OpcodeInfo(-1, 1023, 2),
    Opcode.MLOAD: OpcodeInfo(0, 1023, 3, True, (0, 0, 32)),
    Opcode.MSTORE: OpcodeInfo(-2, 1022, 3, True, (0, 0, 32)),
    Opcode.MSTORE8: OpcodeInfo(-2, 1022, 3, True, (0, 0, 1)),
    Opcode.SLOAD: OpcodeInfo(0, 1023, 0, True),
    Opcode.SSTORE: OpcodeInfo(-2, 1022, 0, True),
    Opcode.JUMP: OpcodeInfo(-1, 1023, 8),
    Opcode.JUMPI: OpcodeInfo(-2, 1022, 10),
    Opcode.PC: OpcodeInfo(1, 1024, 2),
    Opcode.MSIZE: OpcodeInfo(1, 1024, 2),
    Opcode.GAS: OpcodeInfo(1, 1024, 2),
    Opcode.JUMPDEST: OpcodeInfo(0, 1024, 1),
    Opcode.PUSH1: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH2: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH3: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH4: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH5: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH6: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH7: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH8: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH9: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH10: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH11: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH12: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH13: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH14: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH15: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH16: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH17: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH18: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH19: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH20: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH21: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH22: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH23: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH24: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH25: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH26: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH27: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH28: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH29: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH30: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH31: OpcodeInfo(1, 1024, 3),
    Opcode.PUSH32: OpcodeInfo(1, 1024, 3),
    Opcode.DUP1: OpcodeInfo(1, 1023, 3),
    Opcode.DUP2: OpcodeInfo(1, 1022, 3),
    Opcode.DUP3: OpcodeInfo(1, 1021, 3),
    Opcode.DUP4: OpcodeInfo(1, 1020, 3),
    Opcode.DUP5: OpcodeInfo(1, 1019, 3),
    Opcode.DUP6: OpcodeInfo(1, 1018, 3),
    Opcode.DUP7: OpcodeInfo(1, 1017, 3),
    Opcode.DUP8: OpcodeInfo(1, 1016, 3),
    Opcode.DUP9: OpcodeInfo(1, 1015, 3),
    Opcode.DUP10: OpcodeInfo(1, 1014, 3),
    Opcode.DUP11: OpcodeInfo(1, 1013, 3),
    Opcode.DUP12: OpcodeInfo(1, 1012, 3),
    Opcode.DUP13: OpcodeInfo(1, 1011, 3),
    Opcode.DUP14: OpcodeInfo(1, 1010, 3),
    Opcode.DUP15: OpcodeInfo(1, 1009, 3),
    Opcode.DUP16: OpcodeInfo(1, 1008, 3),
    Opcode.SWAP1: OpcodeInfo(0, 1022, 3),
    Opcode.SWAP2: OpcodeInfo(0, 1021, 3),
    Opcode.SWAP3: OpcodeInfo(0, 1020, 3),
    Opcode.SWAP4: OpcodeInfo(0, 1019, 3),
    Opcode.SWAP5: OpcodeInfo(0, 1018, 3),
    Opcode.SWAP6: OpcodeInfo(0, 1017, 3),
    Opcode.SWAP7: OpcodeInfo(0, 1016, 3),
    Opcode.SWAP8: OpcodeInfo(0, 1015, 3),
    Opcode.SWAP9: OpcodeInfo(0, 1014, 3),
    Opcode.SWAP10: OpcodeInfo(0, 1013, 3),
    Opcode.SWAP11: OpcodeInfo(0, 1012, 3),
    Opcode.SWAP12: OpcodeInfo(0, 1011, 3),
    Opcode.SWAP13: OpcodeInfo(0, 1010, 3),
    Opcode.SWAP14: OpcodeInfo(0, 1009, 3),
    Opcode.SWAP15: OpcodeInfo(0, 1008, 3),
    Opcode.SWAP16: OpcodeInfo(0, 1007, 3),
    Opcode.LOG0: OpcodeInfo(-2, 1022, 0, True),
    Opcode.LOG1: OpcodeInfo(-3, 1021, 0, True),
    Opcode.LOG2: OpcodeInfo(-4, 1020, 0, True),
    Opcode.LOG3: OpcodeInfo(-5, 1019, 0, True),
    Opcode.LOG4: OpcodeInfo(-6, 1018, 0, True),
    Opcode.CREATE: OpcodeInfo(-2, 1021, 32000, True, (1, 2, 0)),
    Opcode.CALL: OpcodeInfo(-6, 1017, 100, True),
    Opcode.CALLCODE: OpcodeInfo(-6, 1017, 100, True),
    Opcode.RETURN: OpcodeInfo(-2, 1022, 0, True, (0, 1, 0)),
    Opcode.DELEGATECALL: OpcodeInfo(-5, 1018, 100, True),
    Opcode.CREATE2: OpcodeInfo(-3, 1020, 32000, True),
    Opcode.STATICCALL: OpcodeInfo(-5, 1018, 100, True),
    Opcode.REVERT: OpcodeInfo(-2, 1022, 0, True, (0, 1, 0)),
    Opcode.SELFDESTRUCT: OpcodeInfo(-1, 1023, 5000, True),
})


def valid_opcodes() -> Sequence[Opcode]:
    return list(Opcode)


def invalid_opcodes() -> Sequence[int]:
    return [opcode for opcode in range(256) if opcode not in OPCODE_INFO_MAP]


def stack_overflow_pairs() -> Sequence[Tuple[int, int]]:
    pairs = []
    for opcode in valid_opcodes():
        opcode_info = OPCODE_INFO_MAP[opcode]
        if opcode_info.min_stack_pointer > 0:
            for stack_pointer in range(opcode_info.min_stack_pointer):
                pairs.append((opcode, stack_pointer))
    return pairs


def stack_underflow_pairs() -> Sequence[Tuple[int, int]]:
    pairs = []
    for opcode in valid_opcodes():
        opcode_info = OPCODE_INFO_MAP[opcode]
        if opcode_info.max_stack_pointer < 1024:
            for stack_pointer in range(opcode_info.max_stack_pointer, 1024):
                pairs.append((opcode, stack_pointer + 1))
    return pairs


def opcode_constant_gas_cost_pairs() -> Sequence[Tuple[int, int]]:
    pairs = []
    for opcode in valid_opcodes():
        if not opcode.has_dynamic_gas() and opcode.constant_gas_cost() > 0:
            pairs.append((opcode, opcode.constant_gas_cost()))
    return pairs


def state_write_opcodes() -> Sequence[int]:
    return [
        Opcode.SSTORE, Opcode.LOG0, Opcode.LOG1, Opcode.LOG2, Opcode.LOG3, Opcode.LOG4,
        Opcode.CREATE, Opcode.CALL, Opcode.CREATE2, Opcode.SELFDESTRUCT,
    ]


def call_opcodes() -> Sequence[int]:
    return [Opcode.CALL, Opcode.CALLCODE, Opcode.DELEGATECALL, Opcode.STATICCALL]


def ether_transfer_opcdes() -> Sequence[int]:
    return [Opcode.CALL, Opcode.CALLCODE]


def create_opcodes() -> Sequence[int]:
    return [Opcode.CREATE, Opcode.CREATE2]


def jump_opcodes() -> Sequence[int]:
    return [Opcode.JUMP, Opcode.JUMPI]
