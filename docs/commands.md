# aio command reference

Generated documentation for the All-In-One Pygame Launcher CLI.

## Synopsis

```
aio.py [-h | --help] [--cli | --tui | --gui | --wui [port] | --tray]
       [action] [arguments...]
```

The default (no switch, or `--cli`) is CLI mode. `-h` / `--help` is the only
way to print usage; bare invocation lists the games.

## Actions

| Action | Arguments | Description |
| --- | --- | --- |
| `list` | — | print the numbered catalogue (default when no action) |
| `games` | — | alias of `list` |
| `help` | — | alias of `list` |
| `launch` | `<name-or-number>` | launch a game by name or listing number |
| `install` | `<name\|number\|url\|file\|-r file>` | install a game / repo / requirements |
| `doctor` | — | system status (curses/tkinter/pystray/jinja2/cython) |
| `hello` | `[name]` | echo demo |
| `build` | `<system> [args]` | build integration (see below) |
| `jinja` | `...` | Jinja2 templating |
| `docs` | `<markdown\|html\|man\|doxygen\|all>` | regenerate documentation |

Unknown actions print `Unknown action: <name>` and exit.

## Build targets (`build`)

| Target | Usage |
| --- | --- |
| `cython` | `aio.py build cython <file.py>` — cythonize in place |
| `cmake` | `aio.py build cmake <source_dir> <build_dir>` |
| `ninja` | `aio.py build ninja <build_dir>` |
| `meson` | `aio.py build meson <build_dir> <source_dir>` |
| `cargo` | `aio.py build cargo [target]` |

## Launch semantics

| Kind | Launch command |
| --- | --- |
| `builtin` | `python -m pygame.examples.<name>` |
| `pypi` | ensure installed, then `python -m <pkg>` |
| `github` / `awesome` | clone + `find_entry_point` + run |
| URL / local file | clone-and-run, or run directly |

Missing modules are auto-installed via `run_with_auto_install` and the launch
is retried once.

## Install semantics

| Target | Action |
| --- | --- |
| number → `builtin` | nothing to do (already installed) |
| number → `pypi` | `pip install <pkg>` |
| number → `github` / `awesome` | `install_repo(https://github.com/<repo>.git)` |
| `https://...` / `git+...` / `github.com/...` | `install_repo(url)` |
| `*.txt` / `*.requirements` / existing file | `pip install -r <file>` |
| `-r <file>` | `pip install -r <file>` |
| anything else (unresolved) | `pip install <target>` |

## WUI endpoints

| Endpoint | Description |
| --- | --- |
| `GET /` | the web UI (four cards + control panel) |
| `GET /api/launch?name=<name-or-number>` | launch a game |
| `GET /api/install?name=<name-or-number>` | install a game |

Default port **8080**; override with `--wui <port>`.
