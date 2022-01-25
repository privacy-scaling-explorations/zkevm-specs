from typing import NewType, Tuple

U64 = NewType("U64", int)
U160 = NewType("U160", int)
U256 = NewType("U256", int)


Array3 = NewType("Array3", Tuple[int, int, int])
Array4 = NewType("Array4", Tuple[int, int, int, int])
Array8 = NewType("Array8", Tuple[int, int, int, int, int, int, int, int])
Array10 = NewType("Array10", Tuple[int, int, int, int, int, int, int, int, int, int])
Array32 = NewType(
    "Array32",
    Tuple[
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
    ],
)
