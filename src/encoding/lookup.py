from typing import Tuple, Sequence, Set


class LookupTable:
    columns: Tuple[str]
    rows: Set[int]
    random: int

    def __init__(self, columns: Sequence[str], random: int = 5566) -> None:
        self.columns = set(columns)
        self.rows = set()
        self.random = random

    def __compress(self, **kwargs):
        assert set(kwargs.keys()) == self.columns
        return sum(kwargs[col] * self.random ** i for i, col in enumerate(self.columns))

    def add_row(self, **kwargs):
        self.rows.add(self.__compress(**kwargs))

    def __len__(self):
        return len(self.rows)

    def lookup(self, **kwargs) -> bool:
        if self.__compress(**kwargs) in self.rows:
            return True
        raise ValueError("Row does not exist", kwargs)
