# aio

**All-In-One Pygame Launcher** — a single Python file that discovers every
public pygame game (built-in examples, PyPI packages, GitHub repos, and the
awesome-pygame list) and launches or installs any of them by name or listing
number, from five interfaces: CLI, TUI, GUI, WUI and system tray.

The application compiles to a standalone native binary with
Cython + gcc and runs identically from source.

## Modes

| Mode | Switch | Entry point |
| --- | --- | --- |
| CLI | (default) / `--cli` | `run_cli` |
| TUI | `--tui` | `start_tui` / `run_tui` |
| GUI | `--gui` | `run_gui` |
| WUI | `--wui [port]` | `run_wui` |
| Tray | `--tray` | `run_taskbar` |

## Sources

| Source | Fetcher | Kind |
| --- | --- | --- |
| Built-in examples | `get_installed_pygame_examples` | `builtin` |
| PyPI packages | `fetch_pypi_public_games` | `pypi` |
| GitHub repos | `fetch_github_pygame_repos` | `github` |
| awesome-pygame | `fetch_awesome_pygame_repos` | `awesome` |

## API map

- Catalogue: `get_public_pygame_games`, `get_numbered_games`,
  `resolve_games_entry`, `list_public_games`
- Launch: `launch_game`, `run_pygame_launcher`, `clone_and_run_repo`,
  `find_entry_point`
- Install: `run_install`, `install_repo`, `pip_install`, `ensure_package`
- Auto-install: `run_with_auto_install`, `parse_missing_requirements`
- Caching: `_cached_fetch`, `_load_cache`, `_save_cache`
- pygame tooling: `get_available_pygame_versions`, `install_pygame_version`
- Build: `run_build`; templating: `run_jinja`
- Interfaces: `run_tui`, `run_gui`, `run_wui`, `run_taskbar`

See `docs/api.md` for the full function-by-function reference and
`docs/INDEX.md` for the documentation + compiler map.

## Building the documentation

```bash
doxygen Doxyfile        # -> docs/html/
./build-docs.sh         # doxygen + man-page check + install copy
./aio.py docs all       # same, from the CLI
```

Man pages live in `man/` (install with `./install_man.sh`).
