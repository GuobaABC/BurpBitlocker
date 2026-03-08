import ctypes
import sys
import subprocess

# 全局变量
unlock_success = False
found_password = None
total_attempts = 0


def is_admin():
    """检查是否以管理员身份运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def request_admin_permission():
    """请求管理员权限"""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)


def run_command(cmd, timeout=10, input_text=None):
    """执行系统命令，处理编码问题"""
    try:
        if isinstance(cmd, str):
            # 字符串命令使用shell执行
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                timeout=timeout,
                encoding='gbk',  # Windows中文编码
                errors='ignore',
                input=input_text
            )
        else:
            # 列表命令不使用shell
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                encoding='gbk',
                errors='ignore',
                input=input_text
            )
        return result
    except subprocess.TimeoutExpired:
        return type('obj', (object,), {'returncode': -2, 'stdout': '', 'stderr': '命令执行超时'})()
    except Exception as e:
        return type('obj', (object,), {'returncode': -1, 'stdout': '', 'stderr': str(e)})()
