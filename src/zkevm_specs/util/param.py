# Maximum integer value of u64
MAX_U64 = 2**64 - 1

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
# Number of bytes of stack pointer(1024)
N_BYTES_STACK = 2


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
# Gas cost (dynamic) per exponent byte-size
GAS_COST_EXP_PER_BYTE = 50
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
# Gas cost of copying every word, specifically in the case of SHA3 opcode
GAS_COST_COPY_SHA3 = 6
# Gas cost of non-creation transaction
GAS_COST_TX = 21000
# Constant gas cost of LOG
GAS_COST_LOG = 375
# Gas cost of per byte in a LOG* operation's data.
GAS_COST_LOGDATA = 8
# Gas cost of creation transaction
GAS_COST_CREATION_TX = 53000
# Gas cost of transaction call_data per non-zero byte
GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE = 16
# Gas cost of transaction call_data per zero byte
GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE = 4
# Gas cost of accessing account or storage slot, EIP 2929
GAS_COST_WARM_ACCESS = 100
# Gas cost of accessing not-yet-accessed account
GAS_COST_ACCOUNT_COLD_ACCESS = 2600
# Extra gas cost of accessing not-yet-accessed account
EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS = GAS_COST_ACCOUNT_COLD_ACCESS - GAS_COST_WARM_ACCESS
# Gas cost of calling with non-zero value
GAS_COST_CALL_WITH_VALUE = 9000
# Gas cost of turning empty account into non-empty account
GAS_COST_NEW_ACCOUNT = 25000
# Gas stipend given if call with non-zero value
GAS_STIPEND_CALL_WITH_VALUE = 2300
# Gas cost of warming up an account with the access list
GAS_COST_ACCESS_LIST_ADDRESS = 2400
# Gas cost of warming up a storage with the access list
GAS_COST_ACCESS_LIST_STORAGE = 1900


# Quotient for max refund of gas used
MAX_REFUND_QUOTIENT_OF_GAS_USED = 5
# Denominator of quadratic part of memory expansion gas cost
MEMORY_EXPANSION_QUAD_DENOMINATOR = 512
# Coefficient of linear part of memory expansion gas cost
MEMORY_EXPANSION_LINEAR_COEFF = 3

# Maximum number of bytes copied during one single iteration of CopyToMemory, i.e. the internal state used by the
# CALLDATACOPY gadget
MAX_N_BYTES_COPY_TO_MEMORY = 32
# Maximum number of bytes copied during one single iteration of CopyCodeToMemory, i.e. the internal state used by
# the CODECOPY gadget
MAX_N_BYTES_COPY_CODE_TO_MEMORY = 32

COLD_SLOAD_COST = 2100
WARM_STORAGE_READ_COST = 100
SLOAD_GAS = 100
SSTORE_SET_GAS = 20000
SSTORE_RESET_GAS = 2900
SSTORE_CLEARS_SCHEDULE = 4800

# The max number of bytes that can be copied in a step limited by the number
# of cells in a step
MAX_COPY_BYTES = 32

# Maximum depth of call/create stack
CALL_CREATE_DEPTH = 1024

# PublicInputs circuit parameters
PUBLIC_INPUTS_BLOCK_LEN = 7 + 256  # Length of block public data
PUBLIC_INPUTS_EXTRA_LEN = 3  # Length of fields that don't belong to any table
PUBLIC_INPUTS_TX_LEN = 10  # Length of tx public data (without calldata)


# Precompiled contract gas prices

# Elliptic curve sender recovery gas price
EcrecoverGas = 3000
# Base price for a SHA256 operation
Sha256BaseGas = 60
# Per-word price for a SHA256 operation
Sha256PerWordGas = 12
# Base price for a RIPEMD160 operation
Ripemd160BaseGas = 600
# Per-word price for a RIPEMD160 operation
Ripemd160PerWordGas = 120
# Base price for a data copy operation
IdentityBaseGas = 15
# Per-work price for a data copy operation
IdentityPerWordGas = 3

# Gas needed for an elliptic curve addition
Bn256AddGas = 150
# Gas needed for an elliptic curve scalar multiplication
Bn256ScalarMulGas = 6000
# Base price for an elliptic curve pairing check
Bn256PairingBaseGas = 45000
# Per-point price for an elliptic curve pairing check
Bn256PairingPerPointGas = 34000

BigModExpBaseGas = 0
Blake2fBaseGas = 0
