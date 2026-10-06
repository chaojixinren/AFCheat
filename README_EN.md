# AFCheat (Amazing Frog Trainer)

## Overview
AFCheat is a Windows trainer for the single-player game Amazing Frog. It provides a GUI to modify game memory, enabling features such as unlocking all costumes and enabling infinite ammo.

## How it works
- Uses Windows APIs (via Python's `ctypes`) to open the target game process and read/write its memory.
- Locates the `GameAssembly.dll` base address and finds target function addresses using known offsets or pattern scanning.
- Applies small assembly patches to force functions to return desired values and achieve modifications.

## Tech Stack
- Language: Python 3
- GUI: `tkinter`
- Memory operations: `ctypes` (calling `kernel32` / `psapi`), implemented in `afcheat/core/memory.py`
- Process enumeration: `psutil`
- Platform: Windows (requires administrator privileges for writing another process memory)

## Features
- List and select running processes
- Validate process and locate `GameAssembly.dll` base
- Unlock all costumes
- Enable / restore infinite ammo
- Restore original memory state

## Usage
1. Install dependencies:

```bash
pip install psutil
```

2. Run the game as administrator and make sure it is running. Then run the tool with administrator privileges:

```bash
python main.py
```

3. Use the GUI to select the target process, find functions and apply or restore patches.

## Notes
- For educational and research purposes only.
- Windows only; writing memory requires admin rights.
- Back up game saves and related data before use.

---
The project author is not responsible for any consequences resulting from the use of this tool.
