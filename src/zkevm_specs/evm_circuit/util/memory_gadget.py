from ...util import N_BYTES_MEMORY_ADDRESS, FQ, Expression
from ..instruction import Instruction


class BufferReaderGadget:
    def __init__(
        self, inst: Instruction, max_bytes: int, addr_start: FQ, addr_end: FQ, bytes_left: FQ
    ):
        self.instruction = inst
        self.selectors = inst.continuous_selectors(bytes_left, max_bytes)
        # Here we are just generating witness data, no need to use inst here
        self.bound_dist = [FQ(max(0, addr_end.n - addr_start.n - i)) for i in range(max_bytes)]
        self.bound_dist_is_zero = [inst.is_zero(bound_dist) for bound_dist in self.bound_dist]

        # constraint on bound_dist[0]
        inst.constrain_equal(
            self.bound_dist[0], addr_end - inst.min(addr_end, addr_start, N_BYTES_MEMORY_ADDRESS)
        )
        # constraints on bound_dist[1:]
        for i in range(1, max_bytes):
            diff = self.bound_dist[i - 1] - self.bound_dist[i]
            # diff == 0 if bound_dist[i - 1] == 0; otherwise 1
            inst.constrain_equal(
                diff, inst.select(self.bound_dist_is_zero[i - 1], FQ.zero(), FQ.one())
            )

    def constrain_byte(self, idx: int, byte: Expression):
        # bytes[idx] == 0 when selectors[idx] == 0
        self.instruction.constrain_zero(byte * (1 - self.selectors[idx]))
        # bytes[idx] == 0 when bound_dist[idx] == 0
        self.instruction.constrain_zero(byte * self.bound_dist_is_zero[idx])

    def num_bytes(self) -> FQ:
        return FQ(sum(self.selectors))

    def has_data(self, idx: int) -> FQ:
        return self.selectors[idx]

    def read_flag(self, idx: int) -> FQ:
        return self.selectors[idx] * (1 - self.bound_dist_is_zero[idx])
