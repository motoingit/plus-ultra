# Building Standalone Executables (Linux & Windows)

### 1. Linux Build (Produces `dist/plus-ultra`)
Run in bash on Ubuntu / Linux:
```bash
uv run pyinstaller --noconfirm --onefile --windowed \
    --name "plus-ultra" \
    --add-data "src/plus_ultra/resources:plus_ultra/resources" \
    --hidden-import "tkinter" \
    --hidden-import "sqlite3" \
    src/plus_ultra/main.py

chmod +x dist/plus-ultra
./dist/plus-ultra
```

---

### 2. Windows Build (Produces `dist/plus-ultra.exe`)
PyInstaller must run on Windows (or inside a Windows VM / Wine / GitHub Actions runner) because PyInstaller packages binaries for the host OS.

Run in Command Prompt / PowerShell on Windows:
> **Note the difference:** Windows uses a semicolon (`;`) instead of a colon (`:`) for `--add-data`.

```powershell
uv run pyinstaller --noconfirm --onefile --windowed `
    --name "plus-ultra" `
    --add-data "src\plus_ultra\resources;plus_ultra\resources" `
    --hidden-import "tkinter" `
    --hidden-import "sqlite3" `
    src\plus_ultra\main.py
```
*(In standard Windows `cmd.exe`, replace trailing backticks `` ` `` with `^` or write as a single line).*

Output will be located at:
```
dist\plus-ultra.exe
```
