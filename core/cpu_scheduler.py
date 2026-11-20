"""
CPU Scheduling Algorithms: FCFS, SJF (Preemptive & Non-Preemptive), and Round Robin.
Computes Gantt charts, metrics (Waiting Time, Turnaround Time, Response Time, CPU Utilization, Throughput).
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from core.pcb import Process, ProcessState


@dataclass
class GanttSegment:
    pid: Optional[int]
    name: str
    start: int
    end: int
    is_idle: bool = False

    @property
    def duration(self) -> int:
        return self.end - self.start

    def to_dict(self) -> Dict[str, Any]:
        return {
            "PID": self.pid if not self.is_idle else "IDLE",
            "Name": self.name,
            "Start": self.start,
            "End": self.end,
            "Duration": self.duration,
            "IsIdle": self.is_idle
        }


@dataclass
class CPUSchedulingResult:
    algorithm: str
    processes: List[Process]
    gantt: List[GanttSegment]
    total_time: int
    cpu_busy_time: int
    cpu_idle_time: int
    cpu_utilization: float
    throughput: float
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float
    params: Dict[str, Any] = field(default_factory=dict)

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "Algorithm": self.algorithm,
            "Total Time": self.total_time,
            "CPU Busy Time": self.cpu_busy_time,
            "CPU Idle Time": self.cpu_idle_time,
            "CPU Utilization (%)": round(self.cpu_utilization, 2),
            "Throughput (proc/unit)": round(self.throughput, 4),
            "Avg Waiting Time": round(self.avg_waiting_time, 2),
            "Avg Turnaround Time": round(self.avg_turnaround_time, 2),
            "Avg Response Time": round(self.avg_response_time, 2),
        }


def _consolidate_gantt(raw_segments: List[GanttSegment]) -> List[GanttSegment]:
    """Merge contiguous segments belonging to the same process or idle period."""
    if not raw_segments:
        return []
    
    merged = [raw_segments[0]]
    for seg in raw_segments[1:]:
        last = merged[-1]
        if last.pid == seg.pid and last.is_idle == seg.is_idle:
            last.end = seg.end
        else:
            merged.append(seg)
    return merged


def _calculate_metrics(algorithm: str, processes: List[Process], gantt: List[GanttSegment], total_time: int, params: Dict[str, Any] = None) -> CPUSchedulingResult:
    if not processes:
        return CPUSchedulingResult(
            algorithm=algorithm,
            processes=[],
            gantt=[],
            total_time=0,
            cpu_busy_time=0,
            cpu_idle_time=0,
            cpu_utilization=0.0,
            throughput=0.0,
            avg_waiting_time=0.0,
            avg_turnaround_time=0.0,
            avg_response_time=0.0,
            params=params or {}
        )

    gantt = _consolidate_gantt(gantt)
    total_busy = sum(s.duration for s in gantt if not s.is_idle)
    total_idle = sum(s.duration for s in gantt if s.is_idle)
    total_span = max(total_time, 1)

    cpu_util = (total_busy / total_span) * 100.0
    throughput = len(processes) / total_span if total_span > 0 else 0.0

    avg_wt = sum(p.waiting_time for p in processes) / len(processes)
    avg_tat = sum(p.turnaround_time for p in processes) / len(processes)
    avg_rt = sum(p.response_time for p in processes) / len(processes)

    return CPUSchedulingResult(
        algorithm=algorithm,
        processes=processes,
        gantt=gantt,
        total_time=total_time,
        cpu_busy_time=total_busy,
        cpu_idle_time=total_idle,
        cpu_utilization=cpu_util,
        throughput=throughput,
        avg_waiting_time=avg_wt,
        avg_turnaround_time=avg_tat,
        avg_response_time=avg_rt,
        params=params or {}
    )


def schedule_fcfs(process_list: List[Process]) -> CPUSchedulingResult:
    """
    First-Come, First-Served (FCFS) CPU Scheduling.
    Processes are executed strictly in order of arrival time.
    """
    procs = [p.copy() for p in process_list]
    for p in procs:
        p.reset()

    # Sort primarily by arrival time, then by PID
    procs.sort(key=lambda p: (p.arrival_time, p.pid))

    current_time = 0
    gantt: List[GanttSegment] = []

    for p in procs:
        if p.state == ProcessState.WAITING:
            # Skip or hold paused processes
            continue

        if current_time < p.arrival_time:
            # CPU is idle waiting for process to arrive
            gantt.append(GanttSegment(pid=None, name="Idle", start=current_time, end=p.arrival_time, is_idle=True))
            current_time = p.arrival_time

        start_time = current_time
        p.start_time = start_time
        p.response_time = start_time - p.arrival_time
        
        current_time += p.burst_time
        p.completion_time = current_time
        p.remaining_time = 0
        p.turnaround_time = p.completion_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time
        p.state = ProcessState.TERMINATED

        gantt.append(GanttSegment(pid=p.pid, name=p.name, start=start_time, end=current_time, is_idle=False))

    return _calculate_metrics("FCFS (First-Come First-Served)", procs, gantt, current_time)


def schedule_sjf(process_list: List[Process], preemptive: bool = False) -> CPUSchedulingResult:
    """
    Shortest Job First (SJF).
    - If preemptive=False: Non-Preemptive SJF (selects available job with smallest burst).
    - If preemptive=True: Preemptive SJF / SRTF (Shortest Remaining Time First).
    """
    procs = [p.copy() for p in process_list]
    for p in procs:
        p.reset()

    algo_name = "SJF (Preemptive - SRTF)" if preemptive else "SJF (Non-Preemptive)"
    gantt: List[GanttSegment] = []
    current_time = 0
    completed_count = 0
    n = len(procs)

    if not preemptive:
        # Non-preemptive SJF
        ready_pool = list(procs)
        while completed_count < n:
            available = [p for p in ready_pool if p.arrival_time <= current_time and p.state != ProcessState.TERMINATED and p.state != ProcessState.WAITING]
            if not available:
                # Find earliest upcoming arrival
                uncompleted = [p for p in ready_pool if p.state != ProcessState.TERMINATED and p.state != ProcessState.WAITING]
                if not uncompleted:
                    break
                next_arrival = min(p.arrival_time for p in uncompleted)
                gantt.append(GanttSegment(pid=None, name="Idle", start=current_time, end=next_arrival, is_idle=True))
                current_time = next_arrival
                continue

            # Pick shortest burst time
            chosen = min(available, key=lambda p: (p.burst_time, p.arrival_time, p.pid))
            chosen.start_time = current_time
            chosen.response_time = chosen.start_time - chosen.arrival_time

            start = current_time
            current_time += chosen.burst_time
            chosen.completion_time = current_time
            chosen.remaining_time = 0
            chosen.turnaround_time = chosen.completion_time - chosen.arrival_time
            chosen.waiting_time = chosen.turnaround_time - chosen.burst_time
            chosen.state = ProcessState.TERMINATED
            completed_count += 1

            gantt.append(GanttSegment(pid=chosen.pid, name=chosen.name, start=start, end=current_time, is_idle=False))

    else:
        # Preemptive SJF / SRTF (discrete tick simulation)
        while completed_count < n:
            available = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0 and p.state != ProcessState.WAITING]
            if not available:
                uncompleted = [p for p in procs if p.remaining_time > 0 and p.state != ProcessState.WAITING]
                if not uncompleted:
                    break
                next_arr = min(p.arrival_time for p in uncompleted)
                gantt.append(GanttSegment(pid=None, name="Idle", start=current_time, end=next_arr, is_idle=True))
                current_time = next_arr
                continue

            chosen = min(available, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))
            if chosen.start_time is None:
                chosen.start_time = current_time
                chosen.response_time = current_time - chosen.arrival_time

            # Run for 1 time unit
            chosen.remaining_time -= 1
            gantt.append(GanttSegment(pid=chosen.pid, name=chosen.name, start=current_time, end=current_time + 1, is_idle=False))
            current_time += 1

            if chosen.remaining_time == 0:
                chosen.completion_time = current_time
                chosen.turnaround_time = chosen.completion_time - chosen.arrival_time
                chosen.waiting_time = chosen.turnaround_time - chosen.burst_time
                chosen.state = ProcessState.TERMINATED
                completed_count += 1

    return _calculate_metrics(algo_name, procs, gantt, current_time, {"preemptive": preemptive})


def schedule_round_robin(process_list: List[Process], time_quantum: int = 2) -> CPUSchedulingResult:
    """
    Round Robin (RR) CPU Scheduling.
    Preemptive time-sliced scheduling with a configurable time quantum.
    """
    time_quantum = max(1, time_quantum)
    procs = [p.copy() for p in process_list]
    for p in procs:
        p.reset()

    # Sort by arrival time initially
    procs.sort(key=lambda p: (p.arrival_time, p.pid))

    gantt: List[GanttSegment] = []
    current_time = 0
    ready_queue: List[Process] = []
    arrived_indices = set()
    completed_count = 0
    n = len(procs)

    def enqueue_new_arrivals(curr_t: int):
        for idx, p in enumerate(procs):
            if idx not in arrived_indices and p.arrival_time <= curr_t and p.state != ProcessState.WAITING:
                ready_queue.append(p)
                arrived_indices.add(idx)

    enqueue_new_arrivals(current_time)

    while completed_count < n:
        if not ready_queue:
            # Find earliest upcoming arrival
            uncompleted = [p for p in procs if p.remaining_time > 0 and p.state != ProcessState.WAITING]
            if not uncompleted:
                break
            next_arrival = min(p.arrival_time for p in uncompleted)
            gantt.append(GanttSegment(pid=None, name="Idle", start=current_time, end=next_arrival, is_idle=True))
            current_time = next_arrival
            enqueue_new_arrivals(current_time)
            continue

        curr_proc = ready_queue.pop(0)

        if curr_proc.start_time is None:
            curr_proc.start_time = current_time
            curr_proc.response_time = current_time - curr_proc.arrival_time

        exec_time = min(time_quantum, curr_proc.remaining_time)
        start = current_time
        current_time += exec_time
        curr_proc.remaining_time -= exec_time

        gantt.append(GanttSegment(pid=curr_proc.pid, name=curr_proc.name, start=start, end=current_time, is_idle=False))

        # Check any newly arrived processes during this quantum before putting current process back
        enqueue_new_arrivals(current_time)

        if curr_proc.remaining_time > 0:
            ready_queue.append(curr_proc)
        else:
            curr_proc.completion_time = current_time
            curr_proc.turnaround_time = curr_proc.completion_time - curr_proc.arrival_time
            curr_proc.waiting_time = curr_proc.turnaround_time - curr_proc.burst_time
            curr_proc.state = ProcessState.TERMINATED
            completed_count += 1

    return _calculate_metrics("Round Robin (RR)", procs, gantt, current_time, {"time_quantum": time_quantum})


def schedule_priority(process_list: List[Process], preemptive: bool = False) -> CPUSchedulingResult:
    """
    Priority Scheduling (Lower number = Higher priority).
    """
    procs = [p.copy() for p in process_list]
    for p in procs:
        p.reset()

    algo_name = "Priority (Preemptive)" if preemptive else "Priority (Non-Preemptive)"
    gantt: List[GanttSegment] = []
    current_time = 0
    completed_count = 0
    n = len(procs)

    if not preemptive:
        while completed_count < n:
            available = [p for p in procs if p.arrival_time <= current_time and p.state != ProcessState.TERMINATED and p.state != ProcessState.WAITING]
            if not available:
                uncompleted = [p for p in procs if p.state != ProcessState.TERMINATED and p.state != ProcessState.WAITING]
                if not uncompleted:
                    break
                next_arr = min(p.arrival_time for p in uncompleted)
                gantt.append(GanttSegment(pid=None, name="Idle", start=current_time, end=next_arr, is_idle=True))
                current_time = next_arr
                continue

            chosen = min(available, key=lambda p: (p.priority, p.arrival_time, p.pid))
            chosen.start_time = current_time
            chosen.response_time = current_time - chosen.arrival_time
            start = current_time
            current_time += chosen.burst_time
            chosen.completion_time = current_time
            chosen.remaining_time = 0
            chosen.turnaround_time = chosen.completion_time - chosen.arrival_time
            chosen.waiting_time = chosen.turnaround_time - chosen.burst_time
            chosen.state = ProcessState.TERMINATED
            completed_count += 1
            gantt.append(GanttSegment(pid=chosen.pid, name=chosen.name, start=start, end=current_time, is_idle=False))
    else:
        while completed_count < n:
            available = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0 and p.state != ProcessState.WAITING]
            if not available:
                uncompleted = [p for p in procs if p.remaining_time > 0 and p.state != ProcessState.WAITING]
                if not uncompleted:
                    break
                next_arr = min(p.arrival_time for p in uncompleted)
                gantt.append(GanttSegment(pid=None, name="Idle", start=current_time, end=next_arr, is_idle=True))
                current_time = next_arr
                continue

            chosen = min(available, key=lambda p: (p.priority, p.arrival_time, p.pid))
            if chosen.start_time is None:
                chosen.start_time = current_time
                chosen.response_time = current_time - chosen.arrival_time

            chosen.remaining_time -= 1
            gantt.append(GanttSegment(pid=chosen.pid, name=chosen.name, start=current_time, end=current_time + 1, is_idle=False))
            current_time += 1

            if chosen.remaining_time == 0:
                chosen.completion_time = current_time
                chosen.turnaround_time = chosen.completion_time - chosen.arrival_time
                chosen.waiting_time = chosen.turnaround_time - chosen.burst_time
                chosen.state = ProcessState.TERMINATED
                completed_count += 1

    return _calculate_metrics(algo_name, procs, gantt, current_time, {"preemptive": preemptive})
