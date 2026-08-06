# aio — All-In-One Pygame Launcher

A single-file Python application that discovers **every public pygame game** —
shipped with pygame, on PyPI, on GitHub, and on the curated
awesome-pygame list — and launches or installs any of them by **name** or
**listing number**, with five interfaces:

| Mode | Switch | Interface |
| --- | --- | --- |
| CLI | (default) / `--cli` | numbered list + launch/install commands |
| TUI | `--tui` | full-screen curses menus |
| GUI | `--gui` | tkinter tabbed window |
| WUI | `--wui [port]` | web UI + JSON API |
| Tray | `--tray` | system tray launcher (pystray) |

It compiles to a **standalone native binary** with Cython + gcc, and can run
straight from source.

## Quick start

```bash
./aio.py                      # or ./aio_bin (compiled) — lists 561 games
./aio.py list                 # same as above
./aio.py launch aliens        # built-in pygame example
./aio.py launch 163           # by listing number (pygame-easy-btn, PyPI)
./aio.py install 550          # pyscroll (awesome list) as a pip package
./aio.py install -r requirements.txt
./aio.py doctor               # system status
./aio.py --tui                # curses interface
./aio.py --gui                # tkinter interface
./aio.py --wui 8090           # web UI at http://localhost:8090
./aio.py --tray               # system tray menu
```

> Bare invocation (or `--cli`) lists the games; help is only shown for
> `-h` / `--help`.

## Game sources

| # | Source | Approx. count | Discovered via | Cache TTL |
| --- | --- | --- | --- | --- |
| 1 | **Built-in** pygame examples | 39 | `pygame.examples` | — |
| 2 | **PyPI** pygame packages | 347 | streaming scan of `pypi.org/simple/` | 7 days |
| 3 | **GitHub** pygame repos | 163 | GitHub search API (top by stars) | 24 hours |
| 4 | **Awesome** awesome-pygame list | 12 | `kadir014/awesome-pygame` README | 7 days |

Continuous numbering: built-in **1–39**, PyPI **40–386**, GitHub **387–549**,
awesome **550–561**. `launch` / `install` accept either the **name** or the
**number**. Listings are cached in `pygame_games_cache.json` next to the
binary; run once online, use forever offline.

## Launching

- **Built-in** → `python -m pygame.examples.<name>`
- **PyPI** → ensures the package is installed, then `python -m <pkg>`
- **GitHub / awesome** → clones the repo, finds a runnable entry point
  (root scripts, then `apps/`, `examples/`, `demo/`, `samples/` — scored by
  pygame usage), and runs it
- **URL / local file** → clone-and-run, or run the script directly

Missing modules are **auto-installed** (`pyopengl`, `numpy`, `pillow`,
`opencv-python`, …) and the game is retried once.

## CLI actions

| Action | Description |
| --- | --- |
| `list` (default) | print the numbered catalogue of all 561 games |
| `launch <name\|number>` | launch a game by name or listing number |
| `install <name\|number\|url\|file>` | install by name, number, git URL, or `-r` requirements file |
| `doctor` | system status (curses/tkinter/pystray/jinja2/cython) |
| `build <system>` | build integration: `cython`, `cmake`, `ninja`, `meson`, `cargo` |
| `jinja <inline\|render> ...` | Jinja2 templating |
| `hello [name]` | echo demo |
| `-h`, `--help` | usage (the only way to see it) |

## Interfaces

### TUI (`--tui`)
Key-driven curses UI. `l`/`b` built-in, `p` PyPI, `g` GitHub, `a` awesome,
`i` install by name, `v` pygame version management, `q` quit. Arrow keys +
Enter to launch from any list.

### GUI (`--gui`)
ttk notebook with one tab per source (counts in the tab titles). Buttons:
**System Doctor**, **Launch Selected**, **Install Selected**, **Open in
Browser**, **Exit**.

### WUI (`--wui [port]`)
Serves four cards (one per source, click any item to launch) plus a name/number
input with Launch / Install buttons. Results stream live into the status pane.

- `GET /` — the UI
- `GET /api/launch?name=<name-or-number>` — launch a game
- `GET /api/install?name=<name-or-number>` — install a game
- `GET /api/status?after=<index>` — poll launch/install results (the UI polls
  this every second)

### Tray (`--tray`)
pystray menu: Launch CLI / TUI / GUI / WUI (each in a fresh process), Launch
Pygame (Alien), Help, Quit.

## Compiler / build pipeline

| Stage | Tool | Output |
| --- | --- | --- |
| venv setup | `venv-build.sh` | `venv/` with pygame, jinja2, cython, pystray, pillow, pandas |
| Cythonize | `cython --embed -3 aio.py` | `aio_bin.c` |
| Compile | `gcc -O3 $(python3-config --cflags) aio_bin.c $(python3-config --ldflags --embed)` | `aio_bin` |
| Wrap | `build.sh` | runs `venv-build.sh`, then cython + gcc |
| Launcher | `aiorewrite` symlink | → `aio_bin` |

The compiled binary resolves the venv Python at runtime and auto-injects the
venv site-packages, so the whole toolchain works from one artifact.

## Documentation map

```
README.md                    this file
Doxyfile                     Doxygen configuration
docs/                        generated API reference (html/) + guides
  mainpage.md                Doxygen main page
  commands.md                CLI command reference
  api.md                     function-by-function API index
  architecture.md            how the pieces fit together
  INDEX.md                   THE MAP: docs, compiler, modes, sources
man/                         man pages (aio.1, per-mode, aio-suite.7)
install_man.sh               installs man pages (~/.local/share/man)
build-docs.sh                regenerates everything (docs all)
```

Regenerate all documentation with:

```bash
./build-docs.sh            # doxygen + man check + copy
./aio.py docs all          # same, via the CLI
```

## Layout

```
aio.py             the whole application (CLI, TUI, GUI, WUI, tray, launcher)
build.sh           full build pipeline (venv + cython + gcc)
venv-build.sh      venv bootstrap
requirements.txt   runtime requirements
pygame_games_cache.json   cached PyPI/GitHub/awesome listings (generated)
aio_bin            compiled binary (generated)
aio_bin.c          Cython output (generated)
```

## Requirements

- Python ≥ 3.10
- pygame (required for launching; `venv-build.sh` installs it)
- tkinter (GUI), pystray + pillow (tray), jinja2 (templating), cython
  (build) — all optional, detected at startup
- git, gcc, cython (only for the standalone build)
- doxygen, groff (only for regenerating docs)
