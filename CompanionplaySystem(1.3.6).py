import tkinter as tk
from tkinter import messagebox
import os
import sys
import ctypes
import psutil
import subprocess
import threading
import time
import hashlib
import json
import winreg  # 用于注册表操作

# ---------------------------- 全局配置 ----------------------------
PASSWORD = "2002"
CARD_KEYS = ["kdys-swax-458d", "plhz-nkcy-381s", "gwtq-zymv-645k", "nykp-sdjh-107t"]
WINDOW_TITLE = "都不陪的！！！"

# 互斥体名称，用于防止多开和守护进程识别
MUTEX_MAIN = "Global\\Companionplay_Main_Mutex"
MUTEX_DAEMON = "Global\\Companionplay_Daemon_Mutex"

# 守护进程PID保存文件
DAEMON_PID_FILE = "daemon.pid"

# ---------------------------- 设备ID获取 ----------------------------
def get_device_id():
    try:
        volume_info = subprocess.check_output("wmic diskdrive get serialnumber", shell=True)
        serial_numbers = volume_info.decode().split('\n')[1:]
        serial_number = ''.join(serial_numbers).strip()
        if not serial_number:
            mac_info = subprocess.check_output("getmac", shell=True)
            mac_address = mac_info.decode().split('\n')[1].split()[0]
            return hashlib.md5(mac_address.encode()).hexdigest()
        return hashlib.md5(serial_number.encode()).hexdigest()
    except:
        return "default_device_id"

# ---------------------------- 卡密管理 ----------------------------
class CardKeyManager:
    def __init__(self):
        self.used_keys_file = "used_keys.json"
        self.device_id = get_device_id()
        self.used_keys = self.load_used_keys()
    
    def load_used_keys(self):
        if os.path.exists(self.used_keys_file):
            try:
                with open(self.used_keys_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_used_keys(self):
        with open(self.used_keys_file, 'w') as f:
            json.dump(self.used_keys, f)
        if os.name == 'nt':
            try:
                subprocess.call(f'attrib +h "{self.used_keys_file}"', shell=True)
            except:
                pass
    
    def is_key_used(self, key):
        if key in self.used_keys:
            return self.used_keys[key] == self.device_id
        return False
    
    def mark_key_used(self, key):
        self.used_keys[key] = self.device_id
        self.save_used_keys()

card_key_manager = CardKeyManager()

# ---------------------------- 反调试/反虚拟机检测 ----------------------------
def is_debugger_present():
    """检测是否有调试器附加"""
    try:
        kernel32 = ctypes.windll.kernel32
        # IsDebuggerPresent
        if kernel32.IsDebuggerPresent():
            return True
        # CheckRemoteDebuggerPresent
        hProcess = kernel32.GetCurrentProcess()
        pbDebuggerPresent = ctypes.c_bool(False)
        kernel32.CheckRemoteDebuggerPresent(hProcess, ctypes.byref(pbDebuggerPresent))
        if pbDebuggerPresent.value:
            return True
        # NtQueryInformationProcess 检测 ProcessDebugPort
        ntdll = ctypes.windll.ntdll
        PROCESS_DEBUG_PORT = 7
        debug_port = ctypes.c_ulong()
        size = ctypes.sizeof(debug_port)
        ret = ntdll.NtQueryInformationProcess(hProcess, PROCESS_DEBUG_PORT, ctypes.byref(debug_port), size, None)
        if ret == 0 and debug_port.value != 0:
            return True
    except:
        pass
    return False

def is_vm_environment():
    """检测是否运行在虚拟机中（简单检查）"""
    # 检查常见虚拟机进程
    vm_processes = ['vmtoolsd.exe', 'vboxservice.exe', 'vboxtray.exe', 'xenservice.exe', 'prl_tools.exe']
    for proc in psutil.process_iter(['name']):
        name = proc.info['name']
        if name and name.lower() in vm_processes:
            return True
    # 检查特定文件
    vm_files = [
        r"C:\windows\System32\drivers\vmmouse.sys",
        r"C:\windows\System32\drivers\vmhgfs.sys",
        r"C:\windows\System32\drivers\VBoxGuest.sys"
    ]
    for f in vm_files:
        if os.path.exists(f):
            return True
    # 检查注册表（VMware/VirtualBox标识）
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\Scsi\Scsi Port 0\Scsi Bus 0\Target Id 0\Logical Unit 0")
        value, _ = winreg.QueryValueEx(key, "Identifier")
        if "VMWARE" in value.upper() or "VBOX" in value.upper():
            return True
    except:
        pass
    return False

# ---------------------------- 守护进程管理 ----------------------------
def add_to_startup():
    """添加注册表启动项（当前用户）"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_SET_VALUE)
        executable = sys.executable
        script = os.path.abspath(__file__)
        command = f'"{executable}" "{script}"'
        winreg.SetValueEx(key, "CompanionplaySystem", 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"注册表自启动设置失败: {e}")

def start_daemon(main_pid):
    """启动守护进程（隐藏窗口）"""
    try:
        # 使用CREATE_NO_WINDOW标志隐藏控制台窗口
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        proc = subprocess.Popen(
            [sys.executable, __file__, "--daemon", str(main_pid)],
            creationflags=subprocess.CREATE_NO_WINDOW,
            startupinfo=startupinfo
        )
        # 保存守护进程PID
        with open(DAEMON_PID_FILE, 'w') as f:
            f.write(str(proc.pid))
        return proc.pid
    except Exception as e:
        print(f"启动守护进程失败: {e}")
        return None

def stop_daemon():
    """停止守护进程"""
    try:
        if os.path.exists(DAEMON_PID_FILE):
            with open(DAEMON_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 9)  # 强制终止
            os.remove(DAEMON_PID_FILE)
    except:
        pass

def monitor_daemon(main_pid):
    """在主进程中监控守护进程，若消失则重新启动"""
    while True:
        time.sleep(5)
        try:
            if os.path.exists(DAEMON_PID_FILE):
                with open(DAEMON_PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                # 检查进程是否存在
                os.kill(pid, 0)  # 信号0仅测试存在性
            else:
                # PID文件丢失，重新启动
                start_daemon(main_pid)
        except (OSError, IOError, ValueError):
            # 进程不存在或文件错误，重新启动
            start_daemon(main_pid)

def daemon_loop(main_pid):
    """守护进程主循环：等待主进程结束，然后重启主进程"""
    # 创建互斥体防止多个守护进程
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexA(None, False, MUTEX_DAEMON.encode())
    if mutex and kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        return  # 已有守护进程运行

    # 打开主进程句柄
    PROCESS_QUERY_INFORMATION = 0x0400
    SYNCHRONIZE = 0x00100000
    hProcess = kernel32.OpenProcess(SYNCHRONIZE, False, main_pid)
    if not hProcess:
        # 主进程可能已经结束，直接重启
        subprocess.Popen([sys.executable, __file__])
        return

    # 等待主进程结束
    kernel32.WaitForSingleObject(hProcess, 0xFFFFFFFF)  # INFINITE
    kernel32.CloseHandle(hProcess)

    # 主进程已终止，重启主进程（不带daemon参数）
    subprocess.Popen([sys.executable, __file__])
    # 守护进程自身退出（新的主进程会启动新的守护进程）

# ---------------------------- 主程序类 ----------------------------
class AntiCloseApp:
    def __init__(self, root):
        # 先进行环境检测（仅在主进程中执行）
        if is_debugger_present():
            messagebox.showerror("错误", "检测到调试器，程序退出。")
            os._exit(1)
        if is_vm_environment():
            messagebox.showerror("错误", "检测到虚拟机环境，程序退出。")
            os._exit(1)

        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 设置窗口大小和位置
        self.root.geometry("400x400+500+300")
        self.root.resizable(False, False)
        self.root.minsize(400, 400)
        self.root.maxsize(400, 400)

        # 移除最小化/最大化按钮
        self.root.attributes('-toolwindow', True)
        self.root.attributes('-topmost', True)

        # 绑定事件
        self.root.bind("<Unmap>", self.on_minimize_attempt)
        self.root.bind("<FocusOut>", self.on_focus_out)

        # 主界面
        self.label = tk.Label(root, text="都不陪的！！！", font=("Arial", 24))
        self.label.pack(pady=20)

        # 协议框架
        self.agreement_frame = tk.Frame(root)
        self.agreement_frame.pack(pady=(0, 15))

        self.agreement_var = tk.BooleanVar(value=False)
        self.agreement_viewed = False
        self.checkbox_click_count = 0
        self.last_click_time = 0

        self.agreement_check = tk.Checkbutton(
            self.agreement_frame,
            variable=self.agreement_var,
            command=self.on_checkbox_click
        )
        self.agreement_check.pack(side=tk.LEFT, padx=(0, 5))

        self.agreement_button = tk.Button(
            self.agreement_frame,
            text="用户协议",
            font=("Arial", 10),
            command=self.show_agreement_window
        )
        self.agreement_button.pack(side=tk.LEFT)

        self.play_button = tk.Button(
            root, text="立即陪玩",
            font=("Arial", 14),
            command=self.show_play_window,
            bg="#4CAF50",
            fg="white",
            height=2,
            width=15,
            state=tk.DISABLED
        )
        self.play_button.pack(pady=10)

        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
        self.monitor_thread.start()

        self.window_monitor_thread = threading.Thread(target=self.monitor_window_state, daemon=True)
        self.window_monitor_thread.start()

    def on_minimize_attempt(self, event=None):
        self.root.deiconify()
        self.root.attributes('-topmost', True)
        messagebox.showwarning("警告", "不允许最小化程序！")

    def on_focus_out(self, event=None):
        self.root.attributes('-topmost', True)

    def monitor_window_state(self):
        while True:
            try:
                if self.root.state() == 'iconic':
                    self.root.deiconify()
                self.root.attributes('-topmost', True)
                self.root.lift()
            except Exception:
                pass
            time.sleep(0.5)

    def on_checkbox_click(self):
        if not self.agreement_viewed and self.agreement_var.get():
            self.agreement_var.set(False)
            messagebox.showwarning("警告", "必须浏览用户协议才可继续！")
            return
        current_time = time.time()
        if current_time - self.last_click_time < 0.5:
            self.checkbox_click_count += 1
        else:
            self.checkbox_click_count = 1
        self.last_click_time = current_time
        if self.checkbox_click_count >= 8:
            self.checkbox_click_count = 0
            self.show_change_password_window()
        if self.agreement_var.get():
            self.play_button.config(state=tk.NORMAL, bg="#4CAF50")
        else:
            self.play_button.config(state=tk.DISABLED, bg="#cccccc")

    def show_change_password_window(self):
        pwd_window = tk.Toplevel(self.root)
        pwd_window.title("修改退出密码")
        pwd_window.geometry("300x150+550+350")
        pwd_window.resizable(False, False)
        pwd_window.transient(self.root)
        pwd_window.grab_set()
        pwd_window.attributes('-topmost', True)

        tk.Label(pwd_window, text="请输入新密码:").pack(pady=10)
        pwd_entry = tk.Entry(pwd_window, show="*")
        pwd_entry.pack(pady=5)
        pwd_entry.focus_set()

        def save_password():
            new_password = pwd_entry.get().strip()
            if new_password:
                global PASSWORD
                PASSWORD = new_password
                pwd_window.destroy()
                messagebox.showinfo("成功", "密码已修改！")

        tk.Button(pwd_window, text="确定", command=save_password).pack(side=tk.LEFT, padx=40)
        tk.Button(pwd_window, text="取消", command=pwd_window.destroy).pack(side=tk.RIGHT, padx=40)
        pwd_window.protocol("WM_DELETE_WINDOW", pwd_window.destroy)
        self.root.wait_window(pwd_window)

    def show_agreement_window(self):
        agreement_window = tk.Toplevel(self.root)
        agreement_window.title("用户协议")
        agreement_window.geometry("450x250+550+350")
        agreement_window.resizable(False, False)
        agreement_window.transient(self.root)
        agreement_window.grab_set()
        agreement_window.attributes('-topmost', True)

        agreement_text = """
必须点击"立即陪玩"才能关闭本程序。
按下"立即陪玩"需要每日陪玩3.5小时。
按下"立即陪玩"必须遵守用户协议。"""

        tk.Label(
            agreement_window,
            text=agreement_text,
            font=("Arial", 12),
            justify=tk.LEFT,
            padx=20,
            pady=20
        ).pack(fill=tk.BOTH, expand=True)

        tk.Button(
            agreement_window,
            text="确定",
            font=("Arial", 12),
            command=lambda: self.close_agreement_window(agreement_window),
            bg="#2196F3",
            fg="white",
            height=1,
            width=8
        ).pack(pady=(0, 15))
        agreement_window.protocol("WM_DELETE_WINDOW", lambda: self.close_agreement_window(agreement_window))

    def close_agreement_window(self, window):
        self.agreement_viewed = True
        window.destroy()

    def show_play_window(self):
        play_window = tk.Toplevel(self.root)
        play_window.title("陪玩")
        play_window.geometry("350x200+550+350")
        play_window.resizable(False, False)
        play_window.transient(self.root)
        play_window.grab_set()
        play_window.attributes('-topmost', True)

        tk.Label(
            play_window,
            text="陪玩！\n（不能在别人不空闲时才陪玩）\n（欺骗我就不和你玩了！！！）",
            font=("Arial", 12)
        ).pack(pady=20)

        tk.Button(
            play_window,
            text="OK",
            font=("Arial", 12),
            command=lambda: self.quit_program(play_window),
            bg="#2196F3",
            fg="white",
            height=2,
            width=10
        ).pack(pady=10)
        play_window.protocol("WM_DELETE_WINDOW", play_window.destroy)

    def quit_program(self, window=None):
        """正常退出程序（验证通过后调用）"""
        if window:
            window.destroy()
        # 停止守护进程，避免重启
        stop_daemon()
        self.root.destroy()
        os._exit(0)

    def on_close(self):
        self.show_unlock_choice()

    def show_unlock_choice(self):
        choice_window = tk.Toplevel(self.root)
        choice_window.title("解锁方式")
        choice_window.geometry("300x150+550+350")
        choice_window.resizable(False, False)
        choice_window.transient(self.root)
        choice_window.grab_set()
        choice_window.attributes('-topmost', True)

        tk.Label(choice_window, text="请选择解锁方式:", font=("Arial", 12)).pack(pady=15)
        button_frame = tk.Frame(choice_window)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="密码退出",
            command=lambda: self.password_unlock(choice_window),
            width=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="卡密临时解锁",
            command=lambda: self.cardkey_unlock(choice_window),
            width=10
        ).pack(side=tk.RIGHT, padx=10)

        choice_window.protocol("WM_DELETE_WINDOW", choice_window.destroy)

    def password_unlock(self, choice_window):
        choice_window.destroy()
        password = self.get_password()
        if password == PASSWORD:
            self.quit_program()
        else:
            messagebox.showerror("错误", "密码错误！")

    def cardkey_unlock(self, choice_window):
        choice_window.destroy()
        cardkey_window = tk.Toplevel(self.root)
        cardkey_window.title("卡密解锁")
        cardkey_window.geometry("300x150+550+350")
        cardkey_window.resizable(False, False)
        cardkey_window.transient(self.root)
        cardkey_window.grab_set()
        cardkey_window.attributes('-topmost', True)

        tk.Label(cardkey_window, text="请输入卡密:").pack(pady=10)
        cardkey_entry = tk.Entry(cardkey_window, width=20)
        cardkey_entry.pack(pady=5)
        cardkey_entry.focus_set()

        def verify_cardkey():
            input_key = cardkey_entry.get().strip()
            if input_key not in CARD_KEYS:
                messagebox.showerror("错误", "卡密无效！")
                cardkey_entry.delete(0, tk.END)
                return
            if card_key_manager.is_key_used(input_key):
                messagebox.showerror("错误", "此卡密已在本设备使用过！")
                cardkey_entry.delete(0, tk.END)
                return
            card_key_manager.mark_key_used(input_key)
            cardkey_window.destroy()
            self.quit_program()

        tk.Button(cardkey_window, text="确定", command=verify_cardkey).pack(pady=10)
        cardkey_window.protocol("WM_DELETE_WINDOW", cardkey_window.destroy)

    def get_password(self):
        password_dialog = tk.Toplevel(self.root)
        password_dialog.title("密码验证")
        password_dialog.geometry("300x150+550+350")
        password_dialog.resizable(False, False)
        password_dialog.transient(self.root)
        password_dialog.grab_set()
        password_dialog.attributes('-topmost', True)

        tk.Label(password_dialog, text="请输入密码:").pack(pady=10)
        password_entry = tk.Entry(password_dialog, show="*")
        password_entry.pack(pady=5)
        password_entry.focus_set()
        result = {"value": None}

        def check_password():
            result["value"] = password_entry.get()
            password_dialog.destroy()

        tk.Button(password_dialog, text="确定", command=check_password).pack(pady=10)
        password_dialog.protocol("WM_DELETE_WINDOW", password_dialog.destroy)
        self.root.wait_window(password_dialog)
        return result["value"]

    def monitor_system(self):
        while True:
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'].lower() if proc.info['name'] else ''
                if proc_name in ['taskmgr.exe', 'cmd.exe', 'powershell.exe', 'powershell_ise.exe']:
                    try:
                        proc.kill()
                    except:
                        pass
            if self.is_shutting_down():
                messagebox.showerror("警告", "不陪玩别想关机！")
                self.abort_shutdown()
            time.sleep(1)

    def is_shutting_down(self):
        try:
            return ctypes.windll.user32.GetSystemMetrics(0x2000) != 0
        except:
            return False

    def abort_shutdown(self):
        try:
            subprocess.run(["shutdown", "/a"], shell=True)
        except:
            pass

# ---------------------------- 主入口 ----------------------------
if __name__ == "__main__":
    # 隐藏控制台窗口（仅Windows）
    try:
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
    except:
        pass

    # 处理命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        # 守护进程模式
        if len(sys.argv) > 2:
            main_pid = int(sys.argv[2])
            daemon_loop(main_pid)
        sys.exit(0)
    else:
        # 主进程模式
        # 创建互斥体防止多开
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexA(None, False, MUTEX_MAIN.encode())
        if mutex and kernel32.GetLastError() == 183:  # 已存在实例
            messagebox.showerror("错误", "程序已经在运行中！")
            sys.exit(1)

        # 添加开机自启动
        add_to_startup()

        # 启动守护进程（传入当前PID）
        main_pid = os.getpid()
        start_daemon(main_pid)

        # 启动监控线程，监视守护进程
        threading.Thread(target=monitor_daemon, args=(main_pid,), daemon=True).start()

        # 运行主程序
        root = tk.Tk()
        app = AntiCloseApp(root)
        root.mainloop()
