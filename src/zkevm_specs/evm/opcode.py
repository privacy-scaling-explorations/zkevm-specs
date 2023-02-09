from enum import IntEnum
from typing import Final, Dict, Tuple, List

from ..util import FQ
from ..util.param import *


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
    EXP = 0x0A
    SIGNEXTEND = 0x0B
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
    BYTE = 0x1A
    SHL = 0x1B
    SHR = 0x1C
    SAR = 0x1D
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
    GASPRICE = 0x3A
    EXTCODESIZE = 0x3B
    EXTCODECOPY = 0x3C
    RETURNDATASIZE = 0x3D
    RETURNDATACOPY = 0x3E
    EXTCODEHASH = 0x3F
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
    GAS = 0x5A
    JUMPDEST = 0x5B
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
    PUSH11 = 0x6A
    PUSH12 = 0x6B
    PUSH13 = 0x6C
    PUSH14 = 0x6D
    PUSH15 = 0x6E
    PUSH16 = 0x6F
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
    PUSH27 = 0x7A
    PUSH28 = 0x7B
    PUSH29 = 0x7C
    PUSH30 = 0x7D
    PUSH31 = 0x7E
    PUSH32 = 0x7F
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
    DUP11 = 0x8A
    DUP12 = 0x8B
    DUP13 = 0x8C
    DUP14 = 0x8D
    DUP15 = 0x8E
    DUP16 = 0x8F
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
    SWAP11 = 0x9A
    SWAP12 = 0x9B
    SWAP13 = 0x9C
    SWAP14 = 0x9D
    SWAP15 = 0x9E
    SWAP16 = 0x9F
    LOG0 = 0xA0
    LOG1 = 0xA1
    LOG2 = 0xA2
    LOG3 = 0xA3
    LOG4 = 0xA4
    CREATE = 0xF0
    CALL = 0xF1
    CALLCODE = 0xF2
    RETURN = 0xF3
    DELEGATECALL = 0xF4
    CREATE2 = 0xF5
    STATICCALL = 0xFA
    REVERT = 0xFD
    SELFDESTRUCT = 0xFF

    def expr(self) -> FQ:
        return FQ(self)

    def hex(self) -> str:
        return "{:02x}".format(self)

    def bytes(self) -> bytes:
        return bytes([self])

    def is_push(self) -> bool:
        return Opcode.PUSH1 <= self <= Opcode.PUSH32

    def is_dup(self) -> bool:
        return Opcode.DUP1 <= self <= Opcode.DUP16

    def is_swap(self) -> bool:
        return Opcode.SWAP1 <= self <= Opcode.SWAP16

    def max_stack_pointer(self) -> int:
        return OPCODE_INFO_MAP[self].max_stack_pointer

    def min_stack_pointer(self) -> int:
        return OPCODE_INFO_MAP[self].min_stack_pointer

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

    def __init__(
        self,
        min_stack_pointer: int,
        max_stack_pointer: int,
        constant_gas_cost: int,
        has_dynamic_gas: bool = False,
    ) -> None:
        self.min_stack_pointer = min_stack_pointer
        self.max_stack_pointer = max_stack_pointer
        self.constant_gas_cost = constant_gas_cost
        self.has_dynamic_gas = has_dynamic_gas


OPCODE_INFO_MAP: Final[Dict[Opcode, OpcodeInfo]] = dict(
    {
        Opcode.STOP: OpcodeInfo(0, 1024, GAS_COST_ZERO),
        Opcode.ADD: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.MUL: OpcodeInfo(-1, 1022, GAS_COST_FAST),
        Opcode.SUB: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.DIV: OpcodeInfo(-1, 1022, GAS_COST_FAST),
        Opcode.SDIV: OpcodeInfo(-1, 1022, GAS_COST_FAST),
        Opcode.MOD: OpcodeInfo(-1, 1022, GAS_COST_FAST),
        Opcode.SMOD: OpcodeInfo(-1, 1022, GAS_COST_FAST),
        Opcode.ADDMOD: OpcodeInfo(-2, 1021, GAS_COST_MID),
        Opcode.MULMOD: OpcodeInfo(-2, 1021, GAS_COST_MID),
        Opcode.EXP: OpcodeInfo(-1, 1022, GAS_COST_ZERO, True),
        Opcode.SIGNEXTEND: OpcodeInfo(-1, 1022, GAS_COST_FAST),
        Opcode.LT: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.GT: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.SLT: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.SGT: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.EQ: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.ISZERO: OpcodeInfo(0, 1023, GAS_COST_FASTEST),
        Opcode.AND: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.OR: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.XOR: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.NOT: OpcodeInfo(0, 1023, GAS_COST_FASTEST),
        Opcode.BYTE: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.SHL: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.SHR: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.SAR: OpcodeInfo(-1, 1022, GAS_COST_FASTEST),
        Opcode.SHA3: OpcodeInfo(-1, 1022, GAS_COST_SHA3, True),
        Opcode.ADDRESS: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.BALANCE: OpcodeInfo(0, 1023, GAS_COST_WARM_ACCESS, True),
        Opcode.ORIGIN: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.CALLER: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.CALLVALUE: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.CALLDATALOAD: OpcodeInfo(0, 1023, GAS_COST_FASTEST),
        Opcode.CALLDATASIZE: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.CALLDATACOPY: OpcodeInfo(-3, 1021, GAS_COST_FASTEST, True),
        Opcode.CODESIZE: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.CODECOPY: OpcodeInfo(-3, 1021, GAS_COST_FASTEST, True),
        Opcode.GASPRICE: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.EXTCODESIZE: OpcodeInfo(0, 1023, GAS_COST_WARM_ACCESS, True),
        Opcode.EXTCODECOPY: OpcodeInfo(-4, 1020, GAS_COST_WARM_ACCESS, True),
        Opcode.RETURNDATASIZE: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.RETURNDATACOPY: OpcodeInfo(-3, 1021, GAS_COST_FASTEST, True),
        Opcode.EXTCODEHASH: OpcodeInfo(0, 1023, GAS_COST_WARM_ACCESS, True),
        Opcode.BLOCKHASH: OpcodeInfo(0, 1023, GAS_COST_EXT),
        Opcode.COINBASE: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.TIMESTAMP: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.NUMBER: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.DIFFICULTY: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.GASLIMIT: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.CHAINID: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.SELFBALANCE: OpcodeInfo(1, 1024, GAS_COST_FAST),
        Opcode.BASEFEE: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.POP: OpcodeInfo(-1, 1023, GAS_COST_QUICK),
        Opcode.MLOAD: OpcodeInfo(0, 1023, GAS_COST_FASTEST, True),
        Opcode.MSTORE: OpcodeInfo(-2, 1022, GAS_COST_FASTEST, True),
        Opcode.MSTORE8: OpcodeInfo(-2, 1022, GAS_COST_FASTEST, True),
        Opcode.SLOAD: OpcodeInfo(0, 1023, GAS_COST_ZERO, True),
        Opcode.SSTORE: OpcodeInfo(-2, 1022, GAS_COST_ZERO, True),
        Opcode.JUMP: OpcodeInfo(-1, 1023, GAS_COST_MID),
        Opcode.JUMPI: OpcodeInfo(-2, 1022, GAS_COST_SLOW),
        Opcode.PC: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.MSIZE: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.GAS: OpcodeInfo(1, 1024, GAS_COST_QUICK),
        Opcode.JUMPDEST: OpcodeInfo(0, 1024, GAS_COST_ONE),
        Opcode.PUSH1: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH2: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH3: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH4: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH5: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH6: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH7: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH8: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH9: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH10: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH11: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH12: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH13: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH14: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH15: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH16: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH17: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH18: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH19: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH20: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH21: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH22: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH23: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH24: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH25: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH26: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH27: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH28: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH29: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH30: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH31: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.PUSH32: OpcodeInfo(1, 1024, GAS_COST_FASTEST),
        Opcode.DUP1: OpcodeInfo(1, 1023, GAS_COST_FASTEST),
        Opcode.DUP2: OpcodeInfo(1, 1022, GAS_COST_FASTEST),
        Opcode.DUP3: OpcodeInfo(1, 1021, GAS_COST_FASTEST),
        Opcode.DUP4: OpcodeInfo(1, 1020, GAS_COST_FASTEST),
        Opcode.DUP5: OpcodeInfo(1, 1019, GAS_COST_FASTEST),
        Opcode.DUP6: OpcodeInfo(1, 1018, GAS_COST_FASTEST),
        Opcode.DUP7: OpcodeInfo(1, 1017, GAS_COST_FASTEST),
        Opcode.DUP8: OpcodeInfo(1, 1016, GAS_COST_FASTEST),
        Opcode.DUP9: OpcodeInfo(1, 1015, GAS_COST_FASTEST),
        Opcode.DUP10: OpcodeInfo(1, 1014, GAS_COST_FASTEST),
        Opcode.DUP11: OpcodeInfo(1, 1013, GAS_COST_FASTEST),
        Opcode.DUP12: OpcodeInfo(1, 1012, GAS_COST_FASTEST),
        Opcode.DUP13: OpcodeInfo(1, 1011, GAS_COST_FASTEST),
        Opcode.DUP14: OpcodeInfo(1, 1010, GAS_COST_FASTEST),
        Opcode.DUP15: OpcodeInfo(1, 1009, GAS_COST_FASTEST),
        Opcode.DUP16: OpcodeInfo(1, 1008, GAS_COST_FASTEST),
        Opcode.SWAP1: OpcodeInfo(0, 1022, GAS_COST_FASTEST),
        Opcode.SWAP2: OpcodeInfo(0, 1021, GAS_COST_FASTEST),
        Opcode.SWAP3: OpcodeInfo(0, 1020, GAS_COST_FASTEST),
        Opcode.SWAP4: OpcodeInfo(0, 1019, GAS_COST_FASTEST),
        Opcode.SWAP5: OpcodeInfo(0, 1018, GAS_COST_FASTEST),
        Opcode.SWAP6: OpcodeInfo(0, 1017, GAS_COST_FASTEST),
        Opcode.SWAP7: OpcodeInfo(0, 1016, GAS_COST_FASTEST),
        Opcode.SWAP8: OpcodeInfo(0, 1015, GAS_COST_FASTEST),
        Opcode.SWAP9: OpcodeInfo(0, 1014, GAS_COST_FASTEST),
        Opcode.SWAP10: OpcodeInfo(0, 1013, GAS_COST_FASTEST),
        Opcode.SWAP11: OpcodeInfo(0, 1012, GAS_COST_FASTEST),
        Opcode.SWAP12: OpcodeInfo(0, 1011, GAS_COST_FASTEST),
        Opcode.SWAP13: OpcodeInfo(0, 1010, GAS_COST_FASTEST),
        Opcode.SWAP14: OpcodeInfo(0, 1009, GAS_COST_FASTEST),
        Opcode.SWAP15: OpcodeInfo(0, 1008, GAS_COST_FASTEST),
        Opcode.SWAP16: OpcodeInfo(0, 1007, GAS_COST_FASTEST),
        Opcode.LOG0: OpcodeInfo(-2, 1022, GAS_COST_ZERO, True),
        Opcode.LOG1: OpcodeInfo(-3, 1021, GAS_COST_ZERO, True),
        Opcode.LOG2: OpcodeInfo(-4, 1020, GAS_COST_ZERO, True),
        Opcode.LOG3: OpcodeInfo(-5, 1019, GAS_COST_ZERO, True),
        Opcode.LOG4: OpcodeInfo(-6, 1018, GAS_COST_ZERO, True),
        Opcode.CREATE: OpcodeInfo(-2, 1021, GAS_COST_CREATE, True),
        Opcode.CALL: OpcodeInfo(-6, 1017, GAS_COST_WARM_ACCESS, True),
        Opcode.CALLCODE: OpcodeInfo(-6, 1017, GAS_COST_WARM_ACCESS, True),
        Opcode.RETURN: OpcodeInfo(-2, 1022, GAS_COST_ZERO, True),
        Opcode.DELEGATECALL: OpcodeInfo(-5, 1018, GAS_COST_WARM_ACCESS, True),
        Opcode.CREATE2: OpcodeInfo(-3, 1020, GAS_COST_CREATE2, True),
        Opcode.STATICCALL: OpcodeInfo(-5, 1018, GAS_COST_WARM_ACCESS, True),
        Opcode.REVERT: OpcodeInfo(-2, 1022, GAS_COST_ZERO, True),
        Opcode.SELFDESTRUCT: OpcodeInfo(-1, 1023, GAS_COST_SELF_DESTRUCT, True),
    }
)


def valid_opcodes() -> List[Opcode]:
    return list(Opcode)


def invalid_opcodes() -> List[int]:
    return [opcode for opcode in range(256) if opcode not in valid_opcodes()]


def stack_overflow_pairs() -> List[Tuple[Opcode, int]]:
    pairs = []
    for opcode in valid_opcodes():
        if opcode.min_stack_pointer() > 0:
            for stack_pointer in range(opcode.min_stack_pointer()):
                pairs.append((opcode, stack_pointer))
    return pairs


def stack_underflow_pairs() -> List[Tuple[Opcode, int]]:
    pairs = []
    for opcode in valid_opcodes():
        if opcode.max_stack_pointer() < 1024:
            for stack_pointer in range(opcode.max_stack_pointer(), 1024):
                pairs.append((opcode, stack_pointer + 1))
    return pairs


def constant_gas_cost_pairs() -> List[Tuple[Opcode, int]]:
    pairs = []
    for opcode in valid_opcodes():
        if not opcode.has_dynamic_gas() and opcode.constant_gas_cost() > 0:
            pairs.append((opcode, opcode.constant_gas_cost()))
    return pairs


def state_write_opcodes() -> List[Opcode]:
    return [
        Opcode.SSTORE,
        Opcode.LOG0,
        Opcode.LOG1,
        Opcode.LOG2,
        Opcode.LOG3,
        Opcode.LOG4,
        Opcode.CREATE,
        Opcode.CALL,
        Opcode.CREATE2,
        Opcode.SELFDESTRUCT,
    ]


def call_opcodes() -> List[Opcode]:
    return [Opcode.CALL, Opcode.CALLCODE, Opcode.DELEGATECALL, Opcode.STATICCALL]


def ether_transfer_opcdes() -> List[Opcode]:
    return [Opcode.CALL, Opcode.CALLCODE]


def create_opcodes() -> List[Opcode]:
    return [Opcode.CREATE, Opcode.CREATE2]


def jump_opcodes() -> List[Opcode]:
    return [Opcode.JUMP, Opcode.JUMPI]


# Checks if the passed in byte is a PUSH op
def is_push(op) -> bool:
    return op in range(Opcode.PUSH1, Opcode.PUSH32 + 1)


# Returns how many bytes the opcode pushes
def get_push_size(op) -> int:
    return op - Opcode.PUSH1 + 1 if is_push(op) else 0
