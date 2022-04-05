from typing import NewType


U256 = NewType("U256", int)
U128 = NewType("U128", int)
U64 = NewType("U64", int)
U32 = NewType("U32", int)
U16 = NewType("U16", int)
U8 = NewType("U8", int)
# must be one of -1, 0, 1
Sign = NewType("Sign", int)
