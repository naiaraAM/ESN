## How to generate the .exe file
```bash
pyinstaller --clean --onefile --windowed --add-data "img\\watermark.png;img" --add-data "img\\icon.ico;img" --icon=img/icon.ico main.py
```

The .exe file will be in /dist directory.