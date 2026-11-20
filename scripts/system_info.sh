#!/usr/bin/env bash
# ==============================================================================
# OS Resource Manager - System Information Utility (Bash)
# Queries and displays operating system specifications, CPU, and memory stats.
# ==============================================================================

echo "======================================================================"
echo "                  OS RESOURCE MANAGER - SYSTEM INFO                   "
echo "======================================================================"

# Kernel & Host Architecture
echo -e "\n[+] SYSTEM ARCHITECTURE & KERNEL:"
if command -v uname &> /dev/null; then
    echo "  Kernel Name     : $(uname -s)"
    echo "  Node Name       : $(uname -n)"
    echo "  Kernel Release  : $(uname -r)"
    echo "  Kernel Version  : $(uname -v)"
    echo "  Machine / Arch  : $(uname -m)"
else
    echo "  OS Platform     : Windows $(cmd.exe /c ver 2>&1)"
fi

# CPU Telemetry
echo -e "\n[+] CPU TELEMETRY:"
if [ -f /proc/cpuinfo ]; then
    MODEL=$(grep -m1 "model name" /proc/cpuinfo | cut -d: -f2 | xargs)
    CORES=$(grep -c "^processor" /proc/cpuinfo)
    echo "  CPU Model       : $MODEL"
    echo "  Logical Cores   : $CORES"
elif command -v wmic &> /dev/null; then
    echo "  CPU Name        : $(wmic cpu get name /format:value | grep -v '^$' | cut -d= -f2)"
    echo "  Cores/Threads   : $(wmic cpu get NumberOfCores,NumberOfLogicalProcessors /format:value | grep -v '^$' | tr '\n' ' ')"
fi

# Memory Telemetry
echo -e "\n[+] PHYSICAL & VIRTUAL MEMORY:"
if command -v free &> /dev/null; then
    free -h
elif [ -f /proc/meminfo ]; then
    grep -E "MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree" /proc/meminfo
fi

# Disk Usage
echo -e "\n[+] DISK STORAGE / PARTITIONS:"
if command -v df &> /dev/null; then
    df -h . 2>/dev/null || df -h
fi

# Uptime
echo -e "\n[+] SYSTEM UPTIME & LOAD:"
uptime 2>/dev/null || date

echo "======================================================================"
