| Variable| Default| What it is for | Analogy |
| ------------------ | ------------------ | ----------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `$XDG_DATA_HOME`   | `~/.local/share`   | Important application data that should persist: databases, saved documents, icons, launchers                | A filing cabinet or pantry   |
| `$XDG_STATE_HOME`  | `~/.local/state`   | Data that persists between runs but is okay to lose: logs, history, and “where I left off” information      | A logbook or notepad         |
| `$XDG_CONFIG_HOME` | `~/.config`        | User-specific application settings and configuration files                                                  | A settings handbook          |
| `$XDG_CACHE_HOME`  | `~/.cache`         | Rebuildable data that can be regenerated: cached images, downloaded metadata, temporary computation results | A scratchpad                 |
| `$XDG_RUNTIME_DIR` | `/run/user/1000`\* | Temporary runtime objects for the current login session: sockets, lock files, and other IPC files           | A whiteboard wiped at logout |
