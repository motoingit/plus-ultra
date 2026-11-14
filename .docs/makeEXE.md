uv run pyinstaller --noconfirm --onefile --windowed \
    --name "plus-ultra" \
    --add-data "src/plus_ultra/resources:plus_ultra/resources" \
    --hidden-import "tkinter" \
    --hidden-import "sqlite3" \
    src/plus_ultra/main.py

chmod +x plus-ultra
./plus-ultra