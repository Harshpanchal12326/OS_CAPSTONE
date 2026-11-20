"""
Analytics, Performance Metrics, and Export Generators for OS Resource Manager.
"""

from typing import List, Dict, Any, Optional
import io
import csv
from core.pcb import Process
from core.cpu_scheduler import CPUSchedulingResult, schedule_fcfs, schedule_sjf, schedule_round_robin
from core.memory_manager import MemoryManager
from core.disk_scheduler import DiskSchedulingResult, schedule_disk_fcfs, schedule_disk_sstf


def compare_cpu_algorithms(processes: List[Process], rr_quantum: int = 2) -> List[Dict[str, Any]]:
    """
    Simulates all CPU algorithms (FCFS, SJF Non-preemptive, SJF Preemptive, Round Robin)
    on an identical set of processes and returns comparative metrics.
    """
    if not processes:
        return []

    r_fcfs = schedule_fcfs(processes)
    r_sjf_np = schedule_sjf(processes, preemptive=False)
    r_sjf_p = schedule_sjf(processes, preemptive=True)
    r_rr = schedule_round_robin(processes, time_quantum=rr_quantum)

    results = [
        {
            "Algorithm": "FCFS",
            "Avg Waiting Time": round(r_fcfs.avg_waiting_time, 2),
            "Avg Turnaround Time": round(r_fcfs.avg_turnaround_time, 2),
            "Avg Response Time": round(r_fcfs.avg_response_time, 2),
            "CPU Utilization (%)": round(r_fcfs.cpu_utilization, 2),
            "Total Time": r_fcfs.total_time,
            "Throughput": round(r_fcfs.throughput, 4),
        },
        {
            "Algorithm": "SJF (Non-Preemptive)",
            "Avg Waiting Time": round(r_sjf_np.avg_waiting_time, 2),
            "Avg Turnaround Time": round(r_sjf_np.avg_turnaround_time, 2),
            "Avg Response Time": round(r_sjf_np.avg_response_time, 2),
            "CPU Utilization (%)": round(r_sjf_np.cpu_utilization, 2),
            "Total Time": r_sjf_np.total_time,
            "Throughput": round(r_sjf_np.throughput, 4),
        },
        {
            "Algorithm": "SJF (Preemptive / SRTF)",
            "Avg Waiting Time": round(r_sjf_p.avg_waiting_time, 2),
            "Avg Turnaround Time": round(r_sjf_p.avg_turnaround_time, 2),
            "Avg Response Time": round(r_sjf_p.avg_response_time, 2),
            "CPU Utilization (%)": round(r_sjf_p.cpu_utilization, 2),
            "Total Time": r_sjf_p.total_time,
            "Throughput": round(r_sjf_p.throughput, 4),
        },
        {
            "Algorithm": f"Round Robin (q={rr_quantum})",
            "Avg Waiting Time": round(r_rr.avg_waiting_time, 2),
            "Avg Turnaround Time": round(r_rr.avg_turnaround_time, 2),
            "Avg Response Time": round(r_rr.avg_response_time, 2),
            "CPU Utilization (%)": round(r_rr.cpu_utilization, 2),
            "Total Time": r_rr.total_time,
            "Throughput": round(r_rr.throughput, 4),
        }
    ]
    return results


def compare_disk_algorithms(initial_head: int, requests: List[int], cylinders: int = 200) -> List[Dict[str, Any]]:
    """
    Compares FCFS and SSTF disk scheduling algorithms.
    """
    if not requests:
        return []

    r_fcfs = schedule_disk_fcfs(initial_head, requests, cylinders)
    r_sstf = schedule_disk_sstf(initial_head, requests, cylinders)

    saving = 0.0
    if r_fcfs.total_seek_operations > 0:
        saving = round(
            ((r_fcfs.total_seek_operations - r_sstf.total_seek_operations) / r_fcfs.total_seek_operations) * 100.0,
            2
        )

    return [
        {
            "Algorithm": "FCFS",
            "Total Head Movements": r_fcfs.total_seek_operations,
            "Average Seek Distance": round(r_fcfs.average_seek_distance, 2),
            "Seek Reduction vs FCFS (%)": "0.0% (Baseline)",
            "Visited Sequence": " -> ".join(map(str, r_fcfs.seek_sequence))
        },
        {
            "Algorithm": "SSTF",
            "Total Head Movements": r_sstf.total_seek_operations,
            "Average Seek Distance": round(r_sstf.average_seek_distance, 2),
            "Seek Reduction vs FCFS (%)": f"{saving}%",
            "Visited Sequence": " -> ".join(map(str, r_sstf.seek_sequence))
        }
    ]


def generate_analytical_markdown_report(
    cpu_res: Optional[CPUSchedulingResult],
    memory_manager: MemoryManager,
    disk_res: Optional[DiskSchedulingResult]
) -> str:
    """
    Generates a full structured Markdown analytical report.
    """
    lines = []
    lines.append("# OS Resource Manager - Comprehensive Analytical Report\n")
    lines.append(f"*Generated automatically by OS Resource Manager Simulator Engine*\n")

    # 1. CPU Scheduling Section
    lines.append("## 1. CPU Scheduling Performance Analysis")
    if cpu_res:
        lines.append(f"- **Algorithm Tested**: {cpu_res.algorithm}")
        lines.append(f"- **Total Execution Time**: {cpu_res.total_time} time units")
        lines.append(f"- **CPU Busy Time**: {cpu_res.cpu_busy_time} units | **Idle Time**: {cpu_res.cpu_idle_time} units")
        lines.append(f"- **CPU Utilization**: **{cpu_res.cpu_utilization:.2f}%**")
        lines.append(f"- **Throughput**: {cpu_res.throughput:.4f} processes/unit")
        lines.append(f"- **Average Turnaround Time (TAT)**: {cpu_res.avg_turnaround_time:.2f}")
        lines.append(f"- **Average Waiting Time (WT)**: {cpu_res.avg_waiting_time:.2f}")
        lines.append(f"- **Average Response Time (RT)**: {cpu_res.avg_response_time:.2f}\n")

        lines.append("### Process Execution Table")
        lines.append("| PID | Name | Arrival Time | Burst Time | Completion Time | Turnaround Time | Waiting Time | Response Time |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for p in cpu_res.processes:
            lines.append(f"| {p.pid} | {p.name} | {p.arrival_time} | {p.burst_time} | {p.completion_time} | {p.turnaround_time} | {p.waiting_time} | {p.response_time} |")
        lines.append("\n")
    else:
        lines.append("No CPU scheduling simulation executed yet.\n")

    # 2. Memory Management Section
    lines.append("## 2. Memory Allocation & Fragmentation Analysis")
    m_stats = memory_manager.get_stats()
    lines.append(f"- **Total Memory**: {m_stats['total_memory_kb']} KB")
    lines.append(f"- **OS Reserved (Kernel)**: {m_stats['os_reserved_kb']} KB")
    lines.append(f"- **User Allocated Memory**: {m_stats['user_allocated_kb']} KB")
    lines.append(f"- **Total Free Memory**: {m_stats['total_free_kb']} KB")
    lines.append(f"- **Memory Utilization**: **{m_stats['utilization_pct']}%**")
    lines.append(f"- **Largest Contiguous Free Hole**: {m_stats['largest_free_block_kb']} KB")
    lines.append(f"- **Total Free Holes**: {m_stats['num_free_holes']}")
    lines.append(f"- **External Fragmentation Metric**: **{m_stats['external_frag_pct']}%**\n")

    lines.append("### Current Memory Segments Map")
    lines.append("| Base Address | End Address | Size (KB) | Status | PID | Process Name |")
    lines.append("|---|---|---|---|---|---|")
    for s in memory_manager.segments:
        pid_str = str(s.pid) if s.is_allocated else "-"
        pname_str = s.process_name if s.is_allocated else "(Free Hole)"
        status_str = "ALLOCATED" if s.is_allocated else "FREE"
        lines.append(f"| 0x{s.base_address:04X} | 0x{s.end_address:04X} | {s.size} | {status_str} | {pid_str} | {pname_str} |")
    lines.append("\n")

    # 3. Disk Scheduling Section
    lines.append("## 3. Disk Storage & I/O Seek Analysis")
    if disk_res:
        lines.append(f"- **Disk Algorithm**: {disk_res.algorithm}")
        lines.append(f"- **Initial Head Position**: Cylinder {disk_res.initial_head}")
        lines.append(f"- **Total Track Requests**: {len(disk_res.requests)}")
        lines.append(f"- **Total Head Movements (Seek Count)**: **{disk_res.total_seek_operations} cylinders**")
        lines.append(f"- **Average Seek Distance**: {disk_res.average_seek_distance:.2f} cylinders/request")
        lines.append(f"- **Head Trajectory Sequence**: `{' -> '.join(map(str, disk_res.seek_sequence))}`\n")
    else:
        lines.append("No disk scheduling simulation executed yet.\n")

    lines.append("## 4. Key Architectural Takeaways")
    lines.append("1. **CPU Scheduler Trade-offs**: Preemptive SJF (SRTF) minimizes average waiting time, while Round Robin guarantees fairness and bounds response time.")
    lines.append("2. **Memory Allocation Dynamics**: Best Fit minimizes immediate wasted remainder but can create small unusable slivers. Compaction eliminates external fragmentation by shifting blocks.")
    lines.append("3. **Disk Arm Optimization**: SSTF drastically reduces seek operations compared to FCFS by exploiting spatial locality, though starvation of distant cylinders must be guarded against.")

    return "\n".join(lines)


def export_processes_csv(processes: List[Process]) -> str:
    """Exports process list to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "PID", "Name", "State", "Arrival Time", "Burst Time",
        "Remaining Time", "Memory (KB)", "Priority",
        "Start Time", "Completion Time", "Turnaround Time", "Waiting Time", "Response Time"
    ])
    for p in processes:
        writer.writerow([
            p.pid, p.name, p.state.value, p.arrival_time, p.burst_time,
            p.remaining_time, p.memory_required, p.priority,
            p.start_time if p.start_time is not None else "",
            p.completion_time if p.completion_time is not None else "",
            p.turnaround_time, p.waiting_time, p.response_time
        ])
    return output.getvalue()
