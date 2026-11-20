#!/usr/bin/env bash
# ==============================================================================
# OS Resource Manager - Automated Benchmark Suite
# Runs automated testing for CPU scheduling, Memory allocation, and Disk seek.
# ==============================================================================

echo "======================================================================"
echo "          OS RESOURCE MANAGER - AUTOMATED SIMULATION BENCHMARK        "
echo "======================================================================"

python3 -c "
from core.pcb import Process
from core.cpu_scheduler import schedule_fcfs, schedule_sjf, schedule_round_robin
from core.memory_manager import MemoryManager, AllocationAlgorithm
from core.disk_scheduler import schedule_disk_fcfs, schedule_disk_sstf
from core.metrics import compare_cpu_algorithms, compare_disk_algorithms

print('\n--- [1] BENCHMARKING CPU SCHEDULING ALGORITHMS ---')
sample_procs = [
    Process(pid=1, name='Kernel_Worker', burst_time=6, arrival_time=0),
    Process(pid=2, name='DB_Daemon', burst_time=8, arrival_time=1),
    Process(pid=3, name='UI_Renderer', burst_time=7, arrival_time=2),
    Process(pid=4, name='Log_Collector', burst_time=3, arrival_time=3),
]

cpu_comparison = compare_cpu_algorithms(sample_procs, rr_quantum=2)
for row in cpu_comparison:
    print(f\"{row['Algorithm']:<28} | Avg WT: {row['Avg Waiting Time']:<5} | Avg TAT: {row['Avg Turnaround Time']:<5} | CPU Util: {row['CPU Utilization (%)']}%\")

print('\n--- [2] BENCHMARKING MEMORY ALLOCATION (FIRST vs BEST vs WORST) ---')
for algo in [AllocationAlgorithm.FIRST_FIT, AllocationAlgorithm.BEST_FIT, AllocationAlgorithm.WORST_FIT]:
    mm = MemoryManager(total_memory_kb=1024, os_reserved_kb=128)
    mm.allocate(1, 'Proc_A', 150, algo)
    mm.allocate(2, 'Proc_B', 300, algo)
    mm.allocate(3, 'Proc_C', 200, algo)
    mm.deallocate(2) # Create a hole in the middle
    mm.allocate(4, 'Proc_D', 180, algo)
    stats = mm.get_stats()
    print(f\"{algo.value:<12} | Util: {stats['utilization_pct']}% | Largest Hole: {stats['largest_free_block_kb']} KB | Frag: {stats['external_frag_pct']}%\")

print('\n--- [3] BENCHMARKING DISK SEEK (FCFS vs SSTF) ---')
reqs = [98, 183, 37, 122, 14, 124, 65, 67]
head = 53
disk_comparison = compare_disk_algorithms(head, reqs)
for row in disk_comparison:
    print(f\"{row['Algorithm']:<8} | Total Head Movements: {row['Total Head Movements']:<4} | Avg Seek: {row['Average Seek Distance']:<5} | Seek Reduction: {row['Seek Reduction vs FCFS (%)']}\")
" 2>/dev/null || python -c "
from core.pcb import Process
from core.cpu_scheduler import schedule_fcfs, schedule_sjf, schedule_round_robin
from core.memory_manager import MemoryManager, AllocationAlgorithm
from core.disk_scheduler import schedule_disk_fcfs, schedule_disk_sstf
from core.metrics import compare_cpu_algorithms, compare_disk_algorithms

print('\n--- [1] BENCHMARKING CPU SCHEDULING ALGORITHMS ---')
sample_procs = [
    Process(pid=1, name='Kernel_Worker', burst_time=6, arrival_time=0),
    Process(pid=2, name='DB_Daemon', burst_time=8, arrival_time=1),
    Process(pid=3, name='UI_Renderer', burst_time=7, arrival_time=2),
    Process(pid=4, name='Log_Collector', burst_time=3, arrival_time=3),
]

cpu_comparison = compare_cpu_algorithms(sample_procs, rr_quantum=2)
for row in cpu_comparison:
    print(f\"{row['Algorithm']:<28} | Avg WT: {row['Avg Waiting Time']:<5} | Avg TAT: {row['Avg Turnaround Time']:<5} | CPU Util: {row['CPU Utilization (%)']}%\")

print('\n--- [2] BENCHMARKING MEMORY ALLOCATION ---')
for algo in [AllocationAlgorithm.FIRST_FIT, AllocationAlgorithm.BEST_FIT, AllocationAlgorithm.WORST_FIT]:
    mm = MemoryManager(total_memory_kb=1024, os_reserved_kb=128)
    mm.allocate(1, 'Proc_A', 150, algo)
    mm.allocate(2, 'Proc_B', 300, algo)
    mm.allocate(3, 'Proc_C', 200, algo)
    mm.deallocate(2)
    mm.allocate(4, 'Proc_D', 180, algo)
    stats = mm.get_stats()
    print(f\"{algo.value:<12} | Util: {stats['utilization_pct']}% | Largest Hole: {stats['largest_free_block_kb']} KB | Frag: {stats['external_frag_pct']}%\")

print('\n--- [3] BENCHMARKING DISK SEEK (FCFS vs SSTF) ---')
reqs = [98, 183, 37, 122, 14, 124, 65, 67]
head = 53
disk_comparison = compare_disk_algorithms(head, reqs)
for row in disk_comparison:
    print(f\"{row['Algorithm']:<8} | Total Head Movements: {row['Total Head Movements']:<4} | Avg Seek: {row['Average Seek Distance']:<5} | Seek Reduction: {row['Seek Reduction vs FCFS (%)']}\")
"
echo -e "\n======================================================================"
echo "Benchmark completed."
