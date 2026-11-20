#!/usr/bin/env bash
# ==============================================================================
# OS Resource Manager - Process Management & Lifecycle Simulator (Bash)
# Demonstrates process creation (fork/exec), backgrounding, pausing, and termination.
# ==============================================================================

echo "=== OS Process Management Lifecycle Script ==="

# Trap cleanup on script termination
cleanup() {
    echo -e "\n[*] Interrupt received. Terminating all spawned background child processes..."
    if [ -n "$PID1" ] && kill -0 "$PID1" 2>/dev/null; then kill -9 "$PID1"; fi
    if [ -n "$PID2" ] && kill -0 "$PID2" 2>/dev/null; then kill -9 "$PID2"; fi
    if [ -n "$PID3" ] && kill -0 "$PID3" 2>/dev/null; then kill -9 "$PID3"; fi
    echo "[*] Cleaned up child processes. Exiting."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 1. Spawn Child Process 1 (Simulated CPU-intensive worker)
echo "[+] Creating Child Process 1 (Worker_Alpha)..."
(
    while true; do
        sleep 1
    done
) &
PID1=$!
echo "    -> Worker_Alpha spawned with PID: $PID1 (State: RUNNING)"

# 2. Spawn Child Process 2 (Simulated I/O-bound worker)
echo "[+] Creating Child Process 2 (Worker_Beta)..."
(
    while true; do
        sleep 2
    done
) &
PID2=$!
echo "    -> Worker_Beta spawned with PID: $PID2 (State: RUNNING)"

# 3. Spawn Child Process 3 (Simulated Memory worker)
echo "[+] Creating Child Process 3 (Worker_Gamma)..."
(
    while true; do
        sleep 3
    done
) &
PID3=$!
echo "    -> Worker_Gamma spawned with PID: $PID3 (State: RUNNING)"

# Display active processes
echo -e "\n[+] Current Active Process Table (ps):"
ps -p "$PID1,$PID2,$PID3" -o pid,stat,time,command 2>/dev/null || ps aux | grep -E "$PID1|$PID2|$PID3" | grep -v grep

# Demonstrate Process Pausing (SIGSTOP)
echo -e "\n[+] Sending SIGSTOP (Pause) to Worker_Alpha (PID: $PID1)..."
kill -STOP "$PID1" 2>/dev/null && echo "    -> Worker_Alpha is now PAUSED (WAITING state)"

sleep 1

# Demonstrate Process Resuming (SIGCONT)
echo -e "\n[+] Sending SIGCONT (Resume) to Worker_Alpha (PID: $PID1)..."
kill -CONT "$PID1" 2>/dev/null && echo "    -> Worker_Alpha is now RESUMED (READY/RUNNING state)"

sleep 1

# Demonstrate Process Termination (SIGTERM / SIGKILL)
echo -e "\n[+] Terminating Worker_Beta (PID: $PID2) via SIGTERM..."
kill -TERM "$PID2" 2>/dev/null
wait "$PID2" 2>/dev/null
echo "    -> Worker_Beta TERMINATED successfully."

echo -e "\n[+] Demonstration completed successfully."
