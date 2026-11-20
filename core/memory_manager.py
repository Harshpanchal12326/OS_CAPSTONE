"""
Memory Management Unit (MMU) Simulator.
Supports Contiguous Dynamic Partition Allocation: First Fit, Best Fit, Worst Fit.
Features Block Coalescing, Compaction (Defragmentation), and Fragmentation Tracking.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


class AllocationAlgorithm(Enum):
    FIRST_FIT = "First Fit"
    BEST_FIT = "Best Fit"
    WORST_FIT = "Worst Fit"


@dataclass
class MemorySegment:
    base_address: int
    size: int
    is_allocated: bool
    pid: Optional[int] = None
    process_name: Optional[str] = None

    @property
    def end_address(self) -> int:
        return self.base_address + self.size

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Base Address": f"0x{self.base_address:04X} ({self.base_address} KB)",
            "End Address": f"0x{self.end_address:04X} ({self.end_address} KB)",
            "Size (KB)": self.size,
            "Status": "Allocated" if self.is_allocated else "Free",
            "PID": self.pid if self.is_allocated else "-",
            "Process": self.process_name if self.is_allocated else "Free Block"
        }


class MemoryManager:
    """
    Simulates contiguous dynamic partition memory management.
    """
    def __init__(self, total_memory_kb: int = 1024, os_reserved_kb: int = 128):
        self.total_memory: int = max(256, total_memory_kb)
        self.os_reserved: int = min(self.total_memory // 2, max(0, os_reserved_kb))
        self.segments: List[MemorySegment] = []
        self.history: List[Dict[str, Any]] = []
        self.reset()

    def reset(self):
        """Reset memory to initial state: OS kernel partition + single large free block."""
        self.segments = []
        if self.os_reserved > 0:
            self.segments.append(
                MemorySegment(
                    base_address=0,
                    size=self.os_reserved,
                    is_allocated=True,
                    pid=0,
                    process_name="OS Kernel"
                )
            )
        free_size = self.total_memory - self.os_reserved
        if free_size > 0:
            self.segments.append(
                MemorySegment(
                    base_address=self.os_reserved,
                    size=free_size,
                    is_allocated=False,
                    pid=None,
                    process_name=None
                )
            )
        self.history = [{
            "action": "INIT",
            "message": f"Initialized memory: Total {self.total_memory} KB (OS Kernel: {self.os_reserved} KB, Usable: {free_size} KB)",
            "success": True
        }]

    def coalesce(self):
        """
        Merge adjacent free memory segments to minimize external fragmentation.
        Fundamental OS concept: when a block is freed, merge with left and right neighbors if free.
        """
        if not self.segments:
            return

        merged: List[MemorySegment] = []
        for seg in self.segments:
            if merged and (not merged[-1].is_allocated) and (not seg.is_allocated):
                # Merge into the previous free segment
                merged[-1].size += seg.size
            else:
                merged.append(seg)
        self.segments = merged

    def allocate(
        self,
        pid: int,
        process_name: str,
        size_kb: int,
        algorithm: AllocationAlgorithm = AllocationAlgorithm.FIRST_FIT
    ) -> Optional[int]:
        """
        Allocate memory of `size_kb` for process `pid` using the chosen algorithm.
        Returns base address if successful, or None if allocation failed (insufficient contiguous memory).
        """
        if size_kb <= 0:
            return None

        # Check if process is already allocated
        for seg in self.segments:
            if seg.is_allocated and seg.pid == pid and pid != 0:
                self.history.append({
                    "action": "ALLOC_FAIL",
                    "pid": pid,
                    "name": process_name,
                    "size": size_kb,
                    "algorithm": algorithm.value,
                    "message": f"Process {process_name} (PID {pid}) already has memory allocated.",
                    "success": False
                })
                return None

        # Find eligible free segments
        eligible_indices = [
            i for i, seg in enumerate(self.segments)
            if not seg.is_allocated and seg.size >= size_kb
        ]

        if not eligible_indices:
            total_free = sum(s.size for s in self.segments if not s.is_allocated)
            self.history.append({
                "action": "ALLOC_FAIL",
                "pid": pid,
                "name": process_name,
                "size": size_kb,
                "algorithm": algorithm.value,
                "message": f"Out of memory! Requested {size_kb} KB, largest free block is {max([s.size for s in self.segments if not s.is_allocated], default=0)} KB (Total free: {total_free} KB). External fragmentation detected.",
                "success": False
            })
            return None

        # Select target segment index according to allocation algorithm
        chosen_idx = None
        if algorithm == AllocationAlgorithm.FIRST_FIT:
            # First segment with size >= size_kb
            chosen_idx = eligible_indices[0]

        elif algorithm == AllocationAlgorithm.BEST_FIT:
            # Segment with minimum size >= size_kb (tightest fit)
            chosen_idx = min(eligible_indices, key=lambda i: self.segments[i].size)

        elif algorithm == AllocationAlgorithm.WORST_FIT:
            # Segment with maximum size >= size_kb (leaves largest hole)
            chosen_idx = max(eligible_indices, key=lambda i: self.segments[i].size)

        target_seg = self.segments[chosen_idx]
        allocated_addr = target_seg.base_address

        if target_seg.size == size_kb:
            # Exact match, simply mark as allocated
            target_seg.is_allocated = True
            target_seg.pid = pid
            target_seg.process_name = process_name
        else:
            # Split segment: allocated block + remaining free block
            remaining_size = target_seg.size - size_kb
            new_allocated = MemorySegment(
                base_address=allocated_addr,
                size=size_kb,
                is_allocated=True,
                pid=pid,
                process_name=process_name
            )
            new_free = MemorySegment(
                base_address=allocated_addr + size_kb,
                size=remaining_size,
                is_allocated=False,
                pid=None,
                process_name=None
            )
            self.segments[chosen_idx] = new_allocated
            self.segments.insert(chosen_idx + 1, new_free)

        self.history.append({
            "action": "ALLOC_SUCCESS",
            "pid": pid,
            "name": process_name,
            "size": size_kb,
            "base_address": allocated_addr,
            "algorithm": algorithm.value,
            "message": f"Allocated {size_kb} KB at 0x{allocated_addr:04X} for {process_name} (PID {pid}) using {algorithm.value}.",
            "success": True
        })
        return allocated_addr

    def deallocate(self, pid: int) -> bool:
        """
        Deallocate/free memory occupied by process `pid` and coalesce adjacent free blocks.
        """
        found = False
        freed_size = 0
        freed_addr = 0
        name = ""

        for seg in self.segments:
            if seg.is_allocated and seg.pid == pid and pid != 0:
                seg.is_allocated = False
                freed_size = seg.size
                freed_addr = seg.base_address
                name = seg.process_name
                seg.pid = None
                seg.process_name = None
                found = True
                break

        if found:
            self.coalesce()
            self.history.append({
                "action": "DEALLOC_SUCCESS",
                "pid": pid,
                "name": name,
                "size": freed_size,
                "base_address": freed_addr,
                "message": f"Deallocated {freed_size} KB at 0x{freed_addr:04X} for {name} (PID {pid}). Free blocks coalesced.",
                "success": True
            })
            return True
        else:
            self.history.append({
                "action": "DEALLOC_FAIL",
                "pid": pid,
                "message": f"Process PID {pid} has no allocated memory to release.",
                "success": False
            })
            return False

    def compact(self) -> int:
        """
        Simulate Memory Compaction (Defragmentation).
        Shifts all allocated blocks towards address 0 (right after OS kernel),
        coalescing all free space into one large contiguous block at the end.
        Returns the number of processes moved.
        """
        allocated_blocks = [s for s in self.segments if s.is_allocated and s.pid != 0]
        os_block = [s for s in self.segments if s.is_allocated and s.pid == 0]

        total_allocated_size = sum(s.size for s in allocated_blocks) + sum(s.size for s in os_block)
        total_free_size = self.total_memory - total_allocated_size

        new_segments: List[MemorySegment] = []
        current_addr = 0

        # Place OS kernel first
        for s in os_block:
            new_segments.append(
                MemorySegment(
                    base_address=current_addr,
                    size=s.size,
                    is_allocated=True,
                    pid=0,
                    process_name=s.process_name
                )
            )
            current_addr += s.size

        # Place user processes contiguously
        moved_count = 0
        for s in allocated_blocks:
            if s.base_address != current_addr:
                moved_count += 1
            new_segments.append(
                MemorySegment(
                    base_address=current_addr,
                    size=s.size,
                    is_allocated=True,
                    pid=s.pid,
                    process_name=s.process_name
                )
            )
            current_addr += s.size

        # Place consolidated free block
        if total_free_size > 0:
            new_segments.append(
                MemorySegment(
                    base_address=current_addr,
                    size=total_free_size,
                    is_allocated=False,
                    pid=None,
                    process_name=None
                )
            )

        self.segments = new_segments
        self.history.append({
            "action": "COMPACTION",
            "message": f"Memory compaction complete: {moved_count} blocks relocated. Single consolidated free block created: {total_free_size} KB at 0x{current_addr:04X}.",
            "success": True
        })
        return moved_count

    def get_stats(self) -> Dict[str, Any]:
        """Compute memory statistics: utilization, free, allocated, holes, external fragmentation."""
        allocated_segs = [s for s in self.segments if s.is_allocated]
        free_segs = [s for s in self.segments if not s.is_allocated]

        total_allocated = sum(s.size for s in allocated_segs)
        user_allocated = sum(s.size for s in allocated_segs if s.pid != 0)
        total_free = sum(s.size for s in free_segs)
        largest_free = max([s.size for s in free_segs], default=0)
        num_free_holes = len(free_segs)

        # External fragmentation: total free space that is unusable if a single block needs > largest_free
        # As an index: 1 - (largest_free / total_free) if total_free > 0 else 0
        ext_frag_index = round((1.0 - (largest_free / total_free)) * 100, 2) if total_free > 0 else 0.0
        utilization = round((total_allocated / self.total_memory) * 100, 2)

        return {
            "total_memory_kb": self.total_memory,
            "os_reserved_kb": self.os_reserved,
            "user_allocated_kb": user_allocated,
            "total_allocated_kb": total_allocated,
            "total_free_kb": total_free,
            "largest_free_block_kb": largest_free,
            "num_free_holes": num_free_holes,
            "num_allocated_blocks": len(allocated_segs),
            "external_frag_pct": ext_frag_index,
            "utilization_pct": utilization
        }
