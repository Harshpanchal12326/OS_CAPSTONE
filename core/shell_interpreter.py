"""
Simulated Bash / Unix Shell Command Interpreter for OS Resource Manager.
Enables process creation, process termination, pausing, memory inspection,
disk queries, and system information via a command-line interface.
"""

from typing import List, Dict, Any, Tuple, Optional
import platform
import sys
import datetime
from core.pcb import Process, ProcessState
from core.memory_manager import MemoryManager, AllocationAlgorithm
from core.cpu_scheduler import schedule_fcfs, schedule_sjf, schedule_round_robin
from core.disk_scheduler import schedule_disk_fcfs, schedule_disk_sstf


class ShellInterpreter:
    """
    Simulates a Bash / Unix command-line shell environment connected
    to the OS Resource Manager's CPU, Memory, and Disk kernels.
    """
    def __init__(self, memory_manager: MemoryManager, process_list: List[Process]):
        self.memory_manager = memory_manager
        self.process_list = process_list
        self.disk_requests: List[int] = [98, 183, 37, 122, 14, 124, 65, 67]
        self.disk_head: int = 53
        self.history: List[str] = []

    def execute(self, cmd_line: str) -> str:
        """Executes a bash-like command and returns the shell output."""
        trimmed = cmd_line.strip()
        if not trimmed:
            return ""

        self.history.append(trimmed)
        tokens = trimmed.split()
        cmd = tokens[0].lower()
        args = tokens[1:]

        try:
            if cmd in ["help", "man"]:
                return self._cmd_help()
            elif cmd in ["ps", "pstree"]:
                return self._cmd_ps(args)
            elif cmd in ["top", "htop"]:
                return self._cmd_top()
            elif cmd in ["create", "fork", "spawn"]:
                return self._cmd_create(args)
            elif cmd in ["kill", "terminate"]:
                return self._cmd_kill(args)
            elif cmd == "pause":
                return self._cmd_pause(args)
            elif cmd == "resume":
                return self._cmd_resume(args)
            elif cmd in ["free", "vmstat"]:
                return self._cmd_free(args)
            elif cmd in ["df", "disk", "iostat"]:
                return self._cmd_disk(args)
            elif cmd in ["sched", "schedule"]:
                return self._cmd_sched(args)
            elif cmd == "compact":
                return self._cmd_compact()
            elif cmd in ["sysinfo", "uname", "neofetch"]:
                return self._cmd_sysinfo(args)
            elif cmd == "history":
                return "\n".join(f"{i+1:3d}  {h}" for i, h in enumerate(self.history))
            elif cmd in ["clear", "cls"]:
                return "__CLEAR__"
            elif cmd == "echo":
                return " ".join(args)
            elif cmd in ["date", "uptime"]:
                return datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
            else:
                return f"bash: {cmd}: command not found. Type 'help' for available OS commands."
        except Exception as e:
            return f"bash: error executing '{cmd}': {str(e)}"

    def _cmd_help(self) -> str:
        return """
===================== OS RESOURCE MANAGER SHELL (BASH) =====================
Available Commands:
  ps [-a]                        : List active processes and PCB states
  top                            : Interactive system resource summary
  create <name> <bt> <mem> [pri] : Spawn a new process (Name, Burst, Memory KB, Priority)
  kill <pid>                     : Terminate a process and release allocated memory
  pause <pid>                    : Pause process (transition READY/RUNNING -> WAITING)
  resume <pid>                   : Resume process (transition WAITING -> READY)
  free [-m|-k]                   : Display memory statistics & fragmentation
  df                             : Display disk track requests and arm status
  sched <fcfs|sjf|rr> [q]        : Run CPU scheduler algorithm (RR optional quantum)
  compact                        : Trigger memory compaction / defragmentation
  sysinfo / uname -a             : Display host and kernel environment information
  history                        : List command execution history
  clear                          : Clear terminal screen
=============================================================================
"""

    def _cmd_ps(self, args: List[str]) -> str:
        lines = [f"{'PID':<6} {'NAME':<12} {'STATE':<12} {'BURST':<7} {'REMAIN':<8} {'MEM(KB)':<9} {'PRIORITY':<8}"]
        lines.append("-" * 65)
        for p in self.process_list:
            lines.append(f"{p.pid:<6} {p.name:<12} {p.state.value:<12} {p.burst_time:<7} {p.remaining_time:<8} {p.memory_required:<9} {p.priority:<8}")
        return "\n".join(lines)

    def _cmd_top(self) -> str:
        active = [p for p in self.process_list if p.state != ProcessState.TERMINATED]
        paused = [p for p in self.process_list if p.state == ProcessState.WAITING]
        terminated = [p for p in self.process_list if p.state == ProcessState.TERMINATED]
        m = self.memory_manager.get_stats()

        header = f"""top - {datetime.datetime.now().strftime('%H:%M:%S')} up 1 session, 1 user
Tasks: {len(self.process_list)} total, {len(active)} active, {len(paused)} sleeping/paused, {len(terminated)} stopped
Mem  : {m['total_memory_kb']}k total, {m['total_allocated_kb']}k used, {m['total_free_kb']}k free ({m['utilization_pct']}% utilized)
Frag : {m['external_frag_pct']}% external fragmentation, largest contiguous hole: {m['largest_free_block_kb']}k
"""
        lines = [header, f"{'PID':<6} {'USER':<8} {'PR':<4} {'VIRT':<8} {'STAT':<6} {'COMMAND':<12}"]
        lines.append("-" * 55)
        for p in self.process_list:
            lines.append(f"{p.pid:<6} {'root':<8} {p.priority:<4} {f'{p.memory_required}k':<8} {p.state.value[:4]:<6} {p.name:<12}")
        return "\n".join(lines)

    def _cmd_create(self, args: List[str]) -> str:
        if len(args) < 3:
            return "Usage: create <name> <burst_time> <memory_kb> [priority] [arrival_time]"
        name = args[0]
        try:
            burst = int(args[1])
            mem = int(args[2])
            pri = int(args[3]) if len(args) > 3 else 1
            arr = int(args[4]) if len(args) > 4 else 0
        except ValueError:
            return "bash: create: burst_time, memory_kb, priority, arrival_time must be integers."

        # Assign unique PID
        existing_pids = [p.pid for p in self.process_list]
        pid = max(existing_pids, default=0) + 1

        new_proc = Process(
            pid=pid,
            name=name,
            burst_time=burst,
            arrival_time=arr,
            memory_required=mem,
            priority=pri
        )
        new_proc.state = ProcessState.READY
        self.process_list.append(new_proc)

        # Attempt memory allocation with First Fit by default
        addr = self.memory_manager.allocate(pid, name, mem, AllocationAlgorithm.FIRST_FIT)
        alloc_msg = f"Allocated {mem} KB at 0x{addr:04X}" if addr is not None else f"Memory allocation queued (waiting for free block)"
        if addr is not None:
            new_proc.allocated_address = addr
            new_proc.allocated_size = mem

        return f"[OK] Created process '{name}' (PID {pid}, BT={burst}, Mem={mem}KB, Pri={pri}). {alloc_msg}."

    def _cmd_kill(self, args: List[str]) -> str:
        if not args:
            return "Usage: kill <pid>"
        try:
            pid = int(args[0])
        except ValueError:
            return "bash: kill: PID must be an integer."

        proc = next((p for p in self.process_list if p.pid == pid), None)
        if not proc:
            return f"bash: kill: ({pid}) - No such process"

        proc.terminate()
        freed = self.memory_manager.deallocate(pid)
        return f"[OK] Process '{proc.name}' (PID {pid}) terminated. Memory freed: {'Yes' if freed else 'None'}."

    def _cmd_pause(self, args: List[str]) -> str:
        if not args:
            return "Usage: pause <pid>"
        try:
            pid = int(args[0])
        except ValueError:
            return "bash: pause: PID must be an integer."

        proc = next((p for p in self.process_list if p.pid == pid), None)
        if not proc:
            return f"bash: pause: ({pid}) - No such process"

        if proc.pause():
            return f"[OK] Process '{proc.name}' (PID {pid}) paused (State -> WAITING)."
        return f"Process '{proc.name}' cannot be paused from state {proc.state.value}."

    def _cmd_resume(self, args: List[str]) -> str:
        if not args:
            return "Usage: resume <pid>"
        try:
            pid = int(args[0])
        except ValueError:
            return "bash: resume: PID must be an integer."

        proc = next((p for p in self.process_list if p.pid == pid), None)
        if not proc:
            return f"bash: resume: ({pid}) - No such process"

        if proc.resume():
            return f"[OK] Process '{proc.name}' (PID {pid}) resumed (State -> READY)."
        return f"Process '{proc.name}' is not paused (Current state: {proc.state.value})."

    def _cmd_free(self, args: List[str]) -> str:
        m = self.memory_manager.get_stats()
        lines = [
            f"{'':<12} {'total':<10} {'used':<10} {'free':<10} {'shared/OS':<12} {'largest':<10}",
            f"{'Mem (KB):':<12} {m['total_memory_kb']:<10} {m['total_allocated_kb']:<10} {m['total_free_kb']:<10} {m['os_reserved_kb']:<12} {m['largest_free_block_kb']:<10}",
            f"{'Utilization:':<12} {m['utilization_pct']}%",
            f"{'External Frag:':<16} {m['external_frag_pct']}% across {m['num_free_holes']} free holes"
        ]
        return "\n".join(lines)

    def _cmd_disk(self, args: List[str]) -> str:
        return f"""Filesystem /dev/sda1
Current Disk Arm Head Position: Cylinder {self.disk_head}
Pending Track Requests Queue  : {self.disk_requests}
Total Cylinders               : 200 (Tracks 0 - 199)
"""

    def _cmd_sched(self, args: List[str]) -> str:
        algo = args[0].lower() if args else "fcfs"
        if algo == "fcfs":
            res = schedule_fcfs(self.process_list)
        elif algo == "sjf":
            res = schedule_sjf(self.process_list, preemptive=False)
        elif algo in ["srtf", "sjf-p"]:
            res = schedule_sjf(self.process_list, preemptive=True)
        elif algo == "rr":
            q = int(args[1]) if len(args) > 1 and args[1].isdigit() else 2
            res = schedule_round_robin(self.process_list, time_quantum=q)
        else:
            return f"Unknown algorithm '{algo}'. Available: fcfs, sjf, srtf, rr [quantum]"

        return f"""[OK] Executed {res.algorithm}
Total Time: {res.total_time} | CPU Utilization: {res.cpu_utilization:.2f}%
Avg Waiting Time: {res.avg_waiting_time:.2f} | Avg Turnaround Time: {res.avg_turnaround_time:.2f}
Gantt Sequence: {' | '.join([f'{s.name}[{s.start}-{s.end}]' for s in res.gantt])}
"""

    def _cmd_compact(self) -> str:
        moved = self.memory_manager.compact()
        return f"[OK] Memory compaction executed. {moved} process blocks consolidated toward base address."

    def _cmd_sysinfo(self, args: List[str]) -> str:
        return f"""OS Kernel Simulator v2.4-capstone
Host Platform : {platform.system()} {platform.release()} ({platform.machine()})
Python Core   : {sys.version.split()[0]}
System Time   : {datetime.datetime.now().isoformat()}
Architecture  : Virtual 64-bit Memory Addressing (Contiguous Dynamic Partitions)
"""
