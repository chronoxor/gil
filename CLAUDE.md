# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`gil` is a single-file Python 3 CLI (`gil.py`) that manages git repository dependencies described in `.gitlinks` files. It solves the recursive-duplication problem of `git submodule` by cloning each unique repo once and stitching repos together with **symlinks** instead of nested copies. See [README.md](README.md) for the conceptual motivation (submodule/subtree comparison and the cycle-resolution example).

The whole tool is `gil.py` (~425 lines). `gil` and `gil.bat` are thin shell/batch wrappers that `exec python3 gil.py "$@"`. There are no source modules, no tests, and no lint/format config — edits go directly to `gil.py`.

## Commands

```shell
# Install from source (editable)
pip3 install -e .

# Run without installing
python3 gil.py <command> [args]
./gil <command> [args]          # bash wrapper

# Smoke test against the bundled sample (this is what CI does)
cd sample && gil update && cd CppLogging/build && ./unix.sh
```

There is no test suite. Validate changes by running `gil update` in `sample/` and inspecting the resulting symlink topology, or by running the GitHub Actions workflows in `.github/workflows/` (each platform runs `gil update` in `sample/` and then builds `CppLogging`).

## Architecture

Two classes in [gil.py](gil.py) do all the work:

- **`GilRecord`** — one row of a `.gitlinks` file: `(name, path, repo, branch, links)`. Identity (`__eq__`/`__hash__`) is **(name, repo, branch)** — `path` is intentionally excluded so the same logical repo discovered at different paths is treated as the same record. The first path seen wins; later occurrences become symlink targets.

- **`GilContext`** holds an `OrderedDict` of records keyed by themselves (so insertion order = discovery order = canonical-path order). Key methods:
  - `discover(path)` — walks **upward** from `path` to find the topmost ancestor containing a `.gitlinks` file (this is the "root"), then `discover_recursive` walks **downward** through every `.gitlinks` it finds. Any record whose `path` lies inside the original `path` is marked `active` (only active records receive `pull`/`push`/`commit`/`status`).
  - `clone(args)` — BFS over records: clones each missing repo, then re-runs `discover_path` on the freshly cloned dir to enqueue any new dependencies it introduces. This is how cycles terminate — `GilRecord.__eq__` deduplicates so the cycle's second leg becomes a symlink, not another clone.
  - `link()` — re-walks up to the root then calls `update_link(src, dst)` for every `.gitlinks` entry. `src` is the canonical (first-discovered) path; `dst` is the path the current `.gitlinks` expects. If `dst` already exists as a non-link directory it is removed and replaced with a symlink. The optional 5th/6th tokens on a line (`base_path target_path` pairs, repeatable) create additional sub-symlinks from `src/base_path` to the current-dir-relative `target_path` — this is how the sample wires `scripts/build` to point inside an already-linked module.
  - `command(name, args)` — runs `git <name> <args...>` in cwd, then in every `active` record's directory (after checking out the record's branch). Used by `pull`/`push`/`commit`/`status`.

## `.gitlinks` file format

Each non-blank, non-`#` line:

```
name  path  repo  branch  [base_path target_path]...
```

- `name` — identifier; combined with `repo` + `branch` to dedupe across the whole tree.
- `path` — relative to the **directory containing this `.gitlinks`** (not the root).
- `repo`, `branch` — passed to `git clone -b <branch> <repo>`.
- Trailing tokens come in pairs (parser rejects odd counts ≥ 5). Each pair adds an extra symlink from `src/base_path` → `target_path` after the main link is created.
- Tokens are space-split via `GilContext.split` (a regex that preserves `"…"` and `'…'` quoted substrings).

## Things to watch out for

- **Cloning uses `--recurse-submodules`** ([gil.py:311](gil.py:311)) — gil cooperates with, rather than replaces, regular submodules nested inside dependency repos.
- **`git_clone` retries up to 10 times with a 10s sleep** between attempts; don't replace this with a single call without reason — CI relies on it for flaky network conditions.
- **`update_link` replaces non-empty directories with symlinks** ([gil.py:295-303](gil.py:295)) only when the destination already contains content but isn't already a correct symlink. Be careful refactoring this — silently deleting a user's edits in a duplicated directory is a real risk.
- **Recursion depth is hard-capped at 1000** (`GilContext(path, 1000)` in `main`) and `discover_recursive` raises on overflow. Cycles are not what trips this; pathologically deep `.gitlinks` chains are.
- **`active` is set on the record object itself**, which is mutated in place. Two `discover()` calls in one process won't reset active flags — fine for the CLI's one-shot invocation, but worth knowing if calling the API in a loop.
- Version lives in **two places**: `__version__` in [gil.py](gil.py) and `version` in [pyproject.toml](pyproject.toml). Bump both.
