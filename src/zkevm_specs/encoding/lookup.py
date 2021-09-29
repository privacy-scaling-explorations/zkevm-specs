from typing import Tuple, Sequence, Set

class LookupTable:
    columns: Tuple[str]
    rows: Set[Tuple[int, ...]]

    def __init__(self, columns: Sequence[str]) -> None:
        self.columns = tuple(columns)
        self.rows = set()

    def __parse_row(self, **kwargs) -> Tuple[int, ...]:
        if len(kwargs.keys()) != len(self.columns):
            raise ValueError(
                f"Columns mismatch: expect {self.columns} but got {kwargs.keys()}"
            )
        return tuple(kwargs[col] for col in self.columns)

    def add_row(self, **kwargs):
        row = self.__parse_row(**kwargs)
        self.rows.add(row)

    def __len__(self):
        return len(self.rows)

    def lookup(self, **kwargs) -> bool:
        row = self.__parse_row(**kwargs)
        if row in self.rows:
            return True
        raise ValueError("Row does not exist", kwargs)
