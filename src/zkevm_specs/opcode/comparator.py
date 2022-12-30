from ..encoding import FIELD_SIZE, LookupTable


class SignTable(LookupTable):
    """
    x: 18 bits signed ( -(2**17 - 1) to 2**17 - 1)
    sign: 2 bits (0, -1, 1)
    (1 column and 2**18 - 1 rows)
    """

    def __init__(self):
        super().__init__(["x", "sign"])
        self.add_row(x=0, sign=0)
        for x in range(1, 2**17):
            self.add_row(x=x, sign=1)
            self.add_row(x=-x + FIELD_SIZE, sign=-1)
