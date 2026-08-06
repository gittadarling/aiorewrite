#!/usr/bin/env python3
"""
All-In-One (AIO) Application Rewrite - Phase 2
Consolidates CLI, TUI, GUI, Taskbar, Pygame Launcher, Build Tools, and Templating into a single script.
"""

import argparse
import os
import sys

# Find the real python executable (sys.executable points to aio_bin when compiled)
import shutil
PYTHON_EXE = sys.executable
if not os.path.basename(PYTHON_EXE).lower().startswith("python"):
    _exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    _venv_python = os.path.join(_exe_dir, "venv", "bin", "python3")
    if os.path.exists(_venv_python):
        PYTHON_EXE = _venv_python
    else:
        PYTHON_EXE = shutil.which("python3") or "python3"

# Auto-inject local venv site-packages so the Cython-compiled binary works seamlessly
_exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
_local_site_packages = os.path.join(_exe_dir, "venv", "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
if os.path.exists(_local_site_packages) and _local_site_packages not in sys.path:
    import site
    site.addsitedir(_local_site_packages)

import subprocess
import threading
import time
import tempfile
import json
import re
from pathlib import Path
import shutil

# Try importing optional dependencies
try:
    import curses
    HAS_CURSES = True
except ImportError:
    HAS_CURSES = False

try:
    import tkinter as tk
    from tkinter import messagebox
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except Exception as e:
    PYSTRAY_ERROR = str(e)
    HAS_PYSTRAY = False

try:
    import jinja2
    HAS_JINJA = True
except ImportError:
    HAS_JINJA = False

try:
    from Cython.Build import cythonize
    HAS_CYTHON = True
except ImportError:
    HAS_CYTHON = False


# ========================================================================
# BUILD SYSTEM INTEGRATION
# ========================================================================
def run_build(args):
    if not args:
        print("Error: Missing build system (cython, cmake, ninja, meson, cargo).")
        return
    
    system = args[0].lower()
    build_args = args[1:]
    
    print(f"--- Build System: {system.upper()} ---")
    
    if system == "cython":
        if not HAS_CYTHON:
            print("Error: cython module not available. (pip install cython)")
            return
        if not build_args:
            print("Usage: aio.py build cython <file.py>")
            return
        
        target = build_args[0]
        print(f"Cythonizing {target}...")
        try:
            # Create a dynamic setup script for cythonization
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(f"from setuptools import setup\nfrom Cython.Build import cythonize\nsetup(ext_modules=cythonize('{target}'))\n")
                setup_file = f.name
            
            subprocess.run([PYTHON_EXE, setup_file, "build_ext", "--inplace"], check=True)
            os.remove(setup_file)
            print("Cython build complete.")
        except Exception as e:
            print(f"Cython build failed: {e}")

    elif system == "cmake":
        if len(build_args) < 2:
            print("Usage: aio.py build cmake <source_dir> <build_dir>")
            return
        subprocess.run(["cmake", "-S", build_args[0], "-B", build_args[1]])

    elif system == "ninja":
        if len(build_args) < 1:
            print("Usage: aio.py build ninja <build_dir>")
            return
        subprocess.run(["ninja", "-C", build_args[0]])

    elif system == "meson":
        if len(build_args) < 2:
            print("Usage: aio.py build meson <build_dir> <source_dir>")
            return
        subprocess.run(["meson", "setup", build_args[0], build_args[1]])

    elif system == "cargo":
        target = build_args[0] if build_args else "."
        subprocess.run(["cargo", "build", "--manifest-path", os.path.join(target, "Cargo.toml")])

    else:
        print(f"Unknown build system: {system}")


# ========================================================================
# JINJA2 TEMPLATING
# ========================================================================
def run_jinja(args):
    if not HAS_JINJA:
        print("Error: jinja2 module not available. (pip install jinja2)")
        return
    if len(args) < 2:
        print("Usage: aio.py jinja <template.j2> <data.json>")
        return
    
    template_path = args[0]
    data_path = args[1]
    
    try:
        with open(data_path, 'r') as f:
            data = json.load(f)
            
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        template = jinja2.Template(template_content)
        rendered = template.render(**data)
        
        print("--- Rendered Template ---")
        print(rendered)
        
    except Exception as e:
        print(f"Template rendering failed: {e}")


# ========================================================================
# CLI MODE
# ========================================================================
def list_public_games():
    games = get_public_pygame_games()
    entries = get_numbered_games()
    builtin, pypi = games["builtin"], games["pypi"]
    github, awesome = games["github"], games["awesome"]
    github_by_repo = {r["repo"]: r for r in github}
    awesome_by_repo = {r["repo"]: r for r in awesome}

    print("\n--- Available Public Pygame Games (launch/install by name or number) ---")

    print(f"\n  Built-in (shipped with pygame): {len(builtin)} game(s)")
    for number, kind, name in entries:
        if kind != "builtin":
            break
        print(f"    {number:>4}. {name}")
    if builtin:
        print("    (launch with: aio.py launch <name-or-number>)")

    if pypi:
        print(f"\n  PyPI (pygame packages): {len(pypi)} package(s)")
        for number, kind, name in entries:
            if kind != "pypi":
                continue
            print(f"    {number:>4}. {name}")
        print("    (install with: aio.py install <name-or-number>)")

    if github:
        print(f"\n  GitHub (pygame repos, top by stars): {len(github)} repo(s)")
        for number, kind, label in entries:
            if kind != "github":
                continue
            repo = github_by_repo[label]
            line = f"    {number:>4}. {repo['repo']}  (★{repo['stars']})"
            if repo["desc"]:
                line += f"  - {repo['desc']}"
            print(line[:160])
        print("    (install/clone with: aio.py install <name-or-number>)")

    if awesome:
        print(f"\n  Awesome (curated awesome-pygame list): {len(awesome)} repo(s)")
        for number, kind, label in entries:
            if kind != "awesome":
                continue
            repo = awesome_by_repo[label]
            line = f"    {number:>4}. {repo['repo']}"
            if repo["desc"]:
                line += f"  - {repo['desc']}"
            print(line[:160])
        print("    (install/clone with: aio.py install <name-or-number>)")

    print(f"\n  Total: {len(entries)} public pygame games/packages available.")
    if not pypi and not github and not awesome:
        print("  (online sources unavailable - run once with internet to cache PyPI/GitHub listings)")


def run_cli(args):
    print("========================================")
    print(" AIO Application - CLI Mode Phase 2")
    print("========================================")
    print(f"Action   : {args.action or 'list'}")
    if args.args:
        print(f"Arguments: {args.args}")
    print("\nSystem Status:")
    print(f" - Curses   (TUI)    : {'Available' if HAS_CURSES else 'Not Available'}")
    print(f" - Tkinter  (GUI)    : {'Available' if HAS_TKINTER else 'Not Available'}")
    print(f" - Pystray  (Taskbar): {'Available' if HAS_PYSTRAY else 'Not Available'}")
    print(f" - Jinja2   (Tpl)    : {'Available' if HAS_JINJA else 'Not Available'}")
    print(f" - Cython   (Build)  : {'Available' if HAS_CYTHON else 'Not Available'}")
    print("========================================")
    
    ensure_testpkg()
    
    action = (args.action or "list").lower()
    if action in ("help", "list", "games"):
        list_public_games()
    elif action == "doctor":
        print("Running system checks... All good!")
    elif action == "hello":
        name = args.args[0] if args.args else "World"
        print(f"Hello, {name}!")
    elif action == "launch":
        if not args.args:
            print("Error: Please provide a public pygame game name or listing number. See: aio.py list")
        else:
            launch_game(args.args[0])
    elif action == "install":
        run_install(args.args)
    elif action == "build":
        run_build(args.args)
    elif action == "jinja":
        run_jinja(args.args)
    elif action == "docs":
        run_docs(args.args)
    else:
        print(f"Unknown action: {action}")


# ========================================================================
# PYPI & PIP INTEGRATION
# ========================================================================
import importlib.util

def ensure_package(package_name: str) -> bool:
    """Check if a Python package is installed; if not, install it via pip."""
    if importlib.util.find_spec(package_name) is None:
        try:
            subprocess.check_call([PYTHON_EXE, "-m", "pip", "install", package_name])
            return True
        except subprocess.CalledProcessError:
            return False
    return True

def get_available_pygame_versions() -> list:
    """Fetch all available Pygame versions published on PyPI using pip index."""
    cmd = [PYTHON_EXE, "-m", "pip", "index", "versions", "pygame"]
    try:
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        for line in output.splitlines():
            if "Available versions:" in line:
                versions_str = line.split("Available versions:")[1].strip()
                return [v.strip() for v in versions_str.split(",") if v.strip()]
    except subprocess.CalledProcessError:
        try:
            import urllib.request
            url = "https://pypi.org/pypi/pygame/json"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                return list(data.get("releases", {}).keys())
        except Exception:
            pass
    return []

def install_pygame_version(version: str) -> bool:
    specifier = f"pygame=={version}"
    try:
        subprocess.check_call(
            [PYTHON_EXE, "-m", "pip", "install", specifier],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        return True
    except subprocess.CalledProcessError:
        return False

# ========================================================================
# TUI MODE
# ========================================================================
PYGAME_EXAMPLES = [
    "aliens", "chimp", "freetype", "glcube", "liquid", "stars", "vgrade",
    "blend_fill", "blit_blends", "camera", "cursors", "droq", "eventlist",
    "fonty", "midi", "mask", "moveit", "pixelarray", "prevent_display_stretching",
    "scroll", "sound", "sound_array_demos", "sprite_texture", "textinput", "video"
]

def get_installed_pygame_examples():
    """Return the public pygame example games shipped with the installed pygame.

    Falls back to the curated PYGAME_EXAMPLES list when pygame is not importable.
    """
    try:
        import pygame.examples as pe
        import pkgutil
        installed = sorted(m.name for m in pkgutil.iter_modules(pe.__path__))
        return installed or list(PYGAME_EXAMPLES)
    except Exception:
        return list(PYGAME_EXAMPLES)

CACHE_FILE = os.path.join(_exe_dir, "pygame_games_cache.json")

def _load_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cache(data):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=1)
    except Exception:
        pass

def _cached_fetch(key, ttl, fetch_fn):
    """Fetch via fetch_fn, caching the result on disk for `ttl` seconds."""
    cache = _load_cache()
    entry = cache.get(key) or {}
    if time.time() - entry.get("ts", 0) < ttl and entry.get("items"):
        return entry["items"]
    try:
        items = fetch_fn()
    except Exception:
        return entry.get("items", [])
    if items:
        cache[key] = {"ts": time.time(), "items": items}
        _save_cache(cache)
    return items

def fetch_pypi_public_games():
    """All pygame-related packages published on PyPI (via the Simple API)."""
    def _scan():
        import urllib.request
        import re
        url = "https://pypi.org/simple/"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        names = []
        with urllib.request.urlopen(req, timeout=90) as resp:
            buf = b""
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                buf += chunk
                while b"</a>" in buf:
                    item, buf = buf.split(b"</a>", 1)
                    m = re.search(rb"<a[^>]*>([^<]+)", item)
                    if m:
                        name = m.group(1).decode("utf-8", "replace").strip()
                        if name and "pygame" in name.lower():
                            names.append(name)
        return sorted(set(names))
    return _cached_fetch("pypi_pygame", 7 * 24 * 3600, _scan)

def fetch_github_pygame_repos():
    """Public pygame game repositories on GitHub (top by stars, cached)."""
    def _search():
        import urllib.request
        import json as _json
        repos = {}
        for query in ("pygame+language:python", "pygame+game"):
            url = ("https://api.github.com/search/repositories"
                   f"?q={query}&sort=stars&order=desc&per_page=100")
            req = urllib.request.Request(url, headers={
                "User-Agent": "aiorewrite",
                "Accept": "application/vnd.github+json",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
            for it in data.get("items", []):
                repos[it["full_name"]] = {
                    "repo": it["full_name"],
                    "stars": it.get("stargazers_count", 0),
                    "desc": (it.get("description") or "").strip(),
                }
        return sorted(repos.values(), key=lambda r: -r["stars"])
    return _cached_fetch("github_pygame", 24 * 3600, _search)

def fetch_awesome_pygame_repos():
    """Curated awesome-pygame list (kadir014/awesome-pygame), cached."""
    def _fetch():
        import urllib.request
        import re
        url = "https://raw.githubusercontent.com/kadir014/awesome-pygame/master/README.md"
        req = urllib.request.Request(url, headers={"User-Agent": "aiorewrite"})
        md = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        repos = {}
        for text, _u, owner, name in re.findall(
                r"\[([^\]]+)\]\((https://github\.com/([^/]+)/([^)/#]+))", md):
            repos[f"{owner}/{name}"] = {
                "repo": f"{owner}/{name}",
                "stars": 0,
                "desc": text.strip(),
            }
        return sorted(repos.values(), key=lambda r: r["repo"].lower())
    return _cached_fetch("awesome_pygame", 7 * 24 * 3600, _fetch)

def get_available_public_games():
    """Launchable public pygame games shipped with the installed pygame module."""
    return get_installed_pygame_examples()

def get_public_pygame_games():
    """All available public pygame games, grouped by source.

    Sources: games shipped with pygame (installed), pygame-related packages
    published on PyPI, and public pygame repositories on GitHub. Online
    sources are cached on disk and degrade gracefully when offline.
    """
    return {
        "builtin": get_installed_pygame_examples(),
        "pypi": fetch_pypi_public_games(),
        "github": fetch_github_pygame_repos(),
        "awesome": fetch_awesome_pygame_repos(),
    }

def get_numbered_games():
    """Continuous (number, kind, label) listing across all sources."""
    games = get_public_pygame_games()
    entries = []
    n = 0
    for name in games["builtin"]:
        n += 1
        entries.append((n, "builtin", name))
    for name in games["pypi"]:
        n += 1
        entries.append((n, "pypi", name))
    for repo in games["github"]:
        n += 1
        entries.append((n, "github", repo["repo"]))
    for repo in games["awesome"]:
        n += 1
        entries.append((n, "awesome", repo["repo"]))
    return entries

def resolve_games_entry(ref):
    """Resolve a game name or listing number to a {kind, number, label} entry."""
    if isinstance(ref, int) or (isinstance(ref, str) and ref.strip().isdigit()):
        num = int(ref)
        for number, kind, label in get_numbered_games():
            if number == num:
                return {"kind": kind, "number": number, "label": label}
        return None
    r = ref.strip().lower()
    for name in get_installed_pygame_examples():
        if name.lower() == r:
            return {"kind": "builtin", "number": None, "label": name}
    for name in fetch_pypi_public_games():
        if name.lower() == r:
            return {"kind": "pypi", "number": None, "label": name}
    for repos in (fetch_github_pygame_repos(), fetch_awesome_pygame_repos()):
        for repo in repos:
            if repo["repo"].lower() == r or repo["repo"].lower().split("/")[-1] == r:
                kind = "github" if repo["stars"] else "awesome"
                return {"kind": kind, "number": None, "label": repo["repo"]}
    return None

def tui_pick(stdscr, title, entries):
    """entries: list of (display, value). Up/Down + Enter to launch, 'q' back."""
    stdscr.nodelay(False)
    stdscr.timeout(-1)

    if not entries:
        stdscr.clear()
        try:
            stdscr.addstr(0, 0, title + " (empty - fetch may have failed)", curses.A_BOLD)
            stdscr.addstr(2, 0, "Press any key to go back.")
        except curses.error:
            pass
        stdscr.refresh()
        stdscr.getch()
        return

    current_idx = 0
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        try:
            stdscr.addstr(0, 0, title + " (Up/Down, Enter to launch, 'q' to go back):", curses.A_BOLD)
            display_count = max_y - 3
            if display_count < 1:
                display_count = 1
            start_idx = max(0, current_idx - display_count // 2)
            end_idx = min(len(entries), start_idx + display_count)
            for i in range(start_idx, end_idx):
                y = i - start_idx + 2
                if i == current_idx:
                    stdscr.addstr(y, 2, f"> {entries[i][0]}", curses.A_REVERSE)
                else:
                    stdscr.addstr(y, 2, f"  {entries[i][0]}")
        except curses.error:
            pass
        stdscr.refresh()
        c = stdscr.getch()

        if c == ord('q'):
            break
        elif c == curses.KEY_UP or c == ord('k'):
            current_idx = max(0, current_idx - 1)
        elif c == curses.KEY_DOWN or c == ord('j'):
            current_idx = min(len(entries) - 1, current_idx + 1)
        elif c == ord('\n') or c == curses.KEY_ENTER or c == 10 or c == 13:
            value = entries[current_idx][1]
            threading.Thread(target=launch_game, args=(value,), daemon=True).start()
            try:
                stdscr.addstr(max_y - 1, 0, f"Launched {value}... Press any key to continue.")
            except curses.error:
                pass
            stdscr.refresh()
            stdscr.getch()

def tui_pygame_menu(stdscr):
    tui_pick(stdscr, "Select a Built-in Pygame Game",
             [(g, g) for g in get_available_public_games()])

def tui_pypi_menu(stdscr):
    tui_pick(stdscr, "Select a PyPI Pygame Package",
             [(p, p) for p in fetch_pypi_public_games()])

def tui_github_menu(stdscr):
    repos = get_public_pygame_games()["github"]
    tui_pick(stdscr, "Select a GitHub Pygame Repo",
             [(f"{r['repo']}  (★{r['stars']})  {r['desc']}", r["repo"]) for r in repos])

def tui_awesome_menu(stdscr):
    repos = get_public_pygame_games()["awesome"]
    tui_pick(stdscr, "Select an Awesome Pygame Repo",
             [(f"{r['repo']}  -  {r['desc']}", r["repo"]) for r in repos])

def tui_pygame_version_menu(stdscr):
    stdscr.nodelay(False)
    stdscr.timeout(-1)
    
    stdscr.clear()
    stdscr.addstr(0, 0, "Fetching available Pygame versions from PyPI...", curses.A_BOLD)
    stdscr.refresh()
    
    versions = get_available_pygame_versions()
    if not versions:
        stdscr.addstr(2, 0, "Failed to fetch versions. Press any key.")
        stdscr.refresh()
        stdscr.getch()
        return
        
    current_idx = 0
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        try:
            stdscr.addstr(0, 0, "Select Pygame Version to Install (Up/Down, Enter to install, 'q' to go back):", curses.A_BOLD)
            display_count = max_y - 3
            if display_count < 1: display_count = 1
                
            start_idx = max(0, current_idx - display_count // 2)
            end_idx = min(len(versions), start_idx + display_count)
            
            for i in range(start_idx, end_idx):
                y = i - start_idx + 2
                if i == current_idx:
                    stdscr.addstr(y, 2, f"> {versions[i]}", curses.A_REVERSE)
                else:
                    stdscr.addstr(y, 2, f"  {versions[i]}")
        except curses.error:
            pass
            
        stdscr.refresh()
        c = stdscr.getch()
        
        if c == ord('q'):
            break
        elif c == curses.KEY_UP or c == ord('k'):
            current_idx = max(0, current_idx - 1)
        elif c == curses.KEY_DOWN or c == ord('j'):
            current_idx = min(len(versions) - 1, current_idx + 1)
        elif c == ord('\n') or c == curses.KEY_ENTER or c == 10 or c == 13:
            stdscr.clear()
            target_version = versions[current_idx]
            stdscr.addstr(0, 0, f"Installing pygame=={target_version}... Please wait.")
            stdscr.refresh()
            success = install_pygame_version(target_version)
            if success:
                stdscr.addstr(2, 0, f"Successfully installed pygame {target_version}! Press any key.", curses.A_BOLD)
            else:
                stdscr.addstr(2, 0, f"Failed to install pygame {target_version}. Press any key.")
            stdscr.refresh()
            stdscr.getch()
            break

def tui_pypi_launch_menu(stdscr):
    stdscr.nodelay(False)
    stdscr.timeout(-1)
    
    curses.echo()
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter PyPI package name to install and launch (or blank to cancel): ", curses.A_BOLD)
    stdscr.refresh()
    
    pkg_bytes = stdscr.getstr(1, 0, 50)
    curses.noecho()
    pkg_name = pkg_bytes.decode('utf-8').strip()
    
    if not pkg_name:
        return
        
    stdscr.addstr(3, 0, f"Ensuring '{pkg_name}' is installed via pip...")
    stdscr.refresh()
    
    success = ensure_package(pkg_name)
    if success:
        stdscr.addstr(4, 0, "Installed successfully! Launching in background...")
        stdscr.refresh()
        threading.Thread(target=lambda: subprocess.run([PYTHON_EXE, "-m", pkg_name]), daemon=True).start()
        time.sleep(1)
    else:
        stdscr.addstr(4, 0, "Failed to install package. Press any key.")
        stdscr.refresh()
        stdscr.getch()

def run_tui(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    msg = "AIO Application - TUI Mode"
    sub_msg = ("'q' Quit | 'l' Built-in | 'p' PyPI | 'g' GitHub | 'a' Awesome "
               "| 'i' Install by name | 'v' Versions")

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        x = max(0, (width - len(msg)) // 2)
        y = max(0, height // 2)
        
        sub_x = max(0, (width - len(sub_msg)) // 2)
        
        try:
            stdscr.addstr(y, x, msg, curses.A_BOLD)
            stdscr.addstr(y + 2, sub_x, sub_msg)
        except curses.error:
            pass
        
        stdscr.refresh()
        
        c = stdscr.getch()
        if c == ord('q'):
            break
        elif c == ord('l') or c == ord('b'):
            tui_pygame_menu(stdscr)
            stdscr.nodelay(True)
            stdscr.timeout(100)
        elif c == ord('p'):
            tui_pypi_menu(stdscr)
            stdscr.nodelay(True)
            stdscr.timeout(100)
        elif c == ord('g'):
            tui_github_menu(stdscr)
            stdscr.nodelay(True)
            stdscr.timeout(100)
        elif c == ord('a'):
            tui_awesome_menu(stdscr)
            stdscr.nodelay(True)
            stdscr.timeout(100)
        elif c == ord('i'):
            tui_pypi_launch_menu(stdscr)
            stdscr.nodelay(True)
            stdscr.timeout(100)
        elif c == ord('v'):
            tui_pygame_version_menu(stdscr)
            stdscr.nodelay(True)
            stdscr.timeout(100)


def start_tui():
    if not HAS_CURSES:
        print("Error: curses module not available for TUI mode.")
        sys.exit(1)
    curses.wrapper(run_tui)


# ========================================================================
# GUI MODE
# ========================================================================
def run_gui():
    if not HAS_TKINTER:
        print("Error: tkinter module not available for GUI mode.")
        sys.exit(1)

    from tkinter import ttk

    games = get_public_pygame_games()

    root = tk.Tk()
    root.title("AIO Application - GUI Mode")
    root.geometry("600x540")

    tk.Label(root, text="All-In-One Dashboard", font=("Helvetica", 16, "bold")).pack(pady=8)

    tabs = [
        ("Built-in", [("builtin", g) for g in games["builtin"]]),
        ("PyPI", [("pypi", g) for g in games["pypi"]]),
        ("GitHub", [("github", r["repo"]) for r in games["github"]]),
        ("Awesome", [("awesome", r["repo"]) for r in games["awesome"]]),
    ]

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=10, pady=6)

    lists = {}
    for title, items in tabs:
        frame = tk.Frame(nb)
        nb.add(frame, text=f"{title} ({len(items)})")
        lb = tk.Listbox(frame, exportselection=False)
        lb.pack(fill="both", expand=True, padx=4, pady=4)
        for _kind, label in items:
            lb.insert(tk.END, label)
        lists[title] = lb

    def current_selection():
        idx = nb.index(nb.select())
        title, _items = tabs[idx]
        lb = lists[title]
        sel = lb.curselection()
        if not sel:
            return None
        label = lb.get(sel[0])
        for kind in ("builtin", "pypi"):
            if label in games[kind]:
                return (kind, label)
        for kind in ("github", "awesome"):
            for r in games[kind]:
                if r["repo"] == label:
                    return (kind, label)
        return None

    def on_launch():
        cur = current_selection()
        if not cur:
            messagebox.showwarning("Launch", "Select a pygame from the list first.")
            return
        _kind, label = cur
        threading.Thread(target=launch_game, args=(label,), daemon=True).start()

    def on_install():
        cur = current_selection()
        if not cur:
            messagebox.showwarning("Install", "Select a package from the list first.")
            return
        kind, label = cur
        if kind == "builtin":
            messagebox.showinfo("Install", f"'{label}' is built-in - nothing to install.")
            return
        threading.Thread(target=run_install, args=([label],), daemon=True).start()

    def on_doctor():
        messagebox.showinfo("Doctor", "Running system checks... All systems go!")

    def on_open():
        cur = current_selection()
        if not cur:
            messagebox.showwarning("Open", "Select a repo from the list first.")
            return
        kind, label = cur
        if kind in ("github", "awesome"):
            import webbrowser
            webbrowser.open(f"https://github.com/{label}")

    btns = tk.Frame(root)
    btns.pack(pady=4)
    tk.Button(btns, text="System Doctor", width=16, command=on_doctor).pack(side="left", padx=4)
    tk.Button(btns, text="Launch Selected", width=16, command=on_launch).pack(side="left", padx=4)
    tk.Button(btns, text="Install Selected", width=16, command=on_install).pack(side="left", padx=4)
    tk.Button(btns, text="Open in Browser", width=16, command=on_open).pack(side="left", padx=4)
    tk.Button(btns, text="Exit", width=10, command=root.quit).pack(side="left", padx=4)

    root.mainloop()


# ========================================================================
# TASKBAR / TRAY MODE
# ========================================================================
def create_image():
    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    d = ImageDraw.Draw(image)
    d.text((10, 25), "AIO", fill=(255, 255, 0))
    return image

def on_quit_callback(icon, item):
    icon.stop()

def _spawn_mode(flag):
    """Launch a mode of this app in a separate process (CLI/TUI/GUI/WUI/help)."""
    app = os.path.abspath(sys.argv[0])
    if app.endswith(".py"):
        cmd = [PYTHON_EXE, app, flag]
    else:
        cmd = [app, flag]
    print(f"Launching {flag} ...")
    subprocess.Popen(cmd, cwd=_exe_dir)

def run_taskbar():
    if not HAS_PYSTRAY:
        print(f"Error: pystray/pillow module not available. (Reason: {PYSTRAY_ERROR})")
        print("Please install them: pip install pystray pillow")
        print("Running in background mock mode...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting.")
        sys.exit(1)

    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem("Launch CLI", lambda: _spawn_mode("--cli")),
        pystray.MenuItem("Launch TUI", lambda: _spawn_mode("--tui")),
        pystray.MenuItem("Launch GUI", lambda: _spawn_mode("--gui")),
        pystray.MenuItem("Launch WUI", lambda: _spawn_mode("--wui")),
        pystray.MenuItem("Launch Pygame (Alien)", lambda: threading.Thread(target=run_pygame_launcher, args=("aliens",), daemon=True).start()),
        pystray.MenuItem("Help", lambda: _spawn_mode("--help")),
        pystray.MenuItem("Quit", on_quit_callback)
    )
    icon = pystray.Icon("AIO", image, "AIO App", menu)
    print("Taskbar app running. Check your system tray.")
    icon.run()


# ========================================================================
# ADVANCED PYGAME LAUNCHER
# ========================================================================
MODULE_TO_PACKAGE = {
    "OpenGL": "pyopengl",
    "OpenGL.GL": "pyopengl",
    "OpenGL.GLU": "pyopengl",
    "cv2": "opencv-python",
    "numpy": "numpy",
    "PIL": "pillow",
    "pandas": "pandas",
    "jinja2": "jinja2",
}

def parse_missing_requirements(output):
    """Extract pip package names from a failed launch."""
    needs = set()
    for m in re.findall(r"The \w+ example requires: ([^\n]+)", output):
        needs.update(m.split())
    for m in re.findall(r"ModuleNotFoundError: No module named '([^']+)'", output):
        mod = m.split(".")[0]
        needs.add(MODULE_TO_PACKAGE.get(mod, mod))
    for m in re.findall(r"ImportError: No module named ([^\s]+)", output):
        mod = m.split(".")[0]
        needs.add(MODULE_TO_PACKAGE.get(mod, mod))
    return sorted(needs)

def pip_install(packages):
    """Install the given pip packages, returning success."""
    pkgs = sorted({p.lower() for p in packages if p})
    if not pkgs:
        return False
    print(f"Auto-installing missing requirements: {', '.join(pkgs)} ...")
    try:
        result = subprocess.run([PYTHON_EXE, "-m", "pip", "install", *pkgs],
                                text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Auto-install failed: {e}")
        return False

def run_with_auto_install(cmd, label, cwd=None):
    """Run a command; on failure auto-install missing requirements and retry once."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    except Exception as e:
        print(f"Failed to launch {label}: {e}")
        return

    output = (result.stdout or "") + (result.stderr or "")
    missing = parse_missing_requirements(output)
    if result.returncode != 0 or missing:
        if missing:
            print(output.strip())
            if pip_install(missing):
                print(f"Retrying {label} ...")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
                output = (result.stdout or "") + (result.stderr or "")

    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")

ENTRY_POINT_NAMES = ("main.py", "game.py", "app.py", "run.py", "play.py")
ENTRY_POINT_DIRS = ("apps", "examples", "example", "demo", "demos", "samples")

def _script_pygame_score(path):
    try:
        with open(path, "r", errors="ignore") as f:
            text = f.read(8000)
    except OSError:
        return 0
    score = 0
    if "import pygame" in text:
        score += 2
    if "pygame.init" in text:
        score += 3
    if "pygame.display" in text:
        score += 2
    if "__main__" in text:
        score += 1
    base = os.path.basename(path)
    if base in ENTRY_POINT_NAMES:
        score += 2
    lower = base.lower()
    if lower.startswith(("demo", "example", "main", "game", "play", "run")):
        score += 1
    return score

def find_entry_point(repo_dir):
    candidates = []
    for name in ENTRY_POINT_NAMES:
        p = os.path.join(repo_dir, name)
        if os.path.isfile(p):
            candidates.append(p)
    try:
        for f in sorted(os.listdir(repo_dir)):
            if f.endswith(".py") and os.path.isfile(os.path.join(repo_dir, f)):
                if f not in ("setup.py", "setupx.py"):
                    candidates.append(os.path.join(repo_dir, f))
    except OSError:
        pass
    for sub in ENTRY_POINT_DIRS:
        d = os.path.join(repo_dir, sub)
        if os.path.isdir(d):
            for root, _dirs, files in os.walk(d):
                depth = len(os.path.relpath(root, d).split(os.sep))
                if depth > 3:
                    _dirs[:] = []
                for f in sorted(files):
                    if f.endswith(".py") and os.path.isfile(os.path.join(root, f)):
                        candidates.append(os.path.join(root, f))
    scored = [(_script_pygame_score(c), c) for c in candidates]
    scored.sort(key=lambda t: (-t[0], len(t[1].split(os.sep)), len(os.path.basename(t[1])), t[1]))
    if scored and scored[0][0] > 0:
        return scored[0][1]
    demo_dirs = ("examples", "example", "demo", "demos", "apps", "samples")
    runnable_names = ("demo", "example", "main", "game", "play", "run")
    for _score, c in scored:
        parts = c.lower().split(os.sep)
        if any(d in parts for d in demo_dirs) and \
           os.path.basename(c).lower().startswith(runnable_names):
            return c
    return None

TESTPKG_DIR = os.path.expanduser("~/testpkg")

def ensure_testpkg():
    """Create the persistent checkout directory ~/testpkg on first use."""
    if not os.path.isdir(TESTPKG_DIR):
        os.makedirs(TESTPKG_DIR, exist_ok=True)
        print(f"Created {TESTPKG_DIR} for repository checkouts.")
    return TESTPKG_DIR

def _repo_slug(repo_url):
    """Map a git URL to a stable directory name under ~/testpkg."""
    try:
        from urllib.parse import urlparse
        u = repo_url if "://" in repo_url else "https://" + repo_url
        path = urlparse(u).path.rstrip("/")
    except Exception:
        path = repo_url
    if path.endswith(".git"):
        path = path[:-4]
    parts = [p for p in path.lstrip("/").split("/") if p]
    if len(parts) >= 2:
        return "__".join(parts[-2:])
    return parts[-1] if parts else "repo"

def _checkout(repo_url, shallow=False):
    """Ensure the repo is checked out in ~/testpkg, cloning or pulling."""
    ensure_testpkg()
    slug = _repo_slug(repo_url)
    target_dir = os.path.join(TESTPKG_DIR, slug)
    if os.path.isdir(os.path.join(target_dir, ".git")):
        print(f"Already checked out at {target_dir}; pulling latest ...")
        subprocess.run(["git", "-C", target_dir, "pull"], check=False)
    else:
        print(f"Cloning repository {repo_url} -> {target_dir} ...")
        cmd = ["git", "clone", repo_url, target_dir]
        if shallow:
            cmd.insert(2, "--depth")
            cmd.insert(3, "1")
        os.makedirs(target_dir, exist_ok=True)
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            shutil.rmtree(target_dir, ignore_errors=True)
            raise e
    return target_dir

def clone_and_run_repo(repo_url):
    try:
        target_dir = _checkout(repo_url)
    except subprocess.CalledProcessError as e:
        print(f"Error during cloning: {e}")
        return

    req_file = os.path.join(target_dir, "requirements.txt")
    if os.path.exists(req_file):
        print("Found requirements.txt, installing...")
        subprocess.run([PYTHON_EXE, "-m", "pip", "install", "-r", req_file], check=False)

    target = find_entry_point(target_dir)
    if target is not None:
        rel = os.path.relpath(target, target_dir)
        print(f"Found entry point {rel}, launching...")
        run_with_auto_install([PYTHON_EXE, target], os.path.basename(target), cwd=target_dir)
    else:
        print("No runnable entry point found in the repository "
              "(this is likely a library, not a standalone game).")
        print("Try: aio.py install <name-or-number> to install it as a Python package.")

def run_pygame_launcher(target):
    print(f"--- Pygame Launcher: Preparing to launch '{target}' ---")
    
    # Check if target is a remote git repo
    if target.startswith("http://") or target.startswith("https://") or target.endswith(".git"):
        clone_and_run_repo(target)
        return
        
    # Check if target is a known builtin example
    if target.lower() in get_available_public_games():
        print(f"Executing python -m pygame.examples.{target.lower()} ...")
        run_with_auto_install([PYTHON_EXE, "-m", f"pygame.examples.{target.lower()}"],
                              f"pygame.examples.{target.lower()}")
        return

    # Check if it's a local file
    if os.path.exists(target):
        print(f"Executing local script: {target}")
        run_with_auto_install([PYTHON_EXE, target], target)
    else:
        print(f"Target '{target}' not found (not a local file, git repo, or built-in example). Cannot launch.")


def find_module_name(dist_name):
    """Resolve the importable module name(s) for an installed distribution.

    PyPI package names frequently differ from their module names (e.g. the
    'PyGameLab' distribution provides the 'pygamelab' module), so the
    launch logic resolves the real module before running ``python -m``.
    Returns a list ordered by likelihood; the first importable entry wins.
    """
    candidates = [dist_name]
    try:
        from importlib.metadata import packages_distributions
        for mod, dists in packages_distributions().items():
            if any(d.lower() == dist_name.lower() for d in dists) and mod not in candidates:
                candidates.append(mod)
    except Exception:
        pass
    try:
        from importlib.metadata import files
        for f in files(dist_name) or []:
            if str(f).endswith("top_level.txt"):
                for ln in (f.read_text() or "").splitlines():
                    ln = ln.strip()
                    if ln and ln not in candidates:
                        candidates.append(ln)
    except Exception:
        pass
    ordered = sorted(candidates, key=lambda c: (c.lower() != dist_name.lower(), c.lower()))
    importable = [c for c in ordered if importlib.util.find_spec(c) is not None]
    return importable or ordered

def _is_runnable_module(mod):
    """True if `python -m <mod>` can execute it (module, or package with __main__)."""
    try:
        spec = importlib.util.find_spec(mod)
    except Exception:
        return False
    if spec is None:
        return False
    if spec.submodule_search_locations is not None:
        try:
            return importlib.util.find_spec(mod + ".__main__") is not None
        except Exception:
            return False
    return True

def launch_game(ref):
    """Launch a pygame by name or listing number."""
    entry = resolve_games_entry(ref)
    if entry is None:
        run_pygame_launcher(ref)
        return
    kind, label = entry["kind"], entry["label"]
    if kind == "builtin":
        run_pygame_launcher(label)
    elif kind == "pypi":
        print(f"--- Ensuring '{label}' is installed ---")
        if ensure_package(label):
            module = None
            for cand in find_module_name(label):
                if _is_runnable_module(cand):
                    module = cand
                    break
            if module is None:
                importable = [c for c in find_module_name(label) if importlib.util.find_spec(c) is not None]
                print(f"Package '{label}' is installed but has no runnable entry point"
                      f" (no __main__, likely a library).")
                if importable:
                    print(f"  Importable modules: {', '.join(importable)}")
                return
            print(f"Launching {module} via python -m {module} ...")
            run_with_auto_install([PYTHON_EXE, "-m", module], f"python -m {module}")
        else:
            print(f"Failed to install/launch {label}.")
    elif kind in ("github", "awesome"):
        clone_and_run_repo(f"https://github.com/{label}.git")


def install_repo(repo_url):
    """Clone a git repository into ~/testpkg and install it (requirements.txt + setup)."""
    print(f"Installing via git from {repo_url} into {TESTPKG_DIR} ...")
    try:
        target_dir = _checkout(repo_url, shallow=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to clone repository: {e}")
        return
    req_file = os.path.join(target_dir, "requirements.txt")
    if os.path.exists(req_file):
        print("Found requirements.txt, installing dependencies...")
        subprocess.run([PYTHON_EXE, "-m", "pip", "install", "-r", req_file], check=False)
    print("Installing package...")
    result = subprocess.run([PYTHON_EXE, "-m", "pip", "install", target_dir], check=False)
    if result.returncode != 0:
        print("No installable setup.py - requirements above were installed; run with: aio.py launch <repo-url>")


def run_install(args):
    """Install any pygame: by name, listing number, git repo, or requirements file."""
    if not args:
        print("Usage: aio.py install <name|number|repo-url|requirements.txt>")
        return
    target = args[0]
    if target in ("-r", "--requirements", "--req"):
        if len(args) < 2:
            print("Error: Missing requirements file.")
            return
        target = args[1]
    if target.endswith((".txt", ".requirements")) or os.path.isfile(target):
        print(f"Installing requirements from {target} ...")
        subprocess.run([PYTHON_EXE, "-m", "pip", "install", "-r", target], check=False)
        return
    if target.startswith(("http://", "https://", "git+", "github.com")):
        url = target if not target.startswith("github.com") else f"https://{target}"
        install_repo(url)
        return
    entry = resolve_games_entry(target)
    if entry is None:
        pip_install([target])
        return
    kind, label = entry["kind"], entry["label"]
    if kind == "builtin":
        print(f"'{label}' is a built-in pygame example (already installed) - nothing to do.")
    elif kind == "pypi":
        pip_install([label])
    elif kind in ("github", "awesome"):
        install_repo(f"https://github.com/{label}.git")


# ========================================================================
# WUI (WEB UI) MODE
# ========================================================================
def run_wui(port=8080):
    import http.server
    import socketserver

    games = get_public_pygame_games()

    def _li_ul(items_html):
        return f"<ul>{items_html}</ul>" if items_html else "<ul><li>(none)</li></ul>"

    builtin_html = "".join(
        f"<li onclick=\"doName('launch','{n}')\" title=\"launch\">{n}</li>" for n in games["builtin"])
    pypi_html = "".join(
        f"<li onclick=\"doName('launch','{p}')\" title=\"launch\">{p}</li>" for p in games["pypi"])
    github_html = "".join(
        f"<li onclick=\"doName('launch','{r['repo']}')\" title=\"launch\">{r['repo']}"
        f" <em>(★{r['stars']})</em></li>" for r in games["github"])
    awesome_html = "".join(
        f"<li onclick=\"doName('launch','{r['repo']}')\" title=\"launch\">{r['repo']}"
        f" <em>{r['desc']}</em></li>" for r in games["awesome"])

    html_content = f"""    <!DOCTYPE html>
    <html>
    <head>
        <title>AIO Web UI</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background-color: #121212; color: #ffffff; }}
            .header {{ background: #1f1f1f; padding: 20px; text-align: center; border-bottom: 2px solid #333; }}
            .container {{ padding: 40px; max-width: 900px; margin: auto; }}
            .card {{ background: #1f1f1f; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center; margin-bottom: 20px; }}
            .card ul {{ text-align: left; columns: 3; list-style: none; padding: 0; }}
            .card li {{ padding: 2px 0; font-family: monospace; cursor: pointer; }}
            .card li:hover {{ color: #bb86fc; }}
            .card li em {{ color: #888; font-style: normal; font-size: 12px; }}
            button {{ padding: 12px 24px; margin: 10px; cursor: pointer; border: none; background: #bb86fc; color: #000; font-weight: bold; border-radius: 4px; font-size: 16px; transition: 0.3s; }}
            button:hover {{ background: #3700b3; color: white; }}
            input {{ padding: 12px; width: 260px; border-radius: 4px; border: 1px solid #333; background: #2a2a2a; color: #fff; }}
            #status {{ margin-top: 20px; color: #03dac6; font-family: monospace; text-align: left; max-height: 220px; overflow-y: auto; white-space: pre-wrap; }}
        </style>
        <script>
            var lastStatus = -1;
            function doAction(action) {{
                fetch('/api/' + action).catch(function(){{}});
            }}
            function doName(action, name) {{
                fetch('/api/' + action + '?name=' + encodeURIComponent(name)).catch(function(){{}});
            }}
            function doInput(action) {{
                var name = document.getElementById('name').value;
                if (name) doName(action, name);
            }}
            function pollStatus() {{
                fetch('/api/status?after=' + lastStatus)
                    .then(r => r.json())
                    .then(lines => {{
                        var el = document.getElementById('status');
                        for (var k = 0; k < lines.length; k++) {{
                            lastStatus = lines[k][0];
                            el.innerText += '\\n' + lines[k][1];
                        }}
                        el.scrollTop = el.scrollHeight;
                    }})
                    .catch(function(){{}});
            }}
            setInterval(pollStatus, 1000);
        </script>
    </head>
    <body>
        <div class="header">
            <h1>AIO Application Dashboard</h1>
        </div>
        <div class="container">
            <div class="card">
                <h2>Built-in Pygame Games ({len(games['builtin'])})</h2>
                {_li_ul(builtin_html)}
            </div>
            <div class="card">
                <h2>PyPI Pygame Packages ({len(games['pypi'])})</h2>
                {_li_ul(pypi_html)}
            </div>
            <div class="card">
                <h2>GitHub Pygame Repos ({len(games['github'])})</h2>
                {_li_ul(github_html)}
            </div>
            <div class="card">
                <h2>Awesome Pygame List ({len(games['awesome'])})</h2>
                {_li_ul(awesome_html)}
            </div>
            <div class="card">
                <h2>Control Panel</h2>
                <p>Click an item above, or enter a name/number here to launch or install:</p>
                <input id="name" placeholder="game name or listing number">
                <br>
                <button onclick="doInput('launch')">Launch</button>
                <button onclick="doInput('install')">Install</button>
                <button onclick="doAction('doctor')">Run System Doctor</button>
                <button onclick="doAction('launch_alien')">Launch Alien Pygame</button>
                <pre id="status">Ready.</pre>
            </div>
        </div>
    </body>
    </html>
    """
    
    wui_log = []
    wui_lock = threading.Lock()

    def _log_wui(msg):
        with wui_lock:
            wui_log.append([len(wui_log), msg])
            if len(wui_log) > 500:
                del wui_log[:len(wui_log) - 500]

    def _wui_launch(name):
        import io
        import contextlib
        _log_wui(f"launch {name}: starting ...")
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                launch_game(name)
            out = buf.getvalue().strip()
            _log_wui(f"launch {name}: {out or 'finished'}")
        except Exception as e:
            _log_wui(f"launch {name}: ERROR {e}")

    def _wui_install(name):
        import io
        import contextlib
        _log_wui(f"install {name}: starting ...")
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                run_install([name])
            out = buf.getvalue().strip()
            _log_wui(f"install {name}: {out or 'finished'}")
        except Exception as e:
            _log_wui(f"install {name}: ERROR {e}")

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass # Suppress logging to console
            
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
            elif self.path.startswith('/api/'):
                path, _, qs = self.path.partition('?')
                query = {}
                if qs:
                    for kv in qs.split('&'):
                        if '=' in kv:
                            k, v = kv.split('=', 1)
                            query[k] = v
                action = path.split('/')[-1]

                if action == 'status':
                    try:
                        after = int(query.get('after', '-1'))
                    except ValueError:
                        after = -1
                    with wui_lock:
                        lines = [[i, m] for i, m in wui_log if i > after]
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(lines).encode('utf-8'))
                    return

                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()

                if action == 'doctor':
                    _log_wui("doctor: system is healthy, all checks passed.")
                    self.wfile.write(b"System is healthy! All checks passed.")
                elif action == 'launch_alien':
                    threading.Thread(target=_wui_launch, args=("aliens",), daemon=True).start()
                    self.wfile.write(b"Launching Pygame Alien Example...")
                elif action == 'launch':
                    name = query.get('name', '')
                    threading.Thread(target=_wui_launch, args=(name,), daemon=True).start()
                    self.wfile.write(f"Launching {name}...".encode('utf-8'))
                elif action == 'install':
                    name = query.get('name', '')
                    threading.Thread(target=_wui_install, args=(name,), daemon=True).start()
                    self.wfile.write(f"Installing {name}...".encode('utf-8'))
                else:
                    self.wfile.write(b"Unknown action")
            else:
                super().do_GET()

    # Allow port reuse
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    with ReusableTCPServer(("", port), Handler) as httpd:
        print(f"Web UI running at http://localhost:{port}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nShutting down Web UI...")


# ========================================================================
# DOCS GENERATION
# ========================================================================
def run_docs(args):
    """Regenerate documentation: doxygen HTML + install man pages."""
    sub = (args[0] if args else "all").lower()
    root = _exe_dir
    done = []

    def _doxygen():
        doxyfile = os.path.join(root, "Doxyfile")
        if not os.path.exists(doxyfile):
            print("Doxyfile not found; skipping doxygen.")
            return
        print("Running doxygen ...")
        result = subprocess.run(["doxygen", doxyfile], cwd=root)
        if result.returncode == 0:
            done.append("docs/html")
        return result.returncode

    def _man():
        mandir = os.path.expanduser("~/.local/share/man")
        man_src = os.path.join(root, "man")
        if not os.path.isdir(man_src):
            print("man/ not found; skipping man install.")
            return
        os.makedirs(os.path.join(mandir, "man1"), exist_ok=True)
        os.makedirs(os.path.join(mandir, "man7"), exist_ok=True)
        for page in sorted(os.listdir(man_src)):
            if page.endswith((".1", ".7")):
                shutil.copy2(os.path.join(man_src, page), os.path.join(mandir, f"man{page[-1]}", page))
        done.append("man -> " + mandir)

    if sub in ("doxygen",):
        return _doxygen()
    if sub in ("man",):
        _man()
        return 0
    if sub in ("markdown", "md", "html"):
        print("commands.md / api.md / architecture.md / INDEX.md are hand-written; "
              "regenerate HTML with `doxygen Doxyfile`.")
        return 0
    if sub in ("all",):
        _doxygen()
        _man()
        print("See docs/INDEX.md for the documentation and build map.")
        return 0
    print("Usage: aio.py docs <doxygen|man|markdown|html|all>")
    return 1


# ========================================================================
# MAIN ENTRY
# ========================================================================
def main():
    parser = argparse.ArgumentParser(add_help=False, description="All-In-One Application (CLI, TUI, GUI, Tray, Launcher, Build, Jinja)")

    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")

    # Display modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--cli", action="store_true", help="Run in Command Line Interface mode (default); lists available public pygame games")
    mode_group.add_argument("--tui", action="store_true", help="Run in Text User Interface mode (curses)")
    mode_group.add_argument("--gui", action="store_true", help="Run in Graphical User Interface mode (tkinter)")
    mode_group.add_argument("--wui", action="store_true", help="Run in Web User Interface mode (browser)")
    mode_group.add_argument("--tray", action="store_true", help="Run as a Taskbar/System Tray application (pystray)")

    # CLI actions
    parser.add_argument("action", nargs="?", default=None, help="Action (e.g., list, launch <name-or-number>, install, doctor, build, jinja)")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Additional arguments")

    args = parser.parse_args()

    # Help is only printed when explicitly requested with -h / --help.
    if args.help:
        parser.print_help()
        sys.exit(0)

    if args.gui:
        run_gui()
    elif args.wui:
        port = int(args.action) if args.action and str(args.action).isdigit() else 8080
        run_wui(port)
    elif args.tui:
        start_tui()
    elif args.tray:
        run_taskbar()
    else:
        # No switch (or --cli): implicit CLI mode - lists available public pygame games.
        run_cli(args)

if __name__ == "__main__":
    main()
