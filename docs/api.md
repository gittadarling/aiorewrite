# aio API reference

Function-by-function index of `aio.py`. Every public function is documented
in the Doxygen HTML (see `docs/html/`).

## Runtime bootstrap

| Symbol | Purpose |
| --- | --- |
| `PYTHON_EXE` | real Python executable (venv python when compiled) |
| `_exe_dir` | directory of the executable / script |
| `_local_site_packages` | venv site-packages, auto-injected into `sys.path` |
| `HAS_CURSES` / `HAS_TKINTER` / `HAS_PYSTRAY` / `HAS_JINJA` / `HAS_CYTHON` | optional-dependency flags |

## Catalogue

| Function | Description |
| --- | --- |
| `list_public_games()` | print the numbered catalogue of all games |
| `get_public_pygame_games()` | dict of `builtin`/`pypi`/`github`/`awesome` listings |
| `get_numbered_games()` | flat `(number, kind, label)` list, continuous numbering |
| `resolve_games_entry(ref)` | map a name or number to `{"kind", "label"}` or `None` |
| `get_available_public_games()` | set of all launchable names |

## Source fetchers + cache

| Function | Description |
| --- | --- |
| `get_installed_pygame_examples()` | built-in example games via `pygame.examples` (fallback list) |
| `fetch_pypi_public_games()` | streaming scan of `pypi.org/simple/` |
| `fetch_github_pygame_repos()` | GitHub search API, top by stars |
| `fetch_awesome_pygame_repos()` | `kadir014/awesome-pygame` README links |
| `_cached_fetch(key, ttl, fetch_fn)` | time-limited disk cache wrapper |
| `_load_cache()` / `_save_cache(data)` | read / write `pygame_games_cache.json` |

Cache TTLs: PyPI 7 days, GitHub 24 hours, awesome 7 days.

## Launching

| Function | Description |
| --- | --- |
| `launch_game(ref)` | launch by name or number (all kinds) |
| `run_pygame_launcher(target)` | dispatch: git URL, built-in example, local file |
| `clone_and_run_repo(repo_url)` | clone, install requirements, find & run entry point |
| `find_entry_point(repo_dir)` | score scripts and pick a runnable entry point |
| `_script_pygame_score(path)` | score a script by pygame usage / naming |

`find_entry_point` scans root scripts, then `apps/`, `examples/`, `demo/`,
`samples/` recursively; candidates are scored for `import pygame`,
`pygame.init`, `pygame.display` and demo/main naming.

## Installing

| Function | Description |
| --- | --- |
| `run_install(args)` | install by name, number, URL, or requirements file |
| `install_repo(repo_url)` | shallow-clone + `requirements.txt` + `pip install` |
| `pip_install(packages)` | `pip install` the given packages |
| `ensure_package(name)` | check importable, else `pip install` |

## Auto-install of missing requirements

| Function | Description |
| --- | --- |
| `run_with_auto_install(cmd, label, cwd=None)` | run, detect missing deps, install, retry once |
| `parse_missing_requirements(output)` | extract packages from `ModuleNotFoundError` / `requires:` lines |

`MODULE_TO_PACKAGE` maps module names to pip names (`OpenGL`→`pyopengl`,
`cv2`→`opencv-python`, `numpy`, `PIL`→`pillow`, …); unknown modules fall
back to the module name as package name.

## pygame tooling

| Function | Description |
| --- | --- |
| `get_available_pygame_versions()` | `pip index versions pygame` with PyPI JSON fallback |
| `install_pygame_version(version)` | `pip install pygame==<version>` |

## Interfaces

| Function | Description |
| --- | --- |
| `run_cli(args)` | CLI mode; dispatch actions |
| `start_tui()` / `run_tui(stdscr)` | curses TUI entry / main loop |
| `tui_pick(stdscr, title, entries)` | generic picker used by all menus |
| `tui_pygame_menu` / `tui_pypi_menu` / `tui_github_menu` / `tui_awesome_menu` | per-source menus |
| `tui_pygame_version_menu(stdscr)` | pygame version manager |
| `tui_pypi_launch_menu(stdscr)` | install-by-name prompt |
| `run_gui()` | tkinter notebook window |
| `run_wui(port=8080)` | HTTP server + web UI + JSON API (launch/install/status) |
| `run_taskbar()` | pystray tray icon + menu |
| `_spawn_mode(flag)` | spawn a fresh instance of a mode (subprocess) |
| `create_image()` | tray icon image |

## Build + templates

| Function | Description |
| --- | --- |
| `run_build(args)` | `cython` / `cmake` / `ninja` / `meson` / `cargo` |
| `run_jinja(args)` | Jinja2 templating helpers |

## Entry point

`main()` parses `-h/--help`, the mode switch (`--cli/--tui/--gui/--wui/--tray`)
and the action, then dispatches. `--wui` accepts an optional numeric port as
the action positional.
