from typing import NewType, Tuple

Array3 = NewType("Array3", Tuple[int, int, int])
Array4 = NewType("Array4", Tuple[int, int, int, int])
Array8 = NewType("Array8", Tuple[int, int, int, int, int, int, int, int])
Array32 = NewType("Array32", Tuple[
    int, int, int, int, int, int, int, int,
    int, int, int, int, int, int, int, int,
    int, int, int, int, int, int, int, int,
    int, int, int, int, int, int, int, int,
])
