"""
Process Control Block (PCB) and Process State Management.
Represents processes, states, and process lifecycle in the OS Resource Manager Simulator.
"""

from enum import Enum
from typing import Optional, Dict, Any


class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"        # Paused / Blocked
    TERMINATED = "TERMINATED"


class Process:
    """
    Process Control Block (PCB) data structure.
    Maintains all scheduling, execution, and memory metadata for a process.
    """
    def __init__(
        self,
        pid: int,
        name: str,
        burst_time: int,
        arrival_time: int = 0,
        memory_required: int = 64,
        priority: int = 1
    ):
        self.pid: int = pid
        self.name: str = name
        self.arrival_time: int = max(0, arrival_time)
        self.burst_time: int = max(1, burst_time)
        self.remaining_time: int = self.burst_time
        self.memory_required: int = max(1, memory_required)
        self.priority: int = priority
        self.state: ProcessState = ProcessState.NEW

        # Scheduling & Telemetry Metrics
        self.start_time: Optional[int] = None
        self.completion_time: Optional[int] = None
        self.waiting_time: int = 0
        self.turnaround_time: int = 0
        self.response_time: int = 0

        # Memory allocation tracker
        self.allocated_address: Optional[int] = None
        self.allocated_size: Optional[int] = None

    def pause(self) -> bool:
        """Pause a running or ready process, putting it in WAITING state."""
        if self.state in [ProcessState.READY, ProcessState.RUNNING]:
            self.state = ProcessState.WAITING
            return True
        return False

    def resume(self) -> bool:
        """Resume a waiting/paused process, moving it back to READY state."""
        if self.state == ProcessState.WAITING:
            self.state = ProcessState.READY
            return True
        return False

    def terminate(self, current_time: Optional[int] = None) -> bool:
        """Explicitly terminate the process."""
        if self.state != ProcessState.TERMINATED:
            self.state = ProcessState.TERMINATED
            if current_time is not None:
                self.completion_time = current_time
                self.turnaround_time = max(0, self.completion_time - self.arrival_time)
                self.waiting_time = max(0, self.turnaround_time - (self.burst_time - self.remaining_time))
            return True
        return False

    def reset(self):
        """Reset execution counters for fresh scheduling simulation."""
        self.remaining_time = self.burst_time
        self.state = ProcessState.NEW
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = 0
        self.allocated_address = None
        self.allocated_size = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert process PCB to a dictionary representation."""
        return {
            "PID": self.pid,
            "Name": self.name,
            "State": self.state.value,
            "Arrival Time (AT)": self.arrival_time,
            "Burst Time (BT)": self.burst_time,
            "Remaining Time": self.remaining_time,
            "Memory (KB)": self.memory_required,
            "Priority": self.priority,
            "Allocated Base Addr": f"0x{self.allocated_address:04X}" if self.allocated_address is not None else "Unallocated",
            "Start Time": self.start_time if self.start_time is not None else "-",
            "Completion Time (CT)": self.completion_time if self.completion_time is not None else "-",
            "Turnaround Time (TAT)": self.turnaround_time if self.completion_time is not None else "-",
            "Waiting Time (WT)": self.waiting_time if self.completion_time is not None else "-",
            "Response Time (RT)": self.response_time if self.start_time is not None else "-"
        }

    def copy(self) -> 'Process':
        """Deep copy process template for comparative scheduling."""
        p = Process(
            pid=self.pid,
            name=self.name,
            burst_time=self.burst_time,
            arrival_time=self.arrival_time,
            memory_required=self.memory_required,
            priority=self.priority
        )
        p.state = self.state
        return p

    def __repr__(self) -> str:
        return f"<Process PID={self.pid} Name={self.name} State={self.state.value} BT={self.burst_time} Rem={self.remaining_time}>"
