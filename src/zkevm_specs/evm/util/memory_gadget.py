from ...util import N_BYTES_MEMORY_ADDRESS, FQ
from ..instruction import Instruction, Transition


class MemoryExpansionGadget:
    pass


class BufferReaderGadget:
    def __init__(self, inst: Instruction, max_bytes: int, addr_start: FQ, addr_end: FQ, bytes_left: FQ):
        self.instruction = inst
        self.selectors = inst.continuous_selectors(bytes_left, max_bytes)
        # Here we are just generating witness data, no need to use `inst.max`
        self.bound_dist = [FQ(max(0, addr_end.n - addr_start.n - i)) for i in range(max_bytes)]
        self.bound_dist_is_zero = [inst.is_zero(bound_dist) for bound_dist in self.bound_dist]

        # constraint on bound_dist[0]
        lt, eq = inst.compare(addr_start, addr_end, N_BYTES_MEMORY_ADDRESS)
        # bound_dist[0] + addr_start == addr_end when addr_start < addr_end
        inst.constrain_zero(lt * (self.bound_dist[0] + addr_start - addr_end))
        # bound_dist[0] == 0 if addr_start >= addr_end
        inst.constrain_zero((1 - lt) * self.bound_dist[0])

        # constraints on bound_dist[1:]
        for i in range(1, max_bytes):
            diff = self.bound_dist[i - 1] - self.bound_dist[i]
            # diff == 1 if bound_dist[i - 1] != 0
            inst.constrain_zero((1 - self.bound_dist_is_zero[i - 1]) * (1 - diff))
            # diff == 0 if bound_dist[i - 1] == 0
            inst.constrain_zero(self.bound_dist_is_zero[i - 1] * diff)

    def constrain_byte(self, idx: int, byte: FQ):
        # bytes[idx] == 0 when selectors[idx] == 0
        self.instruction.constrain_zero(byte * (1 - self.selectors[idx]))
        # bytes[idx] == 0 when bound_dist[idx] == 0
        self.instruction.constrain_zero(byte * self.bound_dist_is_zero[idx])

    def num_bytes(self) -> FQ:
        return FQ(sum(self.selectors))

    def has_data(self, idx: int) -> bool:
        return self.selectors[idx]

    def read_flag(self, idx: int) -> bool:
        return self.selectors[idx] and not self.bound_dist_is_zero[idx]
