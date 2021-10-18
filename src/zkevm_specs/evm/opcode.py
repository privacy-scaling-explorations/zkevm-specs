from enum import IntEnum
from typing import Final, Mapping, Sequence, Tuple, Union


class Opcode(IntEnum):
    STOP = int(0x00)
    ADD = int(0x01)
    MUL = int(0x02)
    SUB = int(0x03)
    DIV = int(0x04)
    SDIV = int(0x05)
    MOD = int(0x06)
    SMOD = int(0x07)
    ADDMOD = int(0x08)
    MULMOD = int(0x09)
    EXP = int(0x0a)
    SIGNEXTEND = int(0x0b)
    LT = int(0x10)
    GT = int(0x11)
    SLT = int(0x12)
    SGT = int(0x13)
    EQ = int(0x14)
    ISZERO = int(0x15)
    AND = int(0x16)
    OR = int(0x17)
    XOR = int(0x18)
    NOT = int(0x19)
    BYTE = int(0x1a)
    SHL = int(0x1b)
    SHR = int(0x1c)
    SAR = int(0x1d)
    SHA3 = int(0x20)
    ADDRESS = int(0x30)
    BALANCE = int(0x31)
    ORIGIN = int(0x32)
    CALLER = int(0x33)
    CALLVALUE = int(0x34)
    CALLDATALOAD = int(0x35)
    CALLDATASIZE = int(0x36)
    CALLDATACOPY = int(0x37)
    CODESIZE = int(0x38)
    CODECOPY = int(0x39)
    GASPRICE = int(0x3a)
    EXTCODESIZE = int(0x3b)
    EXTCODECOPY = int(0x3c)
    RETURNDATASIZE = int(0x3d)
    RETURNDATACOPY = int(0x3e)
    EXTCODEHASH = int(0x3f)
    BLOCKHASH = int(0x40)
    COINBASE = int(0x41)
    TIMESTAMP = int(0x42)
    NUMBER = int(0x43)
    DIFFICULTY = int(0x44)
    GASLIMIT = int(0x45)
    CHAINID = int(0x46)
    SELFBALANCE = int(0x47)
    BASEFEE = int(0x48)
    POP = int(0x50)
    MLOAD = int(0x51)
    MSTORE = int(0x52)
    MSTORE8 = int(0x53)
    SLOAD = int(0x54)
    SSTORE = int(0x55)
    JUMP = int(0x56)
    JUMPI = int(0x57)
    PC = int(0x58)
    MSIZE = int(0x59)
    GAS = int(0x5a)
    JUMPDEST = int(0x5b)
    PUSH1 = int(0x60)
    PUSH2 = int(0x61)
    PUSH3 = int(0x62)
    PUSH4 = int(0x63)
    PUSH5 = int(0x64)
    PUSH6 = int(0x65)
    PUSH7 = int(0x66)
    PUSH8 = int(0x67)
    PUSH9 = int(0x68)
    PUSH10 = int(0x69)
    PUSH11 = int(0x6a)
    PUSH12 = int(0x6b)
    PUSH13 = int(0x6c)
    PUSH14 = int(0x6d)
    PUSH15 = int(0x6e)
    PUSH16 = int(0x6f)
    PUSH17 = int(0x70)
    PUSH18 = int(0x71)
    PUSH19 = int(0x72)
    PUSH20 = int(0x73)
    PUSH21 = int(0x74)
    PUSH22 = int(0x75)
    PUSH23 = int(0x76)
    PUSH24 = int(0x77)
    PUSH25 = int(0x78)
    PUSH26 = int(0x79)
    PUSH27 = int(0x7a)
    PUSH28 = int(0x7b)
    PUSH29 = int(0x7c)
    PUSH30 = int(0x7d)
    PUSH31 = int(0x7e)
    PUSH32 = int(0x7f)
    DUP1 = int(0x80)
    DUP2 = int(0x81)
    DUP3 = int(0x82)
    DUP4 = int(0x83)
    DUP5 = int(0x84)
    DUP6 = int(0x85)
    DUP7 = int(0x86)
    DUP8 = int(0x87)
    DUP9 = int(0x88)
    DUP10 = int(0x89)
    DUP11 = int(0x8a)
    DUP12 = int(0x8b)
    DUP13 = int(0x8c)
    DUP14 = int(0x8d)
    DUP15 = int(0x8e)
    DUP16 = int(0x8f)
    SWAP1 = int(0x90)
    SWAP2 = int(0x91)
    SWAP3 = int(0x92)
    SWAP4 = int(0x93)
    SWAP5 = int(0x94)
    SWAP6 = int(0x95)
    SWAP7 = int(0x96)
    SWAP8 = int(0x97)
    SWAP9 = int(0x98)
    SWAP10 = int(0x99)
    SWAP11 = int(0x9a)
    SWAP12 = int(0x9b)
    SWAP13 = int(0x9c)
    SWAP14 = int(0x9d)
    SWAP15 = int(0x9e)
    SWAP16 = int(0x9f)
    LOG0 = int(0xa0)
    LOG1 = int(0xa1)
    LOG2 = int(0xa2)
    LOG3 = int(0xa3)
    LOG4 = int(0xa4)
    CREATE = int(0xf0)
    CALL = int(0xf1)
    CALLCODE = int(0xf2)
    RETURN = int(0xf3)
    DELEGATECALL = int(0xf4)
    CREATE2 = int(0xf5)
    STATICCALL = int(0xfa)
    REVERT = int(0xfd)
    SELFDESTRUCT = int(0xff)


class OpcodeInfo:
    min_stack_pointer: int
    max_stack_pointer: int
    constant_gas: int
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
        constant_gas: int,
        has_dynamic_gas: bool = False,
        pure_memory_expansion_info: Union[Tuple[int, int, int], None] = None,
    ) -> None:
        self.min_stack_pointer = min_stack_pointer
        self.max_stack_pointer = max_stack_pointer
        self.constant_gas = constant_gas
        self.has_dynamic_gas = has_dynamic_gas
        self.pure_memory_expansion_info = pure_memory_expansion_info


OPCODE_INFO_MAP: Final[Mapping[Opcode, OpcodeInfo]] = dict({
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


def valid_opcodes() -> Sequence[int]:
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


def oog_constant_pairs() -> Sequence[Tuple[int, int]]:
    pairs = []
    for opcode in valid_opcodes():
        opcode_info = OPCODE_INFO_MAP[opcode]
        if opcode_info.constant_gas > 0 and not opcode_info.has_dynamic_gas:
            for gas in range(opcode_info.constant_gas):
                pairs.append((opcode, gas))
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
