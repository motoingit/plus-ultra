

## The three folders

| Variable | Default | What it is for | Analogy |
|---|---|---|---|
| `$XDG_DATA_HOME` | `~/.local/share` | Data that matters and should survive: databases, saved documents, icons, launchers | A filing cabinet or pantry |
| `$XDG_STATE_HOME` | `~/.local/state` | Data that persists between runs but wouldn't hurt to lose: logs, history, "where I left off" | A logbook or notepad |
| `$XDG_RUNTIME_DIR` | `/run/user/1000` | Temporary things for the current login: sockets, lock files | A whiteboard wiped at night |

## What `.local` is

`~/.local` is a mini `/usr` just for your user. System-wide software uses `/usr/bin` and `/usr/share`. Your personal equivalents are `~/.local/bin` (where `uv tool install` puts commands), `~/.local/share` and `~/.local/state`.

Uninstalling the code doesn't touch `~/.local/share/plus-ultra`, so your tasks survive a reinstall.

## Why logs are in state, not data

The spec added the state folder in 2021 for exactly this. Data is what you'd be upset to lose, and a log is what you'd read when debugging and would shrug off if it vanished.

## The runtime folder

`1000` is your user ID (`id -u` shows it). The system creates this folder when you log in, with permissions only you can use. It lives in RAM and is deleted when you log out, so nothing in it survives a reboot. That makes it perfect for a lock file, because a lock left behind by a crash can't linger forever. It's also where Wayland puts its connection socket, so the display system you're running on already uses it.

It isn't guaranteed to exist, for example over SSH without a login session. That's why the plan has a fallback for the lock file in Phase 6.

## Try it yourself

```bash
echo "$XDG_DATA_HOME"      # probably empty, so defaults apply
ls -la ~/.local            # bin, share, state
echo "$XDG_RUNTIME_DIR"    # /run/user/1000
ls "$XDG_RUNTIME_DIR"      # you'll see the Wayland socket here
```

There's also `$XDG_CONFIG_HOME` (`~/.config`) for settings files and `$XDG_CACHE_HOME` (`~/.cache`) for rebuildable data. plus-ultra doesn't need either yet, since the plan keeps settings in the database.

Send Q2 whenever you're ready.