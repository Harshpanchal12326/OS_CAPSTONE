"""
CLI Interactive Mode for OS Resource Manager Simulator.
Allows running the simulator directly in any terminal (PowerShell, Bash, Command Prompt)
without requiring a browser or external GUI packages.
"""

import sys
from core.pcb import Process, ProcessState
from core.cpu_scheduler import schedule_fcfs, schedule_sjf, schedule_round_robin
from core.memory_manager import MemoryManager, AllocationAlgorithm
from core.disk_scheduler import schedule_disk_fcfs, schedule_disk_sstf
from core.metrics import compare_cpu_algorithms, compare_disk_algorithms, generate_analytical_markdown_report
from core.shell_interpreter import ShellInterpreter


def print_banner():
    print("""
======================================================================
           OS RESOURCE MANAGER SIMULATOR - INTERACTIVE CLI            
======================================================================
  * CPU Scheduling: FCFS, SJF (Preemptive/Non-preemptive), Round Robin
  * Memory Allocation: First Fit, Best Fit, Worst Fit, Compaction
  * Disk Scheduling: FCFS and SSTF head movement simulation
  * Interactive Unix/Bash Terminal: ps, top, create, kill, free, df
======================================================================
""")


def main():
    print_banner()

    # Initialize MMU & Processes
    mm = MemoryManager(total_memory_kb=1024, os_reserved_kb=128)
    processes = [
        Process(pid=1, name="Web_Server", burst_time=6, arrival_time=0, memory_required=160, priority=2),
        Process(pid=2, name="Database_Query", burst_time=8, arrival_time=1, memory_required=220, priority=1),
        Process(pid=3, name="UI_Compositor", burst_time=4, arrival_time=2, memory_required=120, priority=3),
        Process(pid=4, name="Cache_Worker", burst_time=3, arrival_time=4, memory_required=80, priority=2),
        Process(pid=5, name="Log_Flusher", burst_time=5, arrival_time=5, memory_required=140, priority=4)
    ]

    for p in processes:
        p.state = ProcessState.READY
        addr = mm.allocate(p.pid, p.name, p.memory_required, AllocationAlgorithm.FIRST_FIT)
        if addr is not None:
            p.allocated_address = addr
            p.allocated_size = p.memory_required

    shell = ShellInterpreter(mm, processes)

    print("[+] Simulator initialized with 5 benchmark processes.")
    print("[+] Type 'help' to see available shell commands, or 'exit' / 'quit' to stop.\n")

    while True:
        try:
            cmd = input("os-manager$ ").strip()
            if not cmd:
                continue
            if cmd.lower() in ["exit", "quit", "q"]:
                print("[*] Exiting OS Resource Manager Simulator. Goodbye!")
                break
            elif cmd.lower() == "report":
                cpu_res = schedule_fcfs(processes)
                disk_res = schedule_disk_sstf(53, [98, 183, 37, 122, 14, 124, 65, 67])
                print(generate_analytical_markdown_report(cpu_res, mm, disk_res))
            else:
                output = shell.execute(cmd)
                if output == "__CLEAR__":
                    print("\n" * 40)
                else:
                    print(output)
            print()
        except (KeyboardInterrupt, EOFError):
            print("\n[*] Exiting.")
            break


if __name__ == "__main__":
    main()
