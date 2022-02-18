# Maximun number of bytes with composition value that doesn't wrap around the field
MAX_N_BYTES = 31
# Number of bytes of account address
N_BYTES_ACCOUNT_ADDRESS = 20
# Number of bytes of memory address
N_BYTES_MEMORY_ADDRESS = 5
# Number of bytes of memory size (in word)
N_BYTES_MEMORY_SIZE = 4
# Number of bytes of gas
N_BYTES_GAS = 8
# Number of bytes of program counter
N_BYTES_PROGRAM_COUNTER = 8
# Number of bytes of u64
N_BYTES_U64 = 8
# Number of bytes of an EVM word (u256)
N_BYTES_WORD = 32

# Gas cost of free step
GAS_COST_ZERO = 0
# Gas cost of JUMPSTEP
GAS_COST_ONE = 1
# Gas cost of quick step
GAS_COST_QUICK = 2
# Gas cost of fastest step
GAS_COST_FASTEST = 3
# Gas cost of fast step
GAS_COST_FAST = 5
# Gas cost of mid step
GAS_COST_MID = 8
# Gas cost of slow step
GAS_COST_SLOW = 10
# Gas cost of ext step
GAS_COST_EXT = 20
# Gas cost of SHA3
GAS_COST_SHA3 = 30
# Gas cost of CREATE
GAS_COST_CREATE = 32000
# Gas cost of CREATE2
GAS_COST_CREATE2 = 32000
# Gas cost of SELFDESTRUCT, EIP 150
GAS_COST_SELF_DESTRUCT = 5000
# Gas cost of copying every word
GAS_COST_COPY = 3
# Gas cost of non-creation transaction
GAS_COST_TX = 21000
# Gas cost of creation transaction
GAS_COST_CREATION_TX = 53000
# Gas cost of transaction call_data per non-zero byte
GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE = 16
# Gas cost of transaction call_data per zero byte
GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE = 4
# Gas cost of accessing account or storage slot, EIP 2929
GAS_COST_WARM_ACCESS = 100
# Extra gas cost of not-yet-accessed account
EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS = 2500
# Extra gas cost of not-yet-accessed storage slot
EXTRA_GAS_COST_STORAGE_SLOT_COLD_ACCESS = 2000
# Gas cost of calling with non-zero value
GAS_COST_CALL_WITH_VALUE = 9000
# Gas cost of calling empty account
GAS_COST_CALL_EMPTY_ACCOUNT = 25000
# Gas stipend given if call with non-zero value
GAS_STIPEND_CALL_WITH_VALUE = 2300

# Quotient for max refund of gas used
MAX_REFUND_QUOTIENT_OF_GAS_USED = 5
# Denominator of quadratic part of memory expansion gas cost
MEMORY_EXPANSION_QUAD_DENOMINATOR = 512
# Coefficient of linear part of memory expansion gas cost
MEMORY_EXPANSION_LINEAR_COEFF = 3
