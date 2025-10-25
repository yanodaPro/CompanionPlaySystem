# CompanionPlaySystem

一个具有复古风格的桌面应用程序，提供强制陪玩功能和多种安全保护机制。

## 项目描述

这是一个使用Python和Tkinter开发的桌面应用程序，具有以下特点：
- 复古风格的UI界面设计
- 强制陪玩机制
- 多重安全保护（防止关闭、防止最小化、防止任务管理器）
- 密码和卡密双重解锁系统
- 设备绑定机制

## 功能特点

### 🎨 复古界面
- 经典Windows 95/98风格配色
- 灰色背景与深蓝色文字
- 立体边框效果
- 传统按钮样式

### 🔒 安全保护
- 窗口始终置顶
- 禁止最小化
- 监控并关闭任务管理器、CMD、PowerShell
- 防止系统关机

### 🔑 解锁系统
- **密码解锁**：预设密码退出
- **卡密解锁**：支持多个一次性卡密
- **设备绑定**：卡密与设备ID绑定，防止重复使用

## 技术栈

```python
import tkinter as tk
import psutil
import ctypes
import hashlib
import json
import threading
```



## 文件结构

```
CompanionPlaySystem/
├── CompanionPlaySystem_RetroVersion.py  # 复古版本主程序
├── CompanionPlaySystem(1.3.5).py        # 标准版本主程序  
└── used_keys.json                       # 卡密使用记录（运行时生成）
```

## 安装要求

```bash
pip install psutil
```

## 使用说明

### 启动程序
```cmd
python CompanionPlaySystem_RetroVersion.py
```
```cmd
python CompanionPlaySystem(1.3.5).py
```

### 操作流程
1. 阅读并同意用户协议
2. 勾选协议复选框
3. 点击"立即陪玩"按钮
4. 按照提示完成陪玩流程

### 退出方式
- **密码退出**：输入预设密码
- **卡密解锁**：使用有效的卡密临时解锁

## 代码示例

### 主窗口初始化
```python
class AntiCloseApp:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE) 
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # 设置窗口属性...
```

### 设备ID获取
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

### 系统监控
```python
def monitor_system(self):
    while True:
        # 检查任务管理器、cmd和powershell
        for proc in psutil.process_iter(['name']): 
            proc_name = proc.info['name'].lower() if proc.info['name'] else ''
            if proc_name in ['taskmgr.exe', 'cmd.exe', 'powershell.exe']: 
                try:
                    proc.kill() 
                except:
                    pass
        time.sleep(1)
```

## 配置参数

### 初始设置
```python
PASSWORD = "2002"  # 默认退出密码
CARD_KEYS = ["kdys-swax-458d", "plhz-nkcy-381s"]  # 可用卡密列表
WINDOW_TITLE = "都不陪的！！！"  # 窗口标题
```

### 复古配色方案
```python
BG_COLOR = "#c0c0c0"        # 经典灰色背景
BUTTON_COLOR = "#d4d0c8"    # 复古按钮颜色  
TEXT_COLOR = "#000080"      # 深蓝色文字
ACCENT_COLOR = "#800000"    # 深红色强调色
BORDER_STYLE = "groove"     # 复古边框样式
```

## 版本历史

### v1.3.5
- 基础功能实现
- 密码和卡密解锁系统
- 系统进程监控

### Retro Version
- 复古UI设计
- 增强的窗口管理
- 改进的设备绑定机制

## 注意事项

⚠️ **重要提醒**
- 该程序具有强制运行特性
- 请妥善保管退出密码
- 卡密为一次性使用，请谨慎选择
- 程序运行时会监控系统进程

## 许可证

© 2025 yanodaPro and Beautifulday 仅供学习交流使用

---

*注意：本项目为演示用途，请遵守相关法律法规。*
```
