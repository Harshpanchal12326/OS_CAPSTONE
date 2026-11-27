"""
OS Resource Manager Simulator - Main Entry Point (main.py)
Usage:
    py main.py          (Automatically checks/installs dependencies and starts Streamlit dashboard)
    py main.py --web    (Starts standalone zero-dependency web dashboard)
    py main.py --cli    (Starts interactive terminal CLI)
"""

import sys
import os
import subprocess
import importlib.util

REQUIRED_PACKAGES = {
    "streamlit": "streamlit>=1.30.0",
    "matplotlib": "matplotlib>=3.8.0",
    "pandas": "pandas>=2.0.0",
    "numpy": "numpy>=1.24.0"
}


def print_banner():
    print("""
======================================================================
               OS RESOURCE MANAGER SIMULATOR LAUNCHER                 
======================================================================
  * Automated Dependency Checker & Installer
  * Launches Streamlit Dashboard (or Fallback Zero-Dependency Server)
======================================================================
""")


def get_missing_packages():
    """Returns a list of missing package requirement specifications."""
    missing = []
    for pkg_name, req_spec in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(pkg_name) is None:
            missing.append(req_spec)
    return missing


def install_requirements():
    """Installs required packages from requirements.txt using pip."""
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    print("[*] Checking dependencies...")
    missing = get_missing_packages()

    if not missing:
        print("[+] All required packages are already installed.")
        return True

    print(f"[-] Missing packages detected: {', '.join(missing)}")
    print("[*] Installing requirements via pip. Please wait...\n")

    cmd = [sys.executable, "-m", "pip", "install"]
    if os.path.exists(req_file):
        cmd.extend(["-r", req_file])
    else:
        cmd.extend(missing)

    try:
        subprocess.check_call(cmd)
        print("\n[+] Successfully installed all dependencies!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error during package installation (exit code {e.returncode}).")
        return False
    except Exception as e:
        print(f"\n[!] Unexpected error while invoking pip: {e}")
        return False


def run_streamlit(extra_args=None):
    """Launches the Streamlit application."""
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    if not os.path.exists(app_path):
        print(f"[!] Error: Could not locate app.py at {app_path}")
        sys.exit(1)

    print("[+] Launching Streamlit Dashboard (app.py)...")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    if extra_args:
        cmd.extend(extra_args)

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[*] Streamlit server stopped by user.")


def run_fallback_web():
    """Launches the zero-dependency built-in web server."""
    print("[*] Launching Standalone Web Dashboard (web_server.py)...")
    web_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_server.py")
    subprocess.run([sys.executable, web_path, "8080"])


def run_fallback_cli():
    """Launches the interactive terminal CLI."""
    cli_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cli.py")
    subprocess.run([sys.executable, cli_path])


def main():
    print_banner()

    args = sys.argv[1:]

    # Check for direct flags
    if "--cli" in args:
        run_fallback_cli()
        return

    if "--web" in args:
        run_fallback_web()
        return

    # Default path: Verify and install requirements, then launch Streamlit
    install_ok = install_requirements()

    if install_ok:
        run_streamlit(args)
    else:
        print("\n" + "="*70)
        print("[!] Could not complete automatic package installation.")
        print("    You can still run the simulator immediately using:")
        print("      Option A: py main.py --web  (Zero-dependency Web UI on http://localhost:8080)")
        print("      Option B: py main.py --cli  (Zero-dependency Terminal CLI)")
        print("="*70)
        choice = input("\nWould you like to start the zero-dependency web dashboard now? (y/n): ").strip().lower()
        if choice in ["y", "yes"]:
            run_fallback_web()


if __name__ == "__main__":
    main()
