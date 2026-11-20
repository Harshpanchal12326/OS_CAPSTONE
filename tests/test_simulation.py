"""
Comprehensive Automated Test Suite for OS Resource Manager Simulator.
Validates CPU Scheduling, Memory Allocation, Disk Scheduling, and Shell Interpreter.
"""

import unittest
from core.pcb import Process, ProcessState
from core.cpu_scheduler import (
    schedule_fcfs,
    schedule_sjf,
    schedule_round_robin
)
from core.memory_manager import MemoryManager, AllocationAlgorithm
from core.disk_scheduler import (
    schedule_disk_fcfs,
    schedule_disk_sstf,
    schedule_disk_scan
)
from core.shell_interpreter import ShellInterpreter
from core.metrics import compare_cpu_algorithms, compare_disk_algorithms


class TestCPUScheduling(unittest.TestCase):
    def setUp(self):
        self.procs = [
            Process(pid=1, name="P1", burst_time=5, arrival_time=0),
            Process(pid=2, name="P2", burst_time=3, arrival_time=1),
            Process(pid=3, name="P3", burst_time=1, arrival_time=2),
            Process(pid=4, name="P4", burst_time=2, arrival_time=3),
        ]

    def test_fcfs_scheduling(self):
        res = schedule_fcfs(self.procs)
        self.assertEqual(res.total_time, 11)
        self.assertEqual(res.cpu_utilization, 100.0)
        # P1 runs 0-5, P2 runs 5-8, P3 runs 8-9, P4 runs 9-11
        p_map = {p.pid: p for p in res.processes}
        self.assertEqual(p_map[1].completion_time, 5)
        self.assertEqual(p_map[2].completion_time, 8)
        self.assertEqual(p_map[3].completion_time, 9)
        self.assertEqual(p_map[4].completion_time, 11)
        # TAT: P1=5, P2=7, P3=7, P4=8 -> Avg = 27/4 = 6.75
        self.assertAlmostEqual(res.avg_turnaround_time, 6.75, places=2)

    def test_sjf_non_preemptive(self):
        res = schedule_sjf(self.procs, preemptive=False)
        self.assertEqual(res.total_time, 11)
        # At t=0, only P1 is available -> runs 0 to 5.
        # At t=5, P2(3), P3(1), P4(2) are available -> P3 runs 5 to 6.
        # At t=6, P4(2) runs 6 to 8.
        # At t=8, P2(3) runs 8 to 11.
        p_map = {p.pid: p for p in res.processes}
        self.assertEqual(p_map[1].completion_time, 5)
        self.assertEqual(p_map[3].completion_time, 6)
        self.assertEqual(p_map[4].completion_time, 8)
        self.assertEqual(p_map[2].completion_time, 11)

    def test_sjf_preemptive_srtf(self):
        res = schedule_sjf(self.procs, preemptive=True)
        self.assertEqual(res.total_time, 11)
        # Verify all processes terminate
        for p in res.processes:
            self.assertEqual(p.state, ProcessState.TERMINATED)
            self.assertEqual(p.remaining_time, 0)
        # SRTF should have lower or equal waiting time compared to FCFS
        res_fcfs = schedule_fcfs(self.procs)
        self.assertLessEqual(res.avg_waiting_time, res_fcfs.avg_waiting_time)

    def test_round_robin(self):
        res = schedule_round_robin(self.procs, time_quantum=2)
        self.assertEqual(res.total_time, 11)
        for p in res.processes:
            self.assertEqual(p.state, ProcessState.TERMINATED)
            self.assertEqual(p.remaining_time, 0)


class TestMemoryManagement(unittest.TestCase):
    def setUp(self):
        # 1024 KB total, 128 KB OS kernel reserved, 896 KB usable
        self.mm = MemoryManager(total_memory_kb=1024, os_reserved_kb=128)

    def test_initial_state(self):
        stats = self.mm.get_stats()
        self.assertEqual(stats["total_memory_kb"], 1024)
        self.assertEqual(stats["os_reserved_kb"], 128)
        self.assertEqual(stats["total_free_kb"], 896)
        self.assertEqual(stats["largest_free_block_kb"], 896)

    def test_first_fit_allocation(self):
        addr1 = self.mm.allocate(1, "Proc1", 200, AllocationAlgorithm.FIRST_FIT)
        self.assertEqual(addr1, 128)
        addr2 = self.mm.allocate(2, "Proc2", 300, AllocationAlgorithm.FIRST_FIT)
        self.assertEqual(addr2, 328)

    def test_deallocation_and_coalescing(self):
        self.mm.allocate(1, "Proc1", 100, AllocationAlgorithm.FIRST_FIT)
        self.mm.allocate(2, "Proc2", 200, AllocationAlgorithm.FIRST_FIT)
        self.mm.allocate(3, "Proc3", 150, AllocationAlgorithm.FIRST_FIT)

        # Free Proc2 in the middle -> creates a hole of 200 KB
        self.assertTrue(self.mm.deallocate(2))
        stats = self.mm.get_stats()
        self.assertEqual(stats["num_free_holes"], 2)

        # Free Proc1 -> should coalesce with Proc2 hole (100 + 200 = 300 KB hole)
        self.assertTrue(self.mm.deallocate(1))
        # After coalescing, holes adjacent merge
        free_blocks = [s for s in self.mm.segments if not s.is_allocated]
        first_hole = free_blocks[0]
        self.assertEqual(first_hole.base_address, 128)
        self.assertEqual(first_hole.size, 300)

    def test_best_fit_vs_worst_fit(self):
        # Setup fragmented memory
        self.mm.allocate(1, "Proc1", 100, AllocationAlgorithm.FIRST_FIT) # 128..228
        self.mm.allocate(2, "Proc2", 200, AllocationAlgorithm.FIRST_FIT) # 228..428
        self.mm.allocate(3, "Proc3", 100, AllocationAlgorithm.FIRST_FIT) # 428..528
        self.mm.allocate(4, "Proc4", 400, AllocationAlgorithm.FIRST_FIT) # 528..928

        # Free Proc2 (200 KB hole) and Proc4 (400 KB hole)
        self.mm.deallocate(2)
        self.mm.deallocate(4)

        # Allocate 150 KB with Best Fit: should choose the 200 KB hole (tighter fit)
        addr_bf = self.mm.allocate(5, "Proc_Best", 150, AllocationAlgorithm.BEST_FIT)
        self.assertEqual(addr_bf, 228)

        # Reset and test Worst Fit with same layout
        mm2 = MemoryManager(total_memory_kb=1024, os_reserved_kb=128)
        mm2.allocate(1, "Proc1", 100, AllocationAlgorithm.FIRST_FIT)
        mm2.allocate(2, "Proc2", 200, AllocationAlgorithm.FIRST_FIT)
        mm2.allocate(3, "Proc3", 100, AllocationAlgorithm.FIRST_FIT)
        mm2.allocate(4, "Proc4", 400, AllocationAlgorithm.FIRST_FIT)
        mm2.deallocate(2)
        mm2.deallocate(4)

        # Allocate 150 KB with Worst Fit: should choose the 400 KB hole (leaves 250 KB)
        addr_wf = mm2.allocate(5, "Proc_Worst", 150, AllocationAlgorithm.WORST_FIT)
        self.assertEqual(addr_wf, 528)

    def test_compaction(self):
        self.mm.allocate(1, "Proc1", 100, AllocationAlgorithm.FIRST_FIT)
        self.mm.allocate(2, "Proc2", 200, AllocationAlgorithm.FIRST_FIT)
        self.mm.allocate(3, "Proc3", 100, AllocationAlgorithm.FIRST_FIT)
        self.mm.deallocate(2) # Leaves a hole between Proc1 and Proc3

        moved = self.mm.compact()
        self.assertGreaterEqual(moved, 1)
        stats = self.mm.get_stats()
        self.assertEqual(stats["num_free_holes"], 1)
        self.assertEqual(stats["external_frag_pct"], 0.0)


class TestDiskScheduling(unittest.TestCase):
    def setUp(self):
        self.requests = [98, 183, 37, 122, 14, 124, 65, 67]
        self.initial_head = 53

    def test_fcfs_disk(self):
        res = schedule_disk_fcfs(self.initial_head, self.requests)
        self.assertEqual(res.seek_sequence, [53, 98, 183, 37, 122, 14, 124, 65, 67])
        self.assertEqual(res.total_seek_operations, 640)
        self.assertEqual(res.average_seek_distance, 640 / 8)

    def test_sstf_disk(self):
        res = schedule_disk_sstf(self.initial_head, self.requests)
        self.assertEqual(res.seek_sequence, [53, 65, 67, 37, 14, 98, 122, 124, 183])
        self.assertEqual(res.total_seek_operations, 236)
        self.assertLess(res.total_seek_operations, 640)

    def test_scan_disk(self):
        res = schedule_disk_scan(self.initial_head, self.requests, total_cylinders=200, direction="high")
        self.assertIn(199, res.seek_sequence)


class TestShellInterpreter(unittest.TestCase):
    def setUp(self):
        self.mm = MemoryManager(1024, 128)
        self.procs = [
            Process(pid=1, name="Init", burst_time=5, memory_required=100)
        ]
        self.shell = ShellInterpreter(self.mm, self.procs)

    def test_commands(self):
        out_help = self.shell.execute("help")
        self.assertIn("OS RESOURCE MANAGER SHELL", out_help)

        out_ps = self.shell.execute("ps")
        self.assertIn("Init", out_ps)

        out_create = self.shell.execute("create Daemon 8 128 2 0")
        self.assertIn("Created process", out_create)
        self.assertEqual(len(self.procs), 2)

        out_pause = self.shell.execute(f"pause {self.procs[1].pid}")
        self.assertIn("paused", out_pause)

        out_resume = self.shell.execute(f"resume {self.procs[1].pid}")
        self.assertIn("resumed", out_resume)

        out_free = self.shell.execute("free")
        self.assertIn("Mem (KB)", out_free)

        out_kill = self.shell.execute(f"kill {self.procs[1].pid}")
        self.assertIn("terminated", out_kill)


if __name__ == "__main__":
    unittest.main()
