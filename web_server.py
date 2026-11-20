"""
Zero-Dependency Web Server Dashboard for OS Resource Manager Simulator.
Runs with Python's built-in standard library (http.server).
Serves an interactive Web UI with HTML5 Canvas Gantt charts, Memory maps,
Disk seek plots, and an interactive Bash shell connected via REST API.
"""

import http.server
import socketserver
import json
import urllib.parse
import sys
import os

from core.pcb import Process, ProcessState
from core.cpu_scheduler import schedule_fcfs, schedule_sjf, schedule_round_robin
from core.memory_manager import MemoryManager, AllocationAlgorithm
from core.disk_scheduler import schedule_disk_fcfs, schedule_disk_sstf, schedule_disk_scan
from core.metrics import compare_cpu_algorithms, compare_disk_algorithms, generate_analytical_markdown_report, export_processes_csv
from core.shell_interpreter import ShellInterpreter

# Global OS Simulator State
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

disk_requests = [98, 183, 37, 122, 14, 124, 65, 67]
disk_head = 53
shell = ShellInterpreter(mm, processes)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OS Resource Manager Simulator</title>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --green: #22c55e;
      --red: #ef4444;
      --amber: #f59e0b;
      --blue: #3b82f6;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      display: flex;
      min-height: 100vh;
    }
    .sidebar {
      width: 260px;
      background: #090d16;
      border-right: 1px solid var(--border);
      padding: 24px 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .sidebar h2 { font-size: 1.1rem; color: var(--accent); margin-bottom: 4px; display: flex; align-items: center; gap: 8px; }
    .sidebar p { font-size: 0.8rem; color: var(--muted); margin-bottom: 16px; }
    .nav-btn {
      background: transparent;
      border: 1px solid transparent;
      color: var(--muted);
      padding: 10px 14px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.9rem;
      text-align: left;
      transition: all 0.2s;
    }
    .nav-btn:hover { background: var(--card); color: var(--text); }
    .nav-btn.active { background: var(--card); color: var(--accent); border-color: var(--border); font-weight: 600; }
    .main {
      flex: 1;
      padding: 28px 36px;
      overflow-y: auto;
    }
    .header {
      margin-bottom: 24px;
    }
    .header h1 { font-size: 1.7rem; font-weight: 700; margin-bottom: 6px; }
    .header p { color: var(--muted); font-size: 0.95rem; }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .kpi-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px;
    }
    .kpi-label { font-size: 0.8rem; text-transform: uppercase; color: var(--muted); letter-spacing: 0.05em; margin-bottom: 6px; }
    .kpi-val { font-size: 1.6rem; font-weight: 700; color: var(--accent); }
    .kpi-sub { font-size: 0.8rem; color: var(--muted); margin-top: 4px; }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .card h3 { font-size: 1.15rem; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.88rem; }
    th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }
    th { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; }
    .badge { padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
    .badge-ready { background: #0369a1; color: white; }
    .badge-running { background: #15803d; color: white; }
    .badge-waiting { background: #b45309; color: white; }
    .badge-term { background: #b91c1c; color: white; }
    .btn {
      background: #0284c7;
      color: white;
      border: none;
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 0.88rem;
      cursor: pointer;
      font-weight: 500;
      transition: background 0.15s;
    }
    .btn:hover { background: #0369a1; }
    .btn-secondary { background: #334155; }
    .btn-secondary:hover { background: #475569; }
    .btn-danger { background: #dc2626; }
    .btn-danger:hover { background: #b91c1c; }
    .btn-success { background: #16a34a; }
    .btn-success:hover { background: #15803d; }
    .form-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }
    input, select {
      background: #090d16;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.88rem;
    }
    .terminal-window {
      background: #090d16;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-family: 'Courier New', monospace;
      color: #38bdf8;
      padding: 16px;
      height: 380px;
      overflow-y: auto;
      white-space: pre-wrap;
      font-size: 0.88rem;
      line-height: 1.4;
    }
    canvas { width: 100%; border-radius: 8px; background: #090d16; border: 1px solid var(--border); }
  </style>
</head>
<body>
  <div class="sidebar">
    <h2>🖥️ OS Manager</h2>
    <p>Operating System Resource Simulator</p>
    <button class="nav-btn active" onclick="showTab('dashboard')">📊 Dashboard Overview</button>
    <button class="nav-btn" onclick="showTab('cpu')">⚡ CPU Scheduling</button>
    <button class="nav-btn" onclick="showTab('memory')">💾 Memory Allocation</button>
    <button class="nav-btn" onclick="showTab('disk')">💽 Disk Scheduling</button>
    <button class="nav-btn" onclick="showTab('terminal')">💻 Bash Shell Terminal</button>
    <button class="nav-btn" onclick="showTab('reports')">📈 Analytical Reports</button>
    <hr style="border: 0; border-top: 1px solid var(--border); margin: 12px 0;">
    <button class="btn btn-secondary" onclick="loadScenario('Balanced Workload')">Load Balanced Workload</button>
    <button class="btn btn-secondary" onclick="loadScenario('Memory Fragmentation')">Load Frag Scenario</button>
    <button class="btn btn-danger" style="margin-top:auto;" onclick="resetSimulator()">🔄 Reset System</button>
  </div>

  <div class="main">
    <!-- DASHBOARD VIEW -->
    <div id="view-dashboard">
      <div class="header">
        <h1>Operating System Resource Manager</h1>
        <p>Live simulation of CPU Scheduling, Contiguous Memory Management, Process Control Blocks, and Disk Arm Mechanics.</p>
      </div>

      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">CPU Utilization</div>
          <div class="kpi-val" id="kpi-cpu-util">100.0%</div>
          <div class="kpi-sub" id="kpi-cpu-algo">FCFS</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Memory Utilization</div>
          <div class="kpi-val" id="kpi-mem-util">82.8%</div>
          <div class="kpi-sub" id="kpi-mem-detail">848 / 1024 KB</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Avg Waiting Time</div>
          <div class="kpi-val" id="kpi-avg-wt">10.6 <span style="font-size:1rem;">units</span></div>
          <div class="kpi-sub" id="kpi-avg-tat">Avg TAT: 15.8 units</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Active Processes</div>
          <div class="kpi-val" id="kpi-active-procs">5 <span style="font-size:1rem;">/ 5</span></div>
          <div class="kpi-sub" id="kpi-frag">Ext Frag: 0.0%</div>
        </div>
      </div>

      <div class="card">
        <h3>⚡ CPU Execution Timeline (Gantt Chart)</h3>
        <canvas id="canvas-gantt" width="900" height="120"></canvas>
      </div>

      <div class="card">
        <h3>💾 Physical RAM Allocation Map (Contiguous Partitions)</h3>
        <canvas id="canvas-mem" width="900" height="90"></canvas>
      </div>

      <div class="card">
        <h3>📋 Process Control Block (PCB) Table</h3>
        <div class="form-row">
          <input type="text" id="new-name" placeholder="Name" value="Worker">
          <input type="number" id="new-burst" placeholder="Burst" value="5" style="width:90px;">
          <input type="number" id="new-mem" placeholder="Mem (KB)" value="120" style="width:110px;">
          <input type="number" id="new-arr" placeholder="Arrival" value="0" style="width:90px;">
          <select id="new-algo">
            <option value="First Fit">First Fit</option>
            <option value="Best Fit">Best Fit</option>
            <option value="Worst Fit">Worst Fit</option>
          </select>
          <button class="btn btn-success" onclick="spawnProcess()">➕ Spawn Process</button>
        </div>
        <table>
          <thead>
            <tr>
              <th>PID</th>
              <th>Name</th>
              <th>State</th>
              <th>Arrival</th>
              <th>Burst</th>
              <th>Remaining</th>
              <th>Memory</th>
              <th>Base Addr</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="table-procs-body"></tbody>
        </table>
      </div>
    </div>

    <!-- CPU SCHEDULING VIEW -->
    <div id="view-cpu" style="display:none;">
      <div class="header">
        <h1>CPU Scheduling Algorithms</h1>
        <p>Benchmark FCFS, Shortest Job First (Non-preemptive & Preemptive/SRTF), and Round Robin.</p>
      </div>
      <div class="card">
        <h3>⚡ Scheduler Settings</h3>
        <div class="form-row">
          <select id="cpu-algo-sel" onchange="toggleRRInput()">
            <option value="fcfs">First-Come, First-Served (FCFS)</option>
            <option value="sjf-np">Shortest Job First (Non-Preemptive)</option>
            <option value="sjf-p">Shortest Job First (Preemptive / SRTF)</option>
            <option value="rr">Round Robin (RR)</option>
          </select>
          <span id="rr-quantum-span" style="display:none;">
            Quantum: <input type="number" id="cpu-quantum" value="2" min="1" max="10" style="width:70px;">
          </span>
          <button class="btn" onclick="runCPUScheduler()">🚀 Run Algorithm</button>
        </div>
        <canvas id="canvas-cpu-gantt" width="900" height="120"></canvas>
      </div>

      <div class="card">
        <h3>📊 Comparative Benchmark (Identical Workload)</h3>
        <table>
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>Avg Waiting Time</th>
              <th>Avg Turnaround Time</th>
              <th>Avg Response Time</th>
              <th>CPU Utilization</th>
              <th>Throughput</th>
            </tr>
          </thead>
          <tbody id="table-cpu-comp-body"></tbody>
        </table>
      </div>
    </div>

    <!-- MEMORY ALLOCATION VIEW -->
    <div id="view-memory" style="display:none;">
      <div class="header">
        <h1>Contiguous Memory Management Unit</h1>
        <p>Simulates First Fit, Best Fit, and Worst Fit allocation policies with Coalescing and Compaction.</p>
      </div>
      <div class="card">
        <h3>🗺️ Memory Block Map</h3>
        <canvas id="canvas-mem-detail" width="900" height="100"></canvas>
        <div style="margin-top:14px; display:flex; gap:12px;">
          <button class="btn btn-secondary" onclick="compactMemory()">🧩 Defragment / Compact Memory</button>
        </div>
      </div>
      <div class="card">
        <h3>📑 Memory Segments Table</h3>
        <table>
          <thead>
            <tr>
              <th>Base Address</th>
              <th>End Address</th>
              <th>Size</th>
              <th>Status</th>
              <th>PID</th>
              <th>Process</th>
            </tr>
          </thead>
          <tbody id="table-mem-body"></tbody>
        </table>
      </div>
    </div>

    <!-- DISK SCHEDULING VIEW -->
    <div id="view-disk" style="display:none;">
      <div class="header">
        <h1>Disk Head Scheduling (FCFS & SSTF)</h1>
        <p>Calculates head seek sequences and movement distances for disk drive requests.</p>
      </div>
      <div class="card">
        <h3>⚙️ Disk Head Parameters</h3>
        <div class="form-row">
          Initial Head: <input type="number" id="disk-init-head" value="53" style="width:90px;">
          Requests: <input type="text" id="disk-req-queue" value="98, 183, 37, 122, 14, 124, 65, 67" style="width:300px;">
          <button class="btn" onclick="runDiskScheduler()">🚀 Simulate Disk Arm</button>
        </div>
        <canvas id="canvas-disk" width="900" height="280"></canvas>
      </div>
      <div class="card">
        <h3>📊 FCFS vs SSTF Comparison</h3>
        <table>
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>Total Head Movements</th>
              <th>Avg Seek Distance</th>
              <th>Seek Reduction vs FCFS</th>
            </tr>
          </thead>
          <tbody id="table-disk-comp-body"></tbody>
        </table>
      </div>
    </div>

    <!-- TERMINAL VIEW -->
    <div id="view-terminal" style="display:none;">
      <div class="header">
        <h1>Unix / Bash Shell Terminal</h1>
        <p>Execute real-time commands against the OS resource simulation kernel.</p>
      </div>
      <div class="card">
        <div class="terminal-window" id="term-screen">OS Resource Manager Shell v2.4&#10;Type 'help' for commands (ps, top, create, kill, pause, resume, free, df, sched, compact, sysinfo)...&#10;</div>
        <div class="form-row" style="margin-top:14px; margin-bottom:0;">
          <input type="text" id="term-input" placeholder="Enter shell command (e.g. ps, top, create Worker 5 120, sched rr 2)..." style="flex:1;" onkeydown="if(event.key==='Enter') sendShellCommand()">
          <button class="btn" onclick="sendShellCommand()">Send</button>
        </div>
        <div style="margin-top:10px; display:flex; gap:8px;">
          <button class="btn btn-secondary" style="font-size:0.75rem;" onclick="runQuickCmd('ps')">ps</button>
          <button class="btn btn-secondary" style="font-size:0.75rem;" onclick="runQuickCmd('top')">top</button>
          <button class="btn btn-secondary" style="font-size:0.75rem;" onclick="runQuickCmd('free')">free</button>
          <button class="btn btn-secondary" style="font-size:0.75rem;" onclick="runQuickCmd('df')">df</button>
          <button class="btn btn-secondary" style="font-size:0.75rem;" onclick="runQuickCmd('sched rr 2')">sched rr 2</button>
          <button class="btn btn-secondary" style="font-size:0.75rem;" onclick="runQuickCmd('sysinfo')">sysinfo</button>
        </div>
      </div>
    </div>

    <!-- REPORTS VIEW -->
    <div id="view-reports" style="display:none;">
      <div class="header">
        <h1>Analytical Performance Reports</h1>
        <p>Export evaluation telemetry, process execution tables, and summary markdown.</p>
      </div>
      <div class="card">
        <div style="display:flex; gap:12px; margin-bottom:16px;">
          <button class="btn" onclick="downloadReport('md')">📥 Download Markdown Report</button>
          <button class="btn btn-secondary" onclick="downloadReport('csv')">📥 Download CSV Telemetry</button>
        </div>
        <div style="background:#090d16; border:1px solid var(--border); padding:20px; border-radius:8px; font-family:monospace; white-space:pre-wrap; max-height:500px; overflow-y:auto;" id="report-text">Loading report...</div>
      </div>
    </div>
  </div>

  <script>
    let globalState = {};

    const PALETTE = ["#38bdf8", "#f43f5e", "#22c55e", "#fbbf24", "#a855f7", "#06b6d4", "#f97316", "#64748b"];

    function showTab(tabId) {
      document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
      event.target.classList.add("active");
      ["dashboard", "cpu", "memory", "disk", "terminal", "reports"].forEach(t => {
        document.getElementById("view-" + t).style.display = (t === tabId) ? "block" : "none";
      });
      if(tabId === 'cpu') runCPUScheduler();
      if(tabId === 'disk') runDiskScheduler();
      if(tabId === 'reports') fetchReport();
    }

    function toggleRRInput() {
      const val = document.getElementById("cpu-algo-sel").value;
      document.getElementById("rr-quantum-span").style.display = (val === "rr") ? "inline" : "none";
    }

    async function fetchState() {
      const res = await fetch("/api/state");
      globalState = await res.json();
      renderDashboard();
    }

    function renderDashboard() {
      const s = globalState;
      if(!s.cpu) return;

      document.getElementById("kpi-cpu-util").textContent = s.cpu.cpu_utilization.toFixed(1) + "%";
      document.getElementById("kpi-cpu-algo").textContent = "Algorithm: " + s.cpu.algorithm.split(" ")[0];
      document.getElementById("kpi-mem-util").textContent = s.memory.stats.utilization_pct + "%";
      document.getElementById("kpi-mem-detail").textContent = s.memory.stats.total_allocated_kb + " / " + s.memory.stats.total_memory_kb + " KB";
      document.getElementById("kpi-avg-wt").innerHTML = s.cpu.avg_waiting_time.toFixed(1) + ' <span style="font-size:1rem;">units</span>';
      document.getElementById("kpi-avg-tat").textContent = "Avg TAT: " + s.cpu.avg_turnaround_time.toFixed(1) + " units";

      const active = s.processes.filter(p => p.State !== "TERMINATED").length;
      document.getElementById("kpi-active-procs").innerHTML = active + ' <span style="font-size:1rem;">/ ' + s.processes.length + '</span>';
      document.getElementById("kpi-frag").textContent = "Ext Frag: " + s.memory.stats.external_frag_pct + "%";

      drawGantt("canvas-gantt", s.cpu);
      drawMemory("canvas-mem", s.memory);
      drawMemory("canvas-mem-detail", s.memory);

      // Render Processes Table
      const tbody = document.getElementById("table-procs-body");
      tbody.innerHTML = "";
      s.processes.forEach(p => {
        const tr = document.createElement("tr");
        let badgeClass = "badge-ready";
        if(p.State === "RUNNING") badgeClass = "badge-running";
        if(p.State === "WAITING") badgeClass = "badge-waiting";
        if(p.State === "TERMINATED") badgeClass = "badge-term";

        tr.innerHTML = `
          <td><strong>${p.PID}</strong></td>
          <td>${p.Name}</td>
          <td><span class="badge ${badgeClass}">${p.State}</span></td>
          <td>${p["Arrival Time (AT)"]}</td>
          <td>${p["Burst Time (BT)"]}</td>
          <td>${p["Remaining Time"]}</td>
          <td>${p["Memory (KB)"]} KB</td>
          <td><code>${p["Allocated Base Addr"]}</code></td>
          <td>
            <button class="btn btn-secondary" style="padding:3px 8px; font-size:0.75rem;" onclick="pauseProc(${p.PID})">⏸</button>
            <button class="btn btn-secondary" style="padding:3px 8px; font-size:0.75rem;" onclick="resumeProc(${p.PID})">▶</button>
            <button class="btn btn-danger" style="padding:3px 8px; font-size:0.75rem;" onclick="killProc(${p.PID})">🛑</button>
          </td>
        `;
        tbody.appendChild(tr);
      });

      // Render Memory Segments
      const mbody = document.getElementById("table-mem-body");
      mbody.innerHTML = "";
      s.memory.segments.forEach(seg => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><code>${seg["Base Address"]}</code></td>
          <td><code>${seg["End Address"]}</code></td>
          <td>${seg["Size (KB)"]} KB</td>
          <td><span class="badge ${seg.Status === 'Allocated' ? 'badge-running' : 'badge-waiting'}">${seg.Status}</span></td>
          <td>${seg.PID}</td>
          <td>${seg.Process}</td>
        `;
        mbody.appendChild(tr);
      });
    }

    function drawGantt(canvasId, cpu) {
      const c = document.getElementById(canvasId);
      if(!c) return;
      const ctx = c.getContext("2d");
      ctx.clearRect(0, 0, c.width, c.height);

      if(!cpu.gantt || cpu.gantt.length === 0) return;
      const total = Math.max(cpu.total_time, 1);
      const margin = 20;
      const w = c.width - margin * 2;
      const h = 50;
      const y = 30;

      cpu.gantt.forEach(s => {
        const x1 = margin + (s.Start / total) * w;
        const sw = (s.Duration / total) * w;
        ctx.fillStyle = s.IsIdle ? "#64748b" : PALETTE[((s.PID || 1) - 1) % PALETTE.length];
        ctx.fillRect(x1, y, sw, h);
        ctx.strokeStyle = "#090d16";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(x1, y, sw, h);

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 11px sans-serif";
        ctx.textAlign = "center";
        if(sw > 30) {
          ctx.fillText((s.IsIdle ? "IDLE" : "P" + s.PID), x1 + sw / 2, y + 30);
        }

        ctx.fillStyle = "#94a3b8";
        ctx.font = "10px monospace";
        ctx.fillText(s.Start, x1, y + h + 18);
      });
      ctx.fillText(cpu.total_time, margin + w, y + h + 18);
    }

    function drawMemory(canvasId, mem) {
      const c = document.getElementById(canvasId);
      if(!c) return;
      const ctx = c.getContext("2d");
      ctx.clearRect(0, 0, c.width, c.height);

      const total = mem.stats.total_memory_kb;
      const margin = 20;
      const w = c.width - margin * 2;
      const h = 42;
      const y = 20;

      mem.segments.forEach((seg, idx) => {
        const base = parseInt(seg["Base Address"].split(" ")[1].replace("(", ""));
        const size = seg["Size (KB)"];
        const x1 = margin + (base / total) * w;
        const sw = (size / total) * w;

        if(seg.Status === "Free") {
          ctx.fillStyle = "#1e293b";
        } else if(seg.PID === 0) {
          ctx.fillStyle = "#0f766e";
        } else {
          ctx.fillStyle = PALETTE[((seg.PID || 1) - 1) % PALETTE.length];
        }

        ctx.fillRect(x1, y, sw, h);
        ctx.strokeStyle = "#090d16";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(x1, y, sw, h);

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 10px sans-serif";
        ctx.textAlign = "center";
        if(sw > 40) {
          ctx.fillText(seg.Process || "Free", x1 + sw/2, y + 26);
        }

        ctx.fillStyle = "#94a3b8";
        ctx.font = "9px monospace";
        ctx.fillText("0x" + base.toString(16).toUpperCase(), x1, y + h + 14);
      });
      ctx.fillText("0x" + total.toString(16).toUpperCase(), margin + w, y + h + 14);
    }

    async function spawnProcess() {
      const name = document.getElementById("new-name").value || "Worker";
      const burst = parseInt(document.getElementById("new-burst").value) || 5;
      const mem = parseInt(document.getElementById("new-mem").value) || 100;
      const arr = parseInt(document.getElementById("new-arr").value) || 0;
      const algo = document.getElementById("new-algo").value;

      await fetch("/api/process/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, burst, memory: mem, arrival: arr, algo })
      });
      fetchState();
    }

    async function pauseProc(pid) {
      await fetch(`/api/process/pause?pid=${pid}`, { method: "POST" });
      fetchState();
    }
    async function resumeProc(pid) {
      await fetch(`/api/process/resume?pid=${pid}`, { method: "POST" });
      fetchState();
    }
    async function killProc(pid) {
      await fetch(`/api/process/kill?pid=${pid}`, { method: "POST" });
      fetchState();
    }
    async function compactMemory() {
      await fetch("/api/memory/compact", { method: "POST" });
      fetchState();
    }

    async function runCPUScheduler() {
      const algo = document.getElementById("cpu-algo-sel").value;
      const q = parseInt(document.getElementById("cpu-quantum").value) || 2;
      const res = await fetch(`/api/cpu/run?algo=${algo}&q=${q}`, { method: "POST" });
      const data = await res.json();
      drawGantt("canvas-cpu-gantt", data.result);

      // Render comparison table
      const tbody = document.getElementById("table-cpu-comp-body");
      tbody.innerHTML = "";
      data.comparison.forEach(c => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${c.Algorithm}</strong></td>
          <td>${c["Avg Waiting Time"]}</td>
          <td>${c["Avg Turnaround Time"]}</td>
          <td>${c["Avg Response Time"]}</td>
          <td>${c["CPU Utilization (%)"]}%</td>
          <td>${c.Throughput}</td>
        `;
        tbody.appendChild(tr);
      });
      fetchState();
    }

    async function runDiskScheduler() {
      const head = parseInt(document.getElementById("disk-init-head").value) || 53;
      const reqStr = document.getElementById("disk-req-queue").value;
      const reqs = reqStr.split(",").map(x => parseInt(x.trim())).filter(x => !isNaN(x));

      const res = await fetch("/api/disk/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ head, requests: reqs })
      });
      const data = await res.json();
      drawDisk("canvas-disk", data.fcfs, data.sstf);

      const tbody = document.getElementById("table-disk-comp-body");
      tbody.innerHTML = "";
      data.comparison.forEach(c => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${c.Algorithm}</strong></td>
          <td>${c["Total Head Movements"]} cyl</td>
          <td>${c["Average Seek Distance"]} cyl</td>
          <td><span class="badge ${c["Seek Reduction vs FCFS (%)"].includes('0.0%') ? 'badge-waiting' : 'badge-running'}">${c["Seek Reduction vs FCFS (%)"]}</span></td>
        `;
        tbody.appendChild(tr);
      });
    }

    function drawDisk(canvasId, fcfs, sstf) {
      const c = document.getElementById(canvasId);
      const ctx = c.getContext("2d");
      ctx.clearRect(0, 0, c.width, c.height);

      const maxTrack = 200;
      const margin = 40;
      const w = c.width - margin * 2;
      const h = c.height - margin * 2;
      const totalSteps = Math.max(fcfs.seek_sequence.length, sstf.seek_sequence.length);

      // Draw Grid
      ctx.strokeStyle = "#1e293b";
      ctx.lineWidth = 1;
      for(let t = 0; t <= maxTrack; t += 25) {
        const x = margin + (t / maxTrack) * w;
        ctx.beginPath();
        ctx.moveTo(x, margin);
        ctx.lineTo(x, margin + h);
        ctx.stroke();
        ctx.fillStyle = "#64748b";
        ctx.font = "9px monospace";
        ctx.textAlign = "center";
        ctx.fillText(t, x, margin - 10);
      }

      function plotPath(seq, color, isDashed) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.5;
        ctx.setLineDash(isDashed ? [5, 4] : []);
        ctx.beginPath();
        seq.forEach((track, i) => {
          const x = margin + (track / maxTrack) * w;
          const y = margin + (i / (totalSteps - 1)) * h;
          if(i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.stroke();

        ctx.setLineDash([]);
        seq.forEach((track, i) => {
          const x = margin + (track / maxTrack) * w;
          const y = margin + (i / (totalSteps - 1)) * h;
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(x, y, 4, 0, Math.PI * 2);
          ctx.fill();
        });
      }

      plotPath(fcfs.seek_sequence, "#ef4444", false);
      plotPath(sstf.seek_sequence, "#22c55e", true);

      // Legend
      ctx.fillStyle = "#ef4444";
      ctx.fillText("● FCFS (Seek: " + fcfs.total_seek_operations + ")", margin + 80, margin + h + 24);
      ctx.fillStyle = "#22c55e";
      ctx.fillText("■ SSTF (Seek: " + sstf.total_seek_operations + ")", margin + 260, margin + h + 24);
    }

    async function sendShellCommand() {
      const input = document.getElementById("term-input");
      const cmd = input.value.trim();
      if(!cmd) return;
      input.value = "";

      const screen = document.getElementById("term-screen");
      screen.textContent += `\\n$ ${cmd}\\n`;

      const res = await fetch("/api/shell/exec", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cmd })
      });
      const data = await res.json();
      if(data.output === "__CLEAR__") {
        screen.textContent = "Terminal cleared.\\n";
      } else {
        screen.textContent += data.output + "\\n";
      }
      screen.scrollTop = screen.scrollHeight;
      fetchState();
    }

    function runQuickCmd(cmd) {
      document.getElementById("term-input").value = cmd;
      sendShellCommand();
    }

    async function fetchReport() {
      const res = await fetch("/api/report?format=md");
      const text = await res.text();
      document.getElementById("report-text").textContent = text;
    }

    function downloadReport(format) {
      window.open(`/api/report?format=${format}&download=1`, "_blank");
    }

    async function loadScenario(name) {
      await fetch(`/api/scenario?name=${encodeURIComponent(name)}`, { method: "POST" });
      fetchState();
    }

    async function resetSimulator() {
      await fetch("/api/reset", { method: "POST" });
      fetchState();
    }

    // Initial Load
    fetchState();
  </script>
</body>
</html>
"""


class OSManagerHTTPHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path in ["/", "/index.html"]:
            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/state":
            cpu_res = schedule_fcfs(processes)
            data = {
                "processes": [p.to_dict() for p in processes],
                "memory": {
                    "stats": mm.get_stats(),
                    "segments": [s.to_dict() for s in mm.segments]
                },
                "cpu": {
                    "algorithm": cpu_res.algorithm,
                    "total_time": cpu_res.total_time,
                    "cpu_utilization": cpu_res.cpu_utilization,
                    "avg_waiting_time": cpu_res.avg_waiting_time,
                    "avg_turnaround_time": cpu_res.avg_turnaround_time,
                    "gantt": [s.to_dict() for s in cpu_res.gantt]
                }
            }
            self._send_json(data)

        elif path == "/api/report":
            fmt = qs.get("format", ["md"])[0]
            cpu_res = schedule_fcfs(processes)
            disk_res = schedule_disk_sstf(disk_head, disk_requests)
            if fmt == "csv":
                content = export_processes_csv(processes).encode("utf-8")
                mime = "text/csv"
                fname = "OS_Processes.csv"
            else:
                content = generate_analytical_markdown_report(cpu_res, mm, disk_res).encode("utf-8")
                mime = "text/markdown"
                fname = "OS_Report.md"

            self.send_response(200)
            self.send_header("Content-Type", mime)
            if "download" in qs:
                self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len) if content_len > 0 else b"{}"
        body_json = {}
        try:
            body_json = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            pass

        if path == "/api/process/create":
            name = body_json.get("name", "Proc")
            burst = int(body_json.get("burst", 5))
            mem_size = int(body_json.get("memory", 100))
            arrival = int(body_json.get("arrival", 0))
            algo_str = body_json.get("algo", "First Fit")

            new_pid = max([p.pid for p in processes], default=0) + 1
            new_p = Process(pid=new_pid, name=name, burst_time=burst, arrival_time=arrival, memory_required=mem_size)
            new_p.state = ProcessState.READY
            processes.append(new_p)

            algo_map = {
                "First Fit": AllocationAlgorithm.FIRST_FIT,
                "Best Fit": AllocationAlgorithm.BEST_FIT,
                "Worst Fit": AllocationAlgorithm.WORST_FIT
            }
            addr = mm.allocate(new_pid, name, mem_size, algo_map.get(algo_str, AllocationAlgorithm.FIRST_FIT))
            if addr is not None:
                new_p.allocated_address = addr
                new_p.allocated_size = mem_size
            self._send_json({"success": True, "pid": new_pid, "addr": addr})

        elif path == "/api/process/pause":
            pid = int(qs.get("pid", [0])[0])
            proc = next((p for p in processes if p.pid == pid), None)
            res = proc.pause() if proc else False
            self._send_json({"success": res})

        elif path == "/api/process/resume":
            pid = int(qs.get("pid", [0])[0])
            proc = next((p for p in processes if p.pid == pid), None)
            res = proc.resume() if proc else False
            self._send_json({"success": res})

        elif path == "/api/process/kill":
            pid = int(qs.get("pid", [0])[0])
            proc = next((p for p in processes if p.pid == pid), None)
            if proc:
                proc.terminate()
            mm.deallocate(pid)
            self._send_json({"success": True})

        elif path == "/api/memory/compact":
            moved = mm.compact()
            self._send_json({"success": True, "moved": moved})

        elif path == "/api/cpu/run":
            algo = qs.get("algo", ["fcfs"])[0]
            q = int(qs.get("q", [2])[0])
            if algo == "fcfs":
                res = schedule_fcfs(processes)
            elif algo == "sjf-np":
                res = schedule_sjf(processes, preemptive=False)
            elif algo == "sjf-p":
                res = schedule_sjf(processes, preemptive=True)
            elif algo == "rr":
                res = schedule_round_robin(processes, time_quantum=q)
            else:
                res = schedule_fcfs(processes)

            comp = compare_cpu_algorithms(processes, rr_quantum=q)
            self._send_json({
                "result": {
                    "algorithm": res.algorithm,
                    "total_time": res.total_time,
                    "cpu_utilization": res.cpu_utilization,
                    "avg_waiting_time": res.avg_waiting_time,
                    "avg_turnaround_time": res.avg_turnaround_time,
                    "gantt": [s.to_dict() for s in res.gantt]
                },
                "comparison": comp
            })

        elif path == "/api/disk/run":
            head = body_json.get("head", 53)
            reqs = body_json.get("requests", [98, 183, 37, 122, 14, 124, 65, 67])
            r_fcfs = schedule_disk_fcfs(head, reqs)
            r_sstf = schedule_disk_sstf(head, reqs)
            comp = compare_disk_algorithms(head, reqs)
            self._send_json({
                "fcfs": {
                    "seek_sequence": r_fcfs.seek_sequence,
                    "total_seek_operations": r_fcfs.total_seek_operations,
                    "average_seek_distance": r_fcfs.average_seek_distance
                },
                "sstf": {
                    "seek_sequence": r_sstf.seek_sequence,
                    "total_seek_operations": r_sstf.total_seek_operations,
                    "average_seek_distance": r_sstf.average_seek_distance
                },
                "comparison": comp
            })

        elif path == "/api/shell/exec":
            cmd = body_json.get("cmd", "")
            out = shell.execute(cmd)
            self._send_json({"output": out})

        elif path == "/api/reset":
            mm.reset()
            processes.clear()
            # Restore 5 default procs
            defaults = [
                Process(pid=1, name="Web_Server", burst_time=6, arrival_time=0, memory_required=160, priority=2),
                Process(pid=2, name="Database_Query", burst_time=8, arrival_time=1, memory_required=220, priority=1),
                Process(pid=3, name="UI_Compositor", burst_time=4, arrival_time=2, memory_required=120, priority=3),
                Process(pid=4, name="Cache_Worker", burst_time=3, arrival_time=4, memory_required=80, priority=2),
                Process(pid=5, name="Log_Flusher", burst_time=5, arrival_time=5, memory_required=140, priority=4)
            ]
            for p in defaults:
                p.state = ProcessState.READY
                addr = mm.allocate(p.pid, p.name, p.memory_required, AllocationAlgorithm.FIRST_FIT)
                if addr is not None:
                    p.allocated_address = addr
                    p.allocated_size = p.memory_required
                processes.append(p)
            self._send_json({"success": True})

        elif path == "/api/scenario":
            name = qs.get("name", ["Balanced Workload"])[0]
            mm.reset()
            processes.clear()
            if "Frag" in name:
                procs = [
                    Process(pid=1, name="Alloc_1", burst_time=4, memory_required=150),
                    Process(pid=2, name="Alloc_2", burst_time=6, memory_required=250),
                    Process(pid=3, name="Alloc_3", burst_time=5, memory_required=180),
                ]
                for p in procs:
                    p.state = ProcessState.READY
                    addr = mm.allocate(p.pid, p.name, p.memory_required, AllocationAlgorithm.FIRST_FIT)
                    p.allocated_address = addr
                    processes.append(p)
                mm.deallocate(2)
                processes[1].state = ProcessState.TERMINATED
                processes[1].allocated_address = None
            else:
                defaults = [
                    Process(pid=1, name="Web_Server", burst_time=6, arrival_time=0, memory_required=160, priority=2),
                    Process(pid=2, name="Database_Query", burst_time=8, arrival_time=1, memory_required=220, priority=1),
                    Process(pid=3, name="UI_Compositor", burst_time=4, arrival_time=2, memory_required=120, priority=3),
                    Process(pid=4, name="Cache_Worker", burst_time=3, arrival_time=4, memory_required=80, priority=2),
                    Process(pid=5, name="Log_Flusher", burst_time=5, arrival_time=5, memory_required=140, priority=4)
                ]
                for p in defaults:
                    p.state = ProcessState.READY
                    addr = mm.allocate(p.pid, p.name, p.memory_required, AllocationAlgorithm.FIRST_FIT)
                    p.allocated_address = addr
                    processes.append(p)
            self._send_json({"success": True})

        else:
            self.send_response(404)
            self.end_headers()


def start_server(port=8080):
    handler = OSManagerHTTPHandler
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"[*] OS Resource Manager Simulator Web UI running at http://127.0.0.1:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Server stopped.")


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8080
    start_server(p)
