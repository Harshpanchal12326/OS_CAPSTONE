"""
Matplotlib Visualizations for OS Resource Manager Simulator:
- Gantt Chart for CPU Scheduling
- Memory Layout Map (Allocated blocks, free holes, addresses)
- Disk Head Movement / Seek Trajectory
- Algorithm Comparison Bar Charts
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless Streamlit rendering
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import List, Dict, Any, Optional
from core.cpu_scheduler import CPUSchedulingResult, GanttSegment
from core.memory_manager import MemoryManager, MemorySegment
from core.disk_scheduler import DiskSchedulingResult


# Consistent modern dark/light-compatible aesthetic color palettes
COLOR_PALETTE = [
    "#3498DB", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6",
    "#1ABC9C", "#D35400", "#34495E", "#16A085", "#27AE60",
    "#8E44AD", "#2980B9", "#E67E22", "#C0392B", "#7F8C8D"
]
IDLE_COLOR = "#BDC3C7"
KERNEL_COLOR = "#2C3E50"
FREE_COLOR = "#ECF0F1"


def plot_gantt_chart(result: CPUSchedulingResult) -> plt.Figure:
    """
    Renders a Gantt Chart representing CPU scheduling execution timeline.
    """
    fig, ax = plt.subplots(figsize=(10, 3.2), dpi=100)

    if not result.gantt:
        ax.text(0.5, 0.5, "No Process Execution Data", ha="center", va="center", fontsize=14, color="gray")
        ax.axis("off")
        return fig

    # Map PIDs to consistent colors
    pids = list(set(s.pid for s in result.gantt if not s.is_idle and s.pid is not None))
    pid_color_map = {pid: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, pid in enumerate(pids)}

    y_pos = 0.5
    height = 0.5

    for seg in result.gantt:
        color = IDLE_COLOR if seg.is_idle else pid_color_map.get(seg.pid, "#3498DB")
        label = "IDLE" if seg.is_idle else f"P{seg.pid} ({seg.name})"

        # Draw execution block
        rect = patches.Rectangle(
            (seg.start, y_pos - height / 2),
            seg.duration,
            height,
            linewidth=1.2,
            edgecolor="#2C3E50",
            facecolor=color,
            alpha=0.9
        )
        ax.add_patch(rect)

        # Center text inside block
        mid_x = seg.start + seg.duration / 2
        text_color = "black" if seg.is_idle else "white"
        ax.text(
            mid_x,
            y_pos,
            label,
            ha="center",
            va="center",
            color=text_color,
            fontsize=10,
            fontweight="bold"
        )

        # Bottom timeline marker
        ax.text(seg.start, y_pos - height / 2 - 0.12, str(seg.start), ha="center", va="top", fontsize=9, color="#555")

    # Mark the final timestamp
    final_time = result.total_time
    ax.text(final_time, y_pos - height / 2 - 0.12, str(final_time), ha="center", va="top", fontsize=9, color="#555")

    ax.set_xlim(-0.5, max(final_time + 1, 5))
    ax.set_ylim(0, 1.2)
    ax.set_yticks([])
    ax.set_xlabel("Time Units (Timeline)", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_title(f"CPU Execution Timeline (Gantt Chart) - {result.algorithm}", fontsize=13, fontweight="bold", pad=12)
    ax.grid(axis="x", linestyle=":", alpha=0.6)

    # Style borders
    for spine in ["top", "left", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#BDC3C7")

    fig.tight_layout()
    return fig


def plot_memory_map(memory_manager: MemoryManager) -> plt.Figure:
    """
    Renders a horizontal visual memory layout displaying physical address boundaries,
    allocated processes, OS kernel reserved space, and free fragmentation holes.
    """
    fig, ax = plt.subplots(figsize=(10, 3.2), dpi=100)

    total_mem = memory_manager.total_memory
    y_pos = 0.5
    bar_height = 0.45

    segments = memory_manager.segments
    if not segments:
        ax.text(0.5, 0.5, "Memory Uninitialized", ha="center", va="center")
        ax.axis("off")
        return fig

    # Build unique colors for allocated processes
    proc_colors = {}
    c_idx = 0
    for seg in segments:
        if seg.is_allocated and seg.pid != 0 and seg.pid not in proc_colors:
            proc_colors[seg.pid] = COLOR_PALETTE[c_idx % len(COLOR_PALETTE)]
            c_idx += 1

    for seg in segments:
        if not seg.is_allocated:
            fill_color = FREE_COLOR
            edge_color = "#95A5A6"
            label = f"FREE\n{seg.size} KB"
            text_color = "#333333"
            hatch = "//"
        elif seg.pid == 0:
            fill_color = KERNEL_COLOR
            edge_color = "#1A252F"
            label = f"OS Kernel\n{seg.size} KB"
            text_color = "white"
            hatch = None
        else:
            fill_color = proc_colors.get(seg.pid, "#2980B9")
            edge_color = "#1B4F72"
            label = f"{seg.process_name}\n(P{seg.pid})\n{seg.size} KB"
            text_color = "white"
            hatch = None

        rect = patches.Rectangle(
            (seg.base_address, y_pos - bar_height / 2),
            seg.size,
            bar_height,
            linewidth=1.2,
            edgecolor=edge_color,
            facecolor=fill_color,
            hatch=hatch,
            alpha=0.92
        )
        ax.add_patch(rect)

        # Center label if wide enough
        if (seg.size / total_mem) > 0.05:
            ax.text(
                seg.base_address + seg.size / 2,
                y_pos,
                label,
                ha="center",
                va="center",
                color=text_color,
                fontsize=9,
                fontweight="bold"
            )

        # Base address tick annotation
        ax.text(
            seg.base_address,
            y_pos - bar_height / 2 - 0.12,
            f"0x{seg.base_address:03X}",
            ha="center",
            va="top",
            fontsize=8,
            color="#555555",
            rotation=45
        )

    # End boundary
    ax.text(
        total_mem,
        y_pos - bar_height / 2 - 0.12,
        f"0x{total_mem:03X}",
        ha="center",
        va="top",
        fontsize=8,
        color="#555555",
        rotation=45
    )

    ax.set_xlim(0, total_mem)
    ax.set_ylim(0, 1.2)
    ax.set_yticks([])
    ax.set_xlabel("Memory Address Space (Kilobytes)", fontsize=11, fontweight="bold", labelpad=15)
    ax.set_title(f"Dynamic Contiguous Memory Partition Map (Total: {total_mem} KB)", fontsize=13, fontweight="bold", pad=12)

    for spine in ["top", "left", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#BDC3C7")

    fig.tight_layout()
    return fig


def plot_disk_trajectory(
    result_fcfs: Optional[DiskSchedulingResult],
    result_sstf: Optional[DiskSchedulingResult]
) -> plt.Figure:
    """
    Renders the Disk Head Seek Trajectory graph comparing FCFS and SSTF head movement steps.
    """
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=100)

    if result_fcfs and result_fcfs.seek_sequence:
        steps_fcfs = list(range(len(result_fcfs.seek_sequence)))
        ax.plot(
            result_fcfs.seek_sequence,
            steps_fcfs,
            marker="o",
            linewidth=2,
            color="#E74C3C",
            label=f"FCFS (Total Seek: {result_fcfs.total_seek_operations})"
        )
        for track, step in zip(result_fcfs.seek_sequence, steps_fcfs):
            ax.annotate(str(track), (track, step), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8, color="#C0392B")

    if result_sstf and result_sstf.seek_sequence:
        steps_sstf = list(range(len(result_sstf.seek_sequence)))
        ax.plot(
            result_sstf.seek_sequence,
            steps_sstf,
            marker="s",
            linewidth=2,
            linestyle="--",
            color="#2ECC71",
            label=f"SSTF (Total Seek: {result_sstf.total_seek_operations})"
        )
        for track, step in zip(result_sstf.seek_sequence, steps_sstf):
            ax.annotate(str(track), (track, step), textcoords="offset points", xytext=(0, -12), ha="center", fontsize=8, color="#27AE60")

    cylinders = result_fcfs.total_cylinders if result_fcfs else 200
    ax.set_xlim(-5, cylinders + 5)
    ax.set_xlabel("Disk Track / Cylinder Position", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_ylabel("Request Service Order (Step)", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_title("Disk Head Arm Trajectory & Movement Comparison", fontsize=13, fontweight="bold", pad=12)
    ax.invert_yaxis()  # Standard OS textbook diagram convention: steps go downward
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="best", frameon=True)

    fig.tight_layout()
    return fig


def plot_cpu_comparison_bar(comparison_data: List[Dict[str, Any]]) -> plt.Figure:
    """
    Bar chart comparing Average Waiting Time and Average Turnaround Time across CPU algorithms.
    """
    fig, ax = plt.subplots(figsize=(8.5, 3.8), dpi=100)

    if not comparison_data:
        ax.text(0.5, 0.5, "No Comparison Data", ha="center", va="center")
        ax.axis("off")
        return fig

    algos = [d["Algorithm"] for d in comparison_data]
    wt = [d["Avg Waiting Time"] for d in comparison_data]
    tat = [d["Avg Turnaround Time"] for d in comparison_data]

    x = np.arange(len(algos))
    width = 0.35

    rects1 = ax.bar(x - width/2, wt, width, label="Avg Waiting Time", color="#3498DB", alpha=0.9)
    rects2 = ax.bar(x + width/2, tat, width, label="Avg Turnaround Time", color="#E67E22", alpha=0.9)

    ax.set_ylabel("Time Units", fontsize=11, fontweight="bold")
    ax.set_title("CPU Scheduling Performance Comparison", fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(algos, fontsize=9, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    # Bar value labels
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h}", xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h}", xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)

    fig.tight_layout()
    return fig
