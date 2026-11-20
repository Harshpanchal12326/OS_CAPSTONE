"""
OS Resource Manager Simulator
An interactive OS simulation platform showcasing:
- CPU Scheduling: FCFS, SJF (Preemptive & Non-Preemptive), Round Robin
- Memory Allocation: First Fit, Best Fit, Worst Fit, Compaction & Fragmentation analysis
- Process Lifecycle Management: Create, Terminate, Pause, Resume
- Disk Scheduling: FCFS and SSTF head movement simulation
- Real-time Performance Metrics & Gantt/Memory/Disk Visualizations
- Interactive Bash / Shell Terminal
- Analytical Reports & Data Exports
"""

import streamlit as st
import pandas as pd
import datetime
from typing import List

# Core OS simulation modules
from core.pcb import Process, ProcessState
from core.cpu_scheduler import (
    schedule_fcfs,
    schedule_sjf,
    schedule_round_robin,
    CPUSchedulingResult
)
from core.memory_manager import MemoryManager, AllocationAlgorithm
from core.disk_scheduler import (
    schedule_disk_fcfs,
    schedule_disk_sstf,
    DiskSchedulingResult
)
from core.shell_interpreter import ShellInterpreter
from core.metrics import (
    compare_cpu_algorithms,
    compare_disk_algorithms,
    generate_analytical_markdown_report,
    export_processes_csv
)
from visualization.charts import (
    plot_gantt_chart,
    plot_memory_map,
    plot_disk_trajectory,
    plot_cpu_comparison_bar
)

# Configure Streamlit Page
st.set_page_config(
    page_title="OS Resource Manager Simulator",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark/Modern OS Theme)
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 13px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .state-badge-ready { background-color: #0284c7; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .state-badge-running { background-color: #16a34a; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .state-badge-waiting { background-color: #d97706; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .state-badge-terminated { background-color: #dc2626; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .terminal-box {
        background-color: #0d1117;
        color: #58a6ff;
        font-family: 'Courier New', monospace;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        height: 380px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
def init_session_state():
    if "memory_manager" not in st.session_state:
        mm = MemoryManager(total_memory_kb=1024, os_reserved_kb=128)
        st.session_state.memory_manager = mm

    if "processes" not in st.session_state:
        # Default realistic benchmark workload
        initial_procs = [
            Process(pid=1, name="Web_Server", burst_time=6, arrival_time=0, memory_required=160, priority=2),
            Process(pid=2, name="Database_Query", burst_time=8, arrival_time=1, memory_required=220, priority=1),
            Process(pid=3, name="UI_Compositor", burst_time=4, arrival_time=2, memory_required=120, priority=3),
            Process(pid=4, name="Cache_Worker", burst_time=3, arrival_time=4, memory_required=80, priority=2),
            Process(pid=5, name="Log_Flusher", burst_time=5, arrival_time=5, memory_required=140, priority=4)
        ]
        # Allocate initial memory
        for p in initial_procs:
            p.state = ProcessState.READY
            addr = st.session_state.memory_manager.allocate(p.pid, p.name, p.memory_required, AllocationAlgorithm.FIRST_FIT)
            if addr is not None:
                p.allocated_address = addr
                p.allocated_size = p.memory_required

        st.session_state.processes = initial_procs

    if "cpu_result" not in st.session_state:
        st.session_state.cpu_result = schedule_fcfs(st.session_state.processes)

    if "disk_requests" not in st.session_state:
        st.session_state.disk_requests = [98, 183, 37, 122, 14, 124, 65, 67]
        st.session_state.disk_head = 53
        st.session_state.disk_result_fcfs = schedule_disk_fcfs(53, st.session_state.disk_requests)
        st.session_state.disk_result_sstf = schedule_disk_sstf(53, st.session_state.disk_requests)

    if "terminal_output" not in st.session_state:
        st.session_state.terminal_output = [
            "OS Resource Manager Simulator Kernel v2.4 initialized.",
            "Type 'help' to view available Unix/Bash commands (e.g. ps, top, create, kill, free, df, sched, compact)."
        ]


init_session_state()


# Helper Functions
def load_scenario(scenario_name: str):
    mm = MemoryManager(total_memory_kb=1024, os_reserved_kb=128)
    st.session_state.memory_manager = mm

    if scenario_name == "Balanced Workload":
        procs = [
            Process(pid=1, name="Web_Server", burst_time=6, arrival_time=0, memory_required=160, priority=2),
            Process(pid=2, name="Database_Query", burst_time=8, arrival_time=1, memory_required=220, priority=1),
            Process(pid=3, name="UI_Compositor", burst_time=4, arrival_time=2, memory_required=120, priority=3),
            Process(pid=4, name="Cache_Worker", burst_time=3, arrival_time=4, memory_required=80, priority=2),
            Process(pid=5, name="Log_Flusher", burst_time=5, arrival_time=5, memory_required=140, priority=4)
        ]
    elif scenario_name == "High CPU Burst Load":
        procs = [
            Process(pid=1, name="ML_Inference", burst_time=18, arrival_time=0, memory_required=300, priority=1),
            Process(pid=2, name="Video_Encode", burst_time=14, arrival_time=2, memory_required=260, priority=2),
            Process(pid=3, name="Ray_Tracer", burst_time=20, arrival_time=3, memory_required=220, priority=3),
            Process(pid=4, name="Background_Sync", burst_time=4, arrival_time=6, memory_required=90, priority=4)
        ]
    elif scenario_name == "Memory Fragmentation Challenge":
        procs = [
            Process(pid=1, name="Alloc_Block1", burst_time=4, arrival_time=0, memory_required=150, priority=1),
            Process(pid=2, name="Alloc_Block2", burst_time=6, arrival_time=1, memory_required=250, priority=2),
            Process(pid=3, name="Alloc_Block3", burst_time=5, arrival_time=2, memory_required=180, priority=3),
            Process(pid=4, name="Alloc_Block4", burst_time=3, arrival_time=3, memory_required=120, priority=4),
        ]
    else:
        procs = [
            Process(pid=1, name="Kernel_Task", burst_time=5, arrival_time=0, memory_required=100, priority=1)
        ]

    for p in procs:
        p.state = ProcessState.READY
        addr = mm.allocate(p.pid, p.name, p.memory_required, AllocationAlgorithm.FIRST_FIT)
        if addr is not None:
            p.allocated_address = addr
            p.allocated_size = p.memory_required

    # If fragmentation scenario, deliberately deallocate block 2 to introduce a hole
    if scenario_name == "Memory Fragmentation Challenge" and len(procs) >= 2:
        mm.deallocate(procs[1].pid)
        procs[1].state = ProcessState.TERMINATED
        procs[1].allocated_address = None

    st.session_state.processes = procs
    st.session_state.cpu_result = schedule_fcfs(procs)


# Sidebar Configuration & Navigation
with st.sidebar:
    st.title("🖥️ OS Manager")
    st.caption("Operating System Resource Simulator")
    st.markdown("---")

    nav_choice = st.radio(
        "Navigation",
        [
            "📊 Dashboard Overview",
            "⚡ CPU Scheduling",
            "💾 Memory Allocation",
            "💽 Disk Scheduling",
            "💻 Bash Shell Terminal",
            "📈 Analytical Reports"
        ],
        index=0
    )

    st.markdown("---")
    st.subheader("⚙️ Simulation Scenarios")
    scenario_sel = st.selectbox(
        "Load Preset Workload",
        ["Balanced Workload", "High CPU Burst Load", "Memory Fragmentation Challenge"]
    )
    if st.button("Apply Preset Scenario", use_container_width=True):
        load_scenario(scenario_sel)
        st.success(f"Loaded scenario: {scenario_sel}")
        st.rerun()

    st.markdown("---")
    if st.button("🔄 Reset Entire Simulator", use_container_width=True):
        st.session_state.memory_manager.reset()
        st.session_state.processes = []
        load_scenario("Balanced Workload")
        st.session_state.terminal_output = ["Simulator reset to clean state."]
        st.rerun()


# ==============================================================================
# TAB 1: DASHBOARD OVERVIEW
# ==============================================================================
if nav_choice == "📊 Dashboard Overview":
    st.title("🖥️ OS Resource Manager Dashboard")
    st.markdown("Real-time telemetry and management of CPU scheduling, memory partitions, disk head, and active processes.")

    # Top KPI Metrics Cards
    col1, col2, col3, col4 = st.columns(4)

    cpu_res = st.session_state.cpu_result
    mem_stats = st.session_state.memory_manager.get_stats()
    active_procs = [p for p in st.session_state.processes if p.state != ProcessState.TERMINATED]

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">CPU Utilization</div>
            <div class="metric-value">{cpu_res.cpu_utilization:.1f}%</div>
            <div style="font-size:12px; color:#38bdf8;">Algorithm: {cpu_res.algorithm.split('(')[0]}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Memory Used</div>
            <div class="metric-value">{mem_stats['utilization_pct']}%</div>
            <div style="font-size:12px; color:#38bdf8;">{mem_stats['total_allocated_kb']} / {mem_stats['total_memory_kb']} KB</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Waiting Time</div>
            <div class="metric-value">{cpu_res.avg_waiting_time:.1f} <span style="font-size:16px;">units</span></div>
            <div style="font-size:12px; color:#38bdf8;">Avg TAT: {cpu_res.avg_turnaround_time:.1f} units</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Processes</div>
            <div class="metric-value">{len(active_procs)} <span style="font-size:16px;">/ {len(st.session_state.processes)}</span></div>
            <div style="font-size:12px; color:#38bdf8;">Ext Frag: {mem_stats['external_frag_pct']}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Visualizations Row: Gantt + Memory Map
    vcol1, vcol2 = st.columns([1, 1])
    with vcol1:
        st.subheader("⚡ CPU Execution Timeline (Gantt)")
        fig_gantt = plot_gantt_chart(cpu_res)
        st.pyplot(fig_gantt)

    with vcol2:
        st.subheader("💾 Physical Memory Layout Map")
        fig_mem = plot_memory_map(st.session_state.memory_manager)
        st.pyplot(fig_mem)

    st.markdown("---")

    # Interactive Process Management Section
    st.subheader("📋 Active Process Management & State Control")
    st.caption("Create, pause, resume, or terminate processes in the system. Allocated memory updates dynamically.")

    # Process Actions Table
    if st.session_state.processes:
        table_data = []
        for p in st.session_state.processes:
            table_data.append({
                "PID": p.pid,
                "Process Name": p.name,
                "State": p.state.value,
                "Arrival Time": p.arrival_time,
                "Burst Time": p.burst_time,
                "Remaining Time": p.remaining_time,
                "Memory (KB)": p.memory_required,
                "Base Address": f"0x{p.allocated_address:04X}" if p.allocated_address is not None else "Unallocated",
                "Priority": p.priority
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

        # Quick Process Controller Controls
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 3, 2])
        with ctrl_col1:
            sel_pid = st.selectbox(
                "Select Target Process PID",
                [p.pid for p in st.session_state.processes],
                format_func=lambda x: f"PID {x}: {next((p.name for p in st.session_state.processes if p.pid == x), '')}"
            )
        with ctrl_col2:
            st.write("Process State Actions:")
            act_col1, act_col2, act_col3 = st.columns(3)
            with act_col1:
                if st.button("⏸️ Pause", use_container_width=True):
                    proc = next((p for p in st.session_state.processes if p.pid == sel_pid), None)
                    if proc and proc.pause():
                        st.success(f"PID {sel_pid} paused (WAITING)")
                        st.rerun()
            with act_col2:
                if st.button("▶️ Resume", use_container_width=True):
                    proc = next((p for p in st.session_state.processes if p.pid == sel_pid), None)
                    if proc and proc.resume():
                        st.success(f"PID {sel_pid} resumed (READY)")
                        st.rerun()
            with act_col3:
                if st.button("🛑 Terminate", use_container_width=True):
                    proc = next((p for p in st.session_state.processes if p.pid == sel_pid), None)
                    if proc:
                        proc.terminate()
                        st.session_state.memory_manager.deallocate(sel_pid)
                        st.success(f"PID {sel_pid} terminated & memory freed.")
                        st.rerun()

    # Form to add a new process
    with st.expander("➕ Spawn New Process Control Block (PCB)"):
        with st.form("new_proc_form"):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                p_name = st.text_input("Process Name", value=f"Proc_{len(st.session_state.processes)+1}")
            with f_col2:
                p_burst = st.number_input("Burst Time (CPU)", min_value=1, max_value=50, value=5)
            with f_col3:
                p_mem = st.number_input("Memory Required (KB)", min_value=10, max_value=512, value=128)
            with f_col4:
                p_arrival = st.number_input("Arrival Time", min_value=0, max_value=50, value=0)

            f_col5, f_col6 = st.columns([1, 1])
            with f_col5:
                p_priority = st.slider("Priority (1 = Highest)", min_value=1, max_value=10, value=2)
            with f_col6:
                p_alloc_algo = st.selectbox("Memory Placement Algorithm", ["First Fit", "Best Fit", "Worst Fit"])

            submitted = st.form_submit_button("🚀 Spawn & Allocate Process", use_container_width=True)
            if submitted:
                new_pid = max([p.pid for p in st.session_state.processes], default=0) + 1
                new_p = Process(
                    pid=new_pid,
                    name=p_name,
                    burst_time=int(p_burst),
                    arrival_time=int(p_arrival),
                    memory_required=int(p_mem),
                    priority=int(p_priority)
                )
                new_p.state = ProcessState.READY
                st.session_state.processes.append(new_p)

                algo_map = {
                    "First Fit": AllocationAlgorithm.FIRST_FIT,
                    "Best Fit": AllocationAlgorithm.BEST_FIT,
                    "Worst Fit": AllocationAlgorithm.WORST_FIT
                }
                addr = st.session_state.memory_manager.allocate(new_pid, p_name, int(p_mem), algo_map[p_alloc_algo])
                if addr is not None:
                    new_p.allocated_address = addr
                    new_p.allocated_size = int(p_mem)
                    st.success(f"Created process '{p_name}' (PID {new_pid}) and allocated {p_mem} KB at 0x{addr:04X}.")
                else:
                    st.warning(f"Created process '{p_name}', but insufficient contiguous memory. Process waiting in queue.")

                st.session_state.cpu_result = schedule_fcfs(st.session_state.processes)
                st.rerun()


# ==============================================================================
# TAB 2: CPU SCHEDULING SIMULATOR
# ==============================================================================
elif nav_choice == "⚡ CPU Scheduling":
    st.title("⚡ CPU Scheduling Simulator")
    st.markdown("Simulate and analyze **FCFS**, **SJF (Shortest Job First)**, and **Round Robin** with arbitrary arrival times and bursts.")

    # Algorithm selector & controls
    col_a, col_b, col_c = st.columns([2, 2, 2])
    with col_a:
        algo_choice = st.selectbox(
            "Select CPU Scheduling Algorithm",
            ["First-Come, First-Served (FCFS)", "Shortest Job First (SJF)", "Round Robin (RR)"]
        )

    with col_b:
        sjf_preempt = False
        time_quantum = 2
        if "SJF" in algo_choice:
            sjf_preempt = st.checkbox("Enable Preemption (SRTF - Shortest Remaining Time First)", value=False)
        elif "Round Robin" in algo_choice:
            time_quantum = st.slider("Time Quantum (q)", min_value=1, max_value=10, value=2)

    with col_c:
        st.write("")
        st.write("")
        run_cpu = st.button("🚀 Run CPU Scheduler", use_container_width=True)

    # Execute Scheduling
    if run_cpu or "cpu_result" not in st.session_state:
        if "FCFS" in algo_choice:
            res = schedule_fcfs(st.session_state.processes)
        elif "SJF" in algo_choice:
            res = schedule_sjf(st.session_state.processes, preemptive=sjf_preempt)
        else:
            res = schedule_round_robin(st.session_state.processes, time_quantum=time_quantum)
        st.session_state.cpu_result = res

    res = st.session_state.cpu_result

    # Display Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("CPU Utilization", f"{res.cpu_utilization:.2f}%")
    m2.metric("Avg Waiting Time (WT)", f"{res.avg_waiting_time:.2f}")
    m3.metric("Avg Turnaround Time (TAT)", f"{res.avg_turnaround_time:.2f}")
    m4.metric("Avg Response Time (RT)", f"{res.avg_response_time:.2f}")
    m5.metric("Throughput", f"{res.throughput:.4f}/unit")

    # Gantt Chart Visualizer
    st.subheader(f"📊 Execution Gantt Chart: {res.algorithm}")
    fig_g = plot_gantt_chart(res)
    st.pyplot(fig_g)

    # Detailed Process Execution Table
    st.subheader("📋 Process Scheduling Execution Results")
    proc_rows = []
    for p in res.processes:
        proc_rows.append({
            "PID": p.pid,
            "Name": p.name,
            "Arrival Time (AT)": p.arrival_time,
            "Burst Time (BT)": p.burst_time,
            "Completion Time (CT)": p.completion_time,
            "Turnaround Time (TAT = CT - AT)": p.turnaround_time,
            "Waiting Time (WT = TAT - BT)": p.waiting_time,
            "Response Time (RT)": p.response_time
        })
    st.dataframe(pd.DataFrame(proc_rows), use_container_width=True)

    # Comparative Performance Evaluation
    st.markdown("---")
    st.subheader("⚖️ Algorithm Side-by-Side Comparison")
    st.caption("Benchmark how FCFS, SJF (Preemptive & Non-Preemptive), and Round Robin perform on this exact same process workload.")

    comp_data = compare_cpu_algorithms(st.session_state.processes, rr_quantum=time_quantum)
    if comp_data:
        cc1, cc2 = st.columns([1, 1])
        with cc1:
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True)
        with cc2:
            fig_comp = plot_cpu_comparison_bar(comp_data)
            st.pyplot(fig_comp)


# ==============================================================================
# TAB 3: MEMORY ALLOCATION & MANAGEMENT
# ==============================================================================
elif nav_choice == "💾 Memory Allocation":
    st.title("💾 Contiguous Memory Allocation Simulator")
    st.markdown("Simulates dynamic partition memory allocation with **First Fit**, **Best Fit**, and **Worst Fit**, plus automatic **Coalescing** and **Compaction**.")

    mm: MemoryManager = st.session_state.memory_manager
    stats = mm.get_stats()

    # Memory Telemetry Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total RAM", f"{stats['total_memory_kb']} KB")
    c2.metric("Used RAM", f"{stats['total_allocated_kb']} KB ({stats['utilization_pct']}%)")
    c3.metric("Free RAM", f"{stats['total_free_kb']} KB")
    c4.metric("Largest Free Hole", f"{stats['largest_free_block_kb']} KB")
    c5.metric("External Fragmentation", f"{stats['external_frag_pct']}%")

    # Visual RAM Layout Map
    st.subheader("🗺️ Physical RAM Block Layout")
    fig_m = plot_memory_map(mm)
    st.pyplot(fig_m)

    st.markdown("---")
    m_col1, m_col2 = st.columns([1, 1])

    with m_col1:
        st.subheader("📥 Allocate Process Memory")
        with st.form("mem_alloc_form"):
            alloc_pid = st.number_input("Process PID", min_value=1, max_value=999, value=10)
            alloc_name = st.text_input("Process Name", value=f"Service_PID{alloc_pid}")
            alloc_size = st.number_input("Requested Memory (KB)", min_value=10, max_value=1024, value=150)
            alloc_algo_choice = st.selectbox(
                "Allocation Policy",
                ["First Fit", "Best Fit", "Worst Fit"],
                help="First Fit: first hole that fits. Best Fit: smallest hole that fits. Worst Fit: largest hole."
            )
            submit_alloc = st.form_submit_button("Allocate Segment", use_container_width=True)
            if submit_alloc:
                algo_enum = {
                    "First Fit": AllocationAlgorithm.FIRST_FIT,
                    "Best Fit": AllocationAlgorithm.BEST_FIT,
                    "Worst Fit": AllocationAlgorithm.WORST_FIT
                }[alloc_algo_choice]

                addr = mm.allocate(int(alloc_pid), alloc_name, int(alloc_size), algo_enum)
                if addr is not None:
                    # Also register in process list if not present
                    existing = next((p for p in st.session_state.processes if p.pid == int(alloc_pid)), None)
                    if existing:
                        existing.allocated_address = addr
                        existing.allocated_size = int(alloc_size)
                    else:
                        new_p = Process(pid=int(alloc_pid), name=alloc_name, burst_time=5, memory_required=int(alloc_size))
                        new_p.state = ProcessState.READY
                        new_p.allocated_address = addr
                        st.session_state.processes.append(new_p)
                    st.success(f"Allocated {alloc_size} KB at physical address 0x{addr:04X} via {alloc_algo_choice}.")
                else:
                    st.error(f"Allocation failed! Insufficient contiguous free memory for {alloc_size} KB. Try running Memory Compaction.")
                st.rerun()

    with m_col2:
        st.subheader("📤 Free Memory & Compaction")
        active_allocs = [s for s in mm.segments if s.is_allocated and s.pid != 0]

        if active_allocs:
            dealloc_pid = st.selectbox(
                "Select Process to Deallocate",
                [s.pid for s in active_allocs],
                format_func=lambda x: f"PID {x}: {next((s.process_name for s in active_allocs if s.pid == x), '')} ({next((s.size for s in active_allocs if s.pid == x), '')} KB)"
            )
            if st.button("🗑️ Release & Coalesce Memory", use_container_width=True):
                if mm.deallocate(dealloc_pid):
                    proc = next((p for p in st.session_state.processes if p.pid == dealloc_pid), None)
                    if proc:
                        proc.allocated_address = None
                    st.success(f"Released memory for PID {dealloc_pid}. Adjacent holes coalesced.")
                    st.rerun()
        else:
            st.info("No user processes currently allocated in memory.")

        st.markdown("---")
        st.write("**Defragmentation (Compaction):**")
        st.caption("Consolidates all fragmented free holes into one single large free block at the end of memory.")
        if st.button("🧩 Defragment / Compact Memory", use_container_width=True):
            moved = mm.compact()
            st.success(f"Memory compaction finished! {moved} blocks shifted. External fragmentation eliminated.")
            st.rerun()

    st.markdown("---")
    st.subheader("📑 Physical Memory Partition Table")
    seg_data = [s.to_dict() for s in mm.segments]
    st.dataframe(pd.DataFrame(seg_data), use_container_width=True)


# ==============================================================================
# TAB 4: DISK SCHEDULING (FCFS & SSTF)
# ==============================================================================
elif nav_choice == "💽 Disk Scheduling":
    st.title("💽 Disk Arm Scheduling Simulator")
    st.markdown("Simulate and compare disk arm movement algorithms: **FCFS (First-Come First-Served)** and **SSTF (Shortest Seek Time First)**.")

    d_col1, d_col2 = st.columns([1, 2])
    with d_col1:
        st.subheader("⚙️ Disk Parameters")
        init_head = st.number_input("Initial Head Position", min_value=0, max_value=499, value=st.session_state.disk_head)
        cylinders = st.number_input("Total Cylinders / Tracks", min_value=100, max_value=1000, value=200)

        req_str = st.text_input(
            "Track Request Queue (comma separated)",
            value=", ".join(map(str, st.session_state.disk_requests))
        )

        if st.button("🚀 Calculate Seek Trajectories", use_container_width=True):
            try:
                parsed_reqs = [int(x.strip()) for x in req_str.split(",") if x.strip()]
                st.session_state.disk_requests = parsed_reqs
                st.session_state.disk_head = int(init_head)
                st.session_state.disk_result_fcfs = schedule_disk_fcfs(int(init_head), parsed_reqs, int(cylinders))
                st.session_state.disk_result_sstf = schedule_disk_sstf(int(init_head), parsed_reqs, int(cylinders))
                st.success("Calculated disk trajectories!")
            except Exception as e:
                st.error(f"Error parsing requests: {e}")

    res_fcfs = st.session_state.disk_result_fcfs
    res_sstf = st.session_state.disk_result_sstf

    with d_col2:
        st.subheader("📊 Comparative Seek Telemetry")
        diff_seek = res_fcfs.total_seek_operations - res_sstf.total_seek_operations
        pct_savings = (diff_seek / res_fcfs.total_seek_operations * 100) if res_fcfs.total_seek_operations > 0 else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("FCFS Total Head Moves", f"{res_fcfs.total_seek_operations} cyl", f"Avg: {res_fcfs.average_seek_distance:.1f}")
        m2.metric("SSTF Total Head Moves", f"{res_sstf.total_seek_operations} cyl", f"Avg: {res_sstf.average_seek_distance:.1f}")
        m3.metric("SSTF Efficiency Gain", f"{pct_savings:.1f}% reduction", f"-{diff_seek} seeks")

    st.markdown("---")
    st.subheader("📈 Disk Arm Trajectory Chart (Track vs Service Order)")
    st.caption("Shows head position over each sequential service step. SSTF minimizes erratic head jumps across the disk platter.")

    fig_disk = plot_disk_trajectory(res_fcfs, res_sstf)
    st.pyplot(fig_disk)

    # Step-by-step movement table
    st.markdown("---")
    st.subheader("📋 Step-by-Step Movement Breakdown")
    t1, t2 = st.columns(2)
    with t1:
        st.write("**FCFS Step Trajectory:**")
        st.dataframe(pd.DataFrame(res_fcfs.step_table()), use_container_width=True)
    with t2:
        st.write("**SSTF Step Trajectory:**")
        st.dataframe(pd.DataFrame(res_sstf.step_table()), use_container_width=True)


# ==============================================================================
# TAB 5: BASH SHELL TERMINAL
# ==============================================================================
elif nav_choice == "💻 Bash Shell Terminal":
    st.title("💻 OS Resource Manager Shell (Bash)")
    st.markdown("Simulated Unix/Bash terminal interface connected directly to the OS kernel simulation engine.")

    shell = ShellInterpreter(st.session_state.memory_manager, st.session_state.processes)

    # Terminal Screen
    screen_text = "\n".join(st.session_state.terminal_output)
    st.markdown(f'<div class="terminal-box">{screen_text}</div>', unsafe_allow_html=True)

    # Command Input
    st.write("")
    with st.form("shell_input_form", clear_on_submit=True):
        cmd_col1, cmd_col2 = st.columns([5, 1])
        with cmd_col1:
            cmd_text = st.text_input("Enter Bash Command", placeholder="ps, top, create Worker 6 120, kill 2, free, df, sched rr 2, sysinfo, help...")
        with cmd_col2:
            st.write("")
            cmd_submit = st.form_submit_button("Execute", use_container_width=True)

        if cmd_submit and cmd_text:
            out = shell.execute(cmd_text)
            if out == "__CLEAR__":
                st.session_state.terminal_output = ["Terminal cleared."]
            else:
                st.session_state.terminal_output.append(f"$ {cmd_text}")
                st.session_state.terminal_output.append(out)
                st.session_state.terminal_output.append("")
            st.rerun()

    # Helpful Command Quick-Pills
    st.caption("Quick command examples: click to populate or test:")
    qp_col1, qp_col2, qp_col3, qp_col4, qp_col5 = st.columns(5)
    with qp_col1:
        if st.button("`ps` (List PCB)", use_container_width=True):
            st.session_state.terminal_output.append("$ ps")
            st.session_state.terminal_output.append(shell.execute("ps"))
            st.rerun()
    with qp_col2:
        if st.button("`top` (Load)", use_container_width=True):
            st.session_state.terminal_output.append("$ top")
            st.session_state.terminal_output.append(shell.execute("top"))
            st.rerun()
    with qp_col3:
        if st.button("`free` (RAM)", use_container_width=True):
            st.session_state.terminal_output.append("$ free")
            st.session_state.terminal_output.append(shell.execute("free"))
            st.rerun()
    with qp_col4:
        if st.button("`sched rr 3`", use_container_width=True):
            st.session_state.terminal_output.append("$ sched rr 3")
            st.session_state.terminal_output.append(shell.execute("sched rr 3"))
            st.rerun()
    with qp_col5:
        if st.button("`sysinfo`", use_container_width=True):
            st.session_state.terminal_output.append("$ sysinfo")
            st.session_state.terminal_output.append(shell.execute("sysinfo"))
            st.rerun()


# ==============================================================================
# TAB 6: ANALYTICAL REPORTS & EXPORTS
# ==============================================================================
elif nav_choice == "📈 Analytical Reports":
    st.title("📈 OS Performance Analytics & Export Suite")
    st.markdown("Comprehensive evaluation reports, trade-off analysis, and exportable datasets for operating system benchmarks.")

    # Export Buttons
    report_md = generate_analytical_markdown_report(
        st.session_state.cpu_result,
        st.session_state.memory_manager,
        st.session_state.disk_result_sstf
    )
    csv_data = export_processes_csv(st.session_state.processes)

    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        st.download_button(
            label="📥 Download Full Analytical Report (.md)",
            data=report_md,
            file_name=f"OS_Resource_Manager_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with exp_col2:
        st.download_button(
            label="📥 Download Process Telemetry Data (.csv)",
            data=csv_data,
            file_name=f"OS_Processes_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown("---")
    st.subheader("📑 Analytical Report Preview")
    st.markdown(report_md)
