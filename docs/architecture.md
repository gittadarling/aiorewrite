# aio architecture

How the All-In-One Pygame Launcher fits together.

## Runtime flow

```
main()
 ├─ parse args (-h/--help, mode switch, action, REMAINDER)
 ├─ --gui   → run_gui()
 ├─ --wui   → run_wui(port)
 ├─ --tui   → start_tui() → run_tui(stdscr)
 ├─ --tray  → run_taskbar()
 └─ default → run_cli(args)
                └─ list / launch / install / doctor / build / jinja / hello / docs
```

## Game discovery pipeline

```
fetch_*  (network)
   │
   ▼
_cached_fetch (TTL: pypi 7d, github 24h, awesome 7d)
   │            pygame_games_cache.json (beside the binary)
   ▼
get_public_pygame_games()
   │        {builtin, pypi, github, awesome}
   ▼
get_numbered_games()   continuous numbering 1..N
   │
   ▼
resolve_games_entry(ref)   name or number → {kind, label}
```

Sources:

1. **builtin** — `pygame.examples` package enumeration (no network).
2. **pypi** — streaming scan of the `pypi.org/simple/` index page; HTML
   search and XML-RPC are bot-blocked, so the simple index is parsed for
   names containing `pygame`.
3. **github** — GitHub search API (`q=pygame language:python`, `per_page=100`,
   sorted by stars).
4. **awesome** — the `kadir014/awesome-pygame` README, repo links extracted
   with a regex.

## Launch resolution

```
launch_game(ref)
 ├─ builtin → python -m pygame.examples.<name>
 ├─ pypi    → ensure_package() then python -m <pkg>
 ├─ github/awesome → clone_and_run_repo(https://github.com/<repo>.git)
 └─ (unresolved) → run_pygame_launcher(ref)  [URL / local file / builtin name]

clone_and_run_repo()
 ├─ _checkout()  git clone into ~/testpkg/<owner>__<repo> (created on first run;
 │               existing checkouts updated with git pull)
 ├─ install requirements.txt (if any)
 ├─ find_entry_point()   root scripts → apps/examples/demo/samples (scored)
 └─ run_with_auto_install()  auto-install missing modules, retry once
```

`find_entry_point` scores each candidate: `import pygame` (+2), `pygame.init`
(+3), `pygame.display` (+2), `__main__` (+1), standard entry names (+2),
demo/main filename (+1). Only demo-style scripts in demo-style directories
qualify as a zero-score fallback; pure libraries (e.g. `pygame_gui`) report
"no runnable entry point" and suggest `install`.

## Auto-install

```
run_with_auto_install(cmd)
 ├─ run (capture stdout+stderr)
 ├─ parse_missing_requirements(output)
 │     "The <X> example requires: a b"  → a, b
 │     ModuleNotFoundError: No module named 'Y' → MODULE_TO_PACKAGE[Y] or Y
 ├─ if rc != 0 or missing → pip_install(missing) → retry once
```

## Interfaces

- **CLI** — argparse with `add_help=False`; bare run is an implicit CLI list.
- **TUI** — curses; `tui_pick` is the shared picker for all four sources;
  key shortcuts `l/p/g/a/i/v/q`.
- **GUI** — tkinter ttk notebook, one tab per source; launch/install run on a
  worker thread so the UI stays responsive.
- **WUI** — stdlib `http.server`/`socketserver` (no dependencies); card list
  + `/api/launch` + `/api/install` + `/api/status` (live result streaming).
  Port from `--wui <port>`, default 8080.
- **Tray** — pystray; every "Launch <mode>" item calls `_spawn_mode()` which
  re-invokes the app (`sys.argv[0]`) with the corresponding flag in a new
  process, so each mode is independent.

## Compiler / build

```
build.sh
 ├─ venv-build.sh        venv with pygame, jinja2, cython, pystray, pillow, pandas
 └─ cython --embed -3 aio.py -o aio_bin.c
    └─ gcc -O3 $(python3-config --cflags) aio_bin.c $(python3-config --ldflags --embed) -o aio_bin
```

At runtime the compiled binary (whose `sys.executable` is the binary itself)
falls back to `venv/bin/python3` for `PYTHON_EXE` and auto-injects the venv
site-packages, so launching, pip and pygame all resolve to the same venv.

## Data files

| File | Purpose |
| --- | --- |
| `pygame_games_cache.json` | cached PyPI / GitHub / awesome listings |
| `venv/` | the runtime environment |
| `aio_bin` / `aio_bin.c` | compiled artifacts |
