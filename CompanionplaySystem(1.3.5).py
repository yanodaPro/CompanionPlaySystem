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

# 初始密码设置
PASSWORD = "2002"
# 卡密设置（可以预设多个卡密）
CARD_KEYS = ["kdys-swax-458d", "plhz-nkcy-381s", "gwtq-zymv-645k", "nykp-sdjh-107t"]
WINDOW_TITLE = "都不陪的！！！"

# 获取设备唯一标识
def get_device_id():
    try:
        # 获取磁盘序列号作为设备标识
        volume_info = subprocess.check_output("wmic diskdrive get serialnumber", shell=True)
        serial_numbers = volume_info.decode().split('\n')[1:]  # 跳过标题行
        serial_number = ''.join(serial_numbers).strip()
        
        if not serial_number:
            # 备用方法：使用MAC地址
            mac_info = subprocess.check_output("getmac", shell=True)
            mac_address = mac_info.decode().split('\n')[1].split()[0]
            return hashlib.md5(mac_address.encode()).hexdigest()
        
        return hashlib.md5(serial_number.encode()).hexdigest()
    except:
        # 如果所有方法都失败，使用固定值（但会导致所有设备被视为同一设备）
        return "default_device_id"

# 卡密管理类
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
        # 保存后隐藏文件（仅Windows）
        if os.name == 'nt':
            try:
                # 设置文件属性为隐藏
                subprocess.call(f'attrib +h "{self.used_keys_file}"', shell=True)
            except:
                pass
    
    def is_key_used(self, key):
        # 检查卡密是否已被当前设备使用
        if key in self.used_keys:
            return self.used_keys[key] == self.device_id
        return False
    
    def mark_key_used(self, key):
        # 标记卡密为已使用
        self.used_keys[key] = self.device_id
        self.save_used_keys()

# 创建卡密管理器实例
card_key_manager = CardKeyManager()

class AntiCloseApp:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE) 
        self.root.protocol("WM_DELETE_WINDOW", self.on_close) 
        
        # 设置窗口大小和位置
        self.root.geometry("400x400+500+300") 
        self.root.resizable(False, False)
        self.root.minsize(400, 400)
        self.root.maxsize(400, 400)

        # 移除最小化按钮和最大化按钮
        self.root.attributes('-toolwindow', True)  # 移除最小化/最大化按钮
        
        # 设置窗口始终置顶，防止被其他窗口遮挡
        self.root.attributes('-topmost', True)
        
        # 监控窗口状态
        self.root.bind("<Unmap>", self.on_minimize_attempt)
        self.root.bind("<FocusOut>", self.on_focus_out)
        
        # 主界面
        self.label = tk.Label(root, text="都不陪的！！！", font=("Arial", 24))
        self.label.pack(pady=20) 

        # 协议框架
        self.agreement_frame = tk.Frame(root)
        self.agreement_frame.pack(pady=(0, 15)) 

        # 协议勾选框变量 
        self.agreement_var = tk.BooleanVar(value=False) 
        
        # 记录用户是否浏览过协议
        self.agreement_viewed = False

        # 连续点击计数器
        self.checkbox_click_count = 0
        self.last_click_time = 0 

        # 协议勾选框
        self.agreement_check = tk.Checkbutton(
            self.agreement_frame, 
            variable=self.agreement_var, 
            command=self.on_checkbox_click
        )
        self.agreement_check.pack(side=tk.LEFT, padx=(0, 5)) 

        # 用户协议按钮
        self.agreement_button = tk.Button(
            self.agreement_frame, 
            text="用户协议",
            font=("Arial", 10),
            command=self.show_agreement_window 
        )
        self.agreement_button.pack(side=tk.LEFT) 

        # 添加"立即陪玩"按钮
        self.play_button = tk.Button(
            root, text="立即陪玩",
            font=("Arial", 14),
            command=self.show_play_window, 
            bg="#4CAF50",
            fg="white",
            height=2,
            width=15,
            state=tk.DISABLED  # 初始禁用
        )
        self.play_button.pack(pady=10) 

        # 监控任务管理器和关机
        self.monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
        self.monitor_thread.start() 
        
        # 监控窗口状态的线程
        self.window_monitor_thread = threading.Thread(target=self.monitor_window_state, daemon=True)
        self.window_monitor_thread.start()

    def on_minimize_attempt(self, event=None):
        """当用户尝试最小化窗口时调用"""
        # 立即取消最小化
        self.root.deiconify()
        self.root.attributes('-topmost', True)  # 重新置顶
        messagebox.showwarning("警告", "不允许最小化程序！")

    def on_focus_out(self, event=None):
        """当窗口失去焦点时调用"""
        # 保持窗口置顶
        self.root.attributes('-topmost', True)

    def monitor_window_state(self):
        """持续监控窗口状态，确保不会被最小化或被遮挡"""
        while True:
            try:
                # 检查窗口是否被最小化
                if self.root.state() == 'iconic':
                    self.root.deiconify()
                
                # 确保窗口始终置顶
                self.root.attributes('-topmost', True)
                
                # 将窗口带到最前面
                self.root.lift()
                
            except Exception as e:
                print(f"窗口监控错误: {e}")
            
            time.sleep(0.5)  # 每0.5秒检查一次

    def on_checkbox_click(self):
        """处理复选框点击事件，用于检测连续点击次数"""
        # 如果用户没有浏览协议就尝试勾选
        if not self.agreement_viewed and self.agreement_var.get():
            self.agreement_var.set(False)
            messagebox.showwarning("警告", "必须浏览用户协议才可继续！")
            return
            
        current_time = time.time() 
        if current_time - self.last_click_time < 0.5:  # 0.5秒内连续点击
            self.checkbox_click_count += 1
        else:
            self.checkbox_click_count = 1
        self.last_click_time = current_time 

        if self.checkbox_click_count >= 8:
            self.checkbox_click_count = 0
            self.show_change_password_window() 

        # 原toggle_play_button功能保留 
        if self.agreement_var.get(): 
            self.play_button.config(state=tk.NORMAL, bg="#4CAF50")
        else:
            self.play_button.config(state=tk.DISABLED, bg="#cccccc")

    def show_change_password_window(self):
        """显示修改密码窗口"""
        pwd_window = tk.Toplevel(self.root) 
        pwd_window.title(" 修改退出密码")
        pwd_window.geometry("300x150+550+350") 
        pwd_window.resizable(False, False)
        pwd_window.transient(self.root) 
        pwd_window.grab_set() 
        pwd_window.attributes('-topmost', True)  # 子窗口也置顶

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
                messagebox.showinfo(" 成功", "密码已修改！") 

        tk.Button(pwd_window, text="确定", command=save_password).pack(side=tk.LEFT, padx=40)
        tk.Button(pwd_window, text="取消", command=pwd_window.destroy).pack(side=tk.RIGHT, padx=40) 

        pwd_window.protocol("WM_DELETE_WINDOW", pwd_window.destroy) 
        self.root.wait_window(pwd_window) 

    def toggle_play_button(self):
        """根据协议勾选状态切换按钮状态"""
        if self.agreement_var.get(): 
            self.play_button.config(state=tk.NORMAL, bg="#4CAF50")
        else:
            self.play_button.config(state=tk.DISABLED, bg="#cccccc")

    def show_agreement_window(self):
        """显示用户协议窗口"""
        agreement_window = tk.Toplevel(self.root) 
        agreement_window.title("  用户协议")
        agreement_window.geometry("450x250+550+350") 
        agreement_window.resizable(False, False)
        agreement_window.transient(self.root) 
        agreement_window.grab_set() 
        agreement_window.attributes('-topmost', True)  # 子窗口也置顶

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
        """关闭协议窗口并标记为已浏览"""
        self.agreement_viewed = True
        window.destroy()

    def show_play_window(self):
        """显示陪玩窗口"""
        play_window = tk.Toplevel(self.root) 
        play_window.title("  陪玩")
        play_window.geometry("350x200+550+350") 
        play_window.resizable(False, False)
        play_window.transient(self.root) 
        play_window.grab_set() 
        play_window.attributes('-topmost', True)  # 子窗口也置顶

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
        """退出程序"""
        if window:
            window.destroy() 
        self.root.destroy() 
        os._exit(0)

    def on_close(self):
        """主窗口关闭事件处理"""
        # 显示解锁方式选择窗口
        self.show_unlock_choice()

    def show_unlock_choice(self):
        """显示解锁方式选择窗口"""
        choice_window = tk.Toplevel(self.root)
        choice_window.title("解锁方式")
        choice_window.geometry("300x150+550+350")
        choice_window.resizable(False, False)
        choice_window.transient(self.root)
        choice_window.grab_set()
        choice_window.attributes('-topmost', True)  # 子窗口也置顶
        
        tk.Label(choice_window, text="请选择解锁方式:", font=("Arial", 12)).pack(pady=15)
        
        # 按钮框架
        button_frame = tk.Frame(choice_window)
        button_frame.pack(pady=10)
        
        # 密码退出按钮
        tk.Button(
            button_frame, 
            text="密码退出", 
            command=lambda: self.password_unlock(choice_window),
            width=10
        ).pack(side=tk.LEFT, padx=10)
        
        # 卡密解锁按钮
        tk.Button(
            button_frame, 
            text="卡密临时解锁", 
            command=lambda: self.cardkey_unlock(choice_window),
            width=10
        ).pack(side=tk.RIGHT, padx=10)
        
        choice_window.protocol("WM_DELETE_WINDOW", choice_window.destroy)
    
    def password_unlock(self, choice_window):
        """密码解锁方式"""
        choice_window.destroy()
        password = self.get_password() 
        if password == PASSWORD:
            self.root.destroy() 
        else:
            messagebox.showerror("  错误", "密码错误！") 
    
    def cardkey_unlock(self, choice_window):
        """卡密解锁方式"""
        choice_window.destroy()
        cardkey_window = tk.Toplevel(self.root)
        cardkey_window.title("卡密解锁")
        cardkey_window.geometry("300x150+550+350")
        cardkey_window.resizable(False, False)
        cardkey_window.transient(self.root)
        cardkey_window.grab_set()
        cardkey_window.attributes('-topmost', True)  # 子窗口也置顶
        
        tk.Label(cardkey_window, text="请输入卡密:").pack(pady=10)
        cardkey_entry = tk.Entry(cardkey_window, width=20)
        cardkey_entry.pack(pady=5)
        cardkey_entry.focus_set()
        
        def verify_cardkey():
            input_key = cardkey_entry.get().strip()
            
            # 检查卡密是否有效
            if input_key not in CARD_KEYS:
                messagebox.showerror("错误", "卡密无效！")
                cardkey_entry.delete(0, tk.END)
                return
                
            # 检查卡密是否已在本设备使用
            if card_key_manager.is_key_used(input_key):
                messagebox.showerror("错误", "此卡密已在本设备使用过！")
                cardkey_entry.delete(0, tk.END)
                return
                
            # 标记卡密为已使用
            card_key_manager.mark_key_used(input_key)
            cardkey_window.destroy()
            self.root.destroy()
        
        tk.Button(cardkey_window, text="确定", command=verify_cardkey).pack(pady=10)
        cardkey_window.protocol("WM_DELETE_WINDOW", cardkey_window.destroy)

    def get_password(self):
        """创建密码输入对话框"""
        password_dialog = tk.Toplevel(self.root) 
        password_dialog.title("  密码验证")
        password_dialog.geometry("300x150+550+350") 
        password_dialog.resizable(False, False)
        password_dialog.transient(self.root) 
        password_dialog.grab_set() 
        password_dialog.attributes('-topmost', True)  # 子窗口也置顶

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
        """监控系统进程和关机事件"""
        while True:
            # 检查任务管理器、cmd和powershell
            for proc in psutil.process_iter(['name']): 
                proc_name = proc.info['name'].lower() if proc.info['name'] else ''
                if proc_name in ['taskmgr.exe', 'cmd.exe', 'powershell.exe', 'powershell_ise.exe']: 
                    try:
                        proc.kill() 
                    except:
                        pass

            # 检查关机事件 
            if self.is_shutting_down(): 
                messagebox.showerror("  警告", "不陪玩别想关机！")
                self.abort_shutdown() 

            time.sleep(1) 

    def is_shutting_down(self):
        """检查系统是否正在关机"""
        try:
            return ctypes.windll.user32.GetSystemMetrics(0x2000) != 0
        except:
            return False

    def abort_shutdown(self):
        """取消关机操作"""
        try:
            subprocess.run(["shutdown", "/a"], shell=True)
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = AntiCloseApp(root)

    # 隐藏控制台窗口（仅Windows）
    try:
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
    except:
        pass 

    root.mainloop()