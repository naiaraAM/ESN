## How to generate the .exe file
```
pyinstaller --onefile --windowed --add-data "watermark.png;." --icon=app_icon.ico main.py
```

The .exe file will be in /dist directory.