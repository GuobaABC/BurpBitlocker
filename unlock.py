import ctypes
import sys
import subprocess
import threading
import queue
import time
import os
import sys
import traceback

# 全局变量 
unlock_success = False
found_password = None
total_attempts = 0
lock = threading.Lock()
start_time = 0

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

#  系统命令执行函数 
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

#  解锁工作线程 
def unlock_worker(drive_letter, password_queue, total_passwords, thread_id):
    """解锁工作线程 - 使用PowerShell的Unlock-BitLocker命令"""
    global unlock_success, found_password, total_attempts, start_time
    
    while not password_queue.empty() and not unlock_success:
        try:
            password = password_queue.get(timeout=0.1)
        except queue.Empty:
            break

        success = False
        
        try:
            # 构建PowerShell脚本
            ps_script = f"""
            $ErrorActionPreference = 'Stop'
            try {{
                $securePassword = ConvertTo-SecureString '{password}' -AsPlainText -Force
                Unlock-BitLocker -MountPoint '{drive_letter}:' -Password $securePassword
                Write-Host "SUCCESS"
                exit 0
            }} catch {{
                Write-Host "FAILED: $_"
                exit 1
            }}
            """
            
            # 执行PowerShell命令
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                timeout=5,
                encoding='gbk',
                errors='ignore'
            )
            
            success = (result.returncode == 0)
            
            # 调试信息（前几次尝试）
            if total_attempts < 3 and thread_id == 0:
                print(f"[DEBUG] 线程{thread_id}尝试: {password}")
                print(f"[DEBUG] 返回码: {result.returncode}")
                if result.stdout:
                    print(f"[DEBUG] 输出: {result.stdout[:100]}")
                
        except Exception:
            success = False
        
        # 方法2: 如果PowerShell失败，尝试manage-bde交互模式（备用）
        if not success:
            try:
                # 使用communicate传递密码给manage-bde
                process = subprocess.Popen(
                    ['manage-bde', '-unlock', drive_letter + ':'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='gbk'
                )
                
                stdout, stderr = process.communicate(input=password + '\n', timeout=3)
                success = (process.returncode == 0)
                
            except Exception:
                success = False
        
        # 处理解锁结果
        if success:
            with lock:
                unlock_success = True
                found_password = password
                
                elapsed = time.time() - start_time
                speed = total_attempts / elapsed if elapsed > 0 else 0
                
                print(f"\n{'='*80}")
                print(f"🎉 解锁成功！")
                print(f"🔑 密码: {found_password}")
                print(f"⏱️  耗时: {elapsed:.2f}秒")
                print(f"🚀 尝试次数: {total_attempts}")
                print(f"📊 平均速度: {speed:.1f} 密码/秒")
                print(f"{'='*80}")
            
            # 清空队列，让其他线程停止
            with password_queue.mutex:
                password_queue.queue.clear()
                password_queue.all_tasks_done.notify_all()
                password_queue.unfinished_tasks = 0
        
        # 更新计数
        with lock:
            total_attempts += 1
            
            # 每100次或每5秒显示一次进度
            if total_attempts % 100 == 0 or (time.time() - start_time) % 5 < 0.1:
                progress = (total_attempts / total_passwords) * 100 if total_passwords > 0 else 0
                elapsed = time.time() - start_time
                
                if elapsed > 0:
                    speed = total_attempts / elapsed
                    remaining = total_passwords - total_attempts
                    eta = remaining / speed if speed > 0 and remaining > 0 else 0
                    
                    # 转换为时分秒格式
                    hours = int(eta // 3600)
                    minutes = int((eta % 3600) // 60)
                    seconds = int(eta % 60)
                    
                    print(f"📈 进度: {progress:.1f}% | 尝试: {total_attempts}/{total_passwords} | "
                          f"速度: {speed:.1f}/秒 | ETA: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        password_queue.task_done()

# ================ 驱动器状态检查 ================
def check_drive_status(drive_letter):
    """详细检查驱动器状态和加密情况"""
    print(f"\n🔍 检查驱动器 {drive_letter}: 状态...")
    
    # 1. 检查驱动器是否存在
    print("1. 检查驱动器访问权限...")
    dir_result = run_command(f'dir {drive_letter}: /A', timeout=5)
    if dir_result.returncode != 0:
        print(f"   ❌ 无法访问驱动器 {drive_letter}:，请确认驱动器已连接")
        return False
    print("   ✅ 驱动器可访问")
    
    # 2. 检查BitLocker状态
    print("\n2. 检查BitLocker状态...")
    status_result = run_command(f'manage-bde -status {drive_letter}:', timeout=10)
    if status_result.returncode != 0:
        print(f"   ⚠  manage-bde状态检查失败: {status_result.stderr[:200]}")
    else:
        status_text = status_result.stdout.lower()
        
        # 检查关键状态信息
        checks = {
            "已加密": "加密状态" in status_result.stdout or "已加密" in status_result.stdout,
            "加密进度": "加密进度" in status_result.stdout or "Encryption Progress" in status_text,
            "锁定状态": "已锁定" in status_result.stdout or "locked" in status_text
        }
        
        for check, result in checks.items():
            print(f"   {'✅' if result else '❌'} {check}")
        
        # 显示简要状态
        lines = status_result.stdout.split('\n')
        for line in lines[:15]:  # 显示前15行
            if any(keyword in line for keyword in ["状态", "State", "加密", "Encryption", "锁定", "Locked"]):
                print(f"      {line.strip()}")
    
    # 3. 检查保护器类型（关键！）
    print("\n3. 检查解锁保护器类型...")
    protectors_result = run_command(f'manage-bde -protectors -get {drive_letter}:', timeout=10)
    
    if protectors_result.returncode == 0:
        protectors_text = protectors_result.stdout
        
        # 检查保护器类型
        protector_types = {
            "密码": "密码" in protectors_text or "Password" in protectors_text,
            "恢复密钥": "数字密码" in protectors_text or "Numerical Password" in protectors_text,
            "TPM": "TPM" in protectors_text,
            "证书": "证书" in protectors_text or "Certificate" in protectors_text
        }
        
        print("   保护器类型:")
        for ptype, found in protector_types.items():
            print(f"      {'✅' if found else '❌'} {ptype}")
        
        # 显示保护器详情
        if protector_types["密码"]:
            print("   ✅ 驱动器使用密码保护，可以尝试密码破解")
            return True
        else:
            print("   ❌ 驱动器未使用密码保护，请使用其他解锁方式")
            return False
    else:
        print(f"   ⚠ 无法获取保护器信息: {protectors_result.stderr[:200]}")
        # 继续尝试，但警告用户
        print("   ⚠ 将继续尝试，但可能无法成功")
        return True

# ================ 密码生成逻辑 ================
def get_custom_keywords():
    """获取用户自定义的关键字"""
    print("\n" + "="*80)
    print("🔑 自定义密码关键字配置")
    print("="*80)
    print("\n请输入密码关键字，输入 'exit' 结束输入")
    print("例如: zhang (回车) san (回车) exit (回车)")
    
    keywords = []
    print("\n开始输入关键字:")
    
    while True:
        user_input = input("  > ").strip()
        
        if user_input.lower() == 'exit':
            if len(keywords) == 0:
                print("❌ 必须至少输入一个关键字")
                continue
            break
        
        if user_input:
            keywords.append(user_input)
            print(f"  ✅ 添加: {user_input}")
    
    print(f"\n✅ 已添加 {len(keywords)} 个关键字:")
    for i, kw in enumerate(keywords, 1):
        print(f"   {i}. {kw}")
    
    confirm = input("\n确认使用这些关键字？(y/n): ").lower()
    if confirm == 'y':
        return keywords
    else:
        print("请重新输入...")
        return get_custom_keywords()

def generate_passwords(custom_keywords):
    """生成密码组合"""
    str1 = custom_keywords
    
    # 年份和两位数字
    str2 = [str(year) for year in range(2000, 2025)]
    str2.extend([f"{num:02d}" for num in range(0, 25)])
    
    # 特殊日期
    str3 = ["1229", "0223", "0406"]
    
    # 生成密码队列
    password_queue = queue.Queue()
    generated_count = 0
    
    print("\n🔑 生成密码组合...")
    
    # 组合1: str1 + str2 + str3
    print("  生成组合: 名字 + 年份/数字 + 日期")
    for p1 in str1:
        for p2 in str2:
            for p3 in str3:
                password_queue.put(p1 + p2 + p3)
                generated_count += 1
    
    # 组合2: str1 + str3
    print("  生成组合: 名字 + 日期")
    for p1 in str1:
        for p3 in str3:
            password_queue.put(p1 + p3)
            generated_count += 1
    
    total_passwords = password_queue.qsize()
    
    print(f"\n✅ 密码生成完成:")
    print(f"   总密码数: {total_passwords:,}")
    print(f"   组合方式: {len(str1)} × {len(str2)} × {len(str3)} + {len(str1)} × {len(str3)}")
    
    # 显示示例密码
    print("\n📋 密码示例:")
    samples = []
    temp_queue = queue.Queue()
    
    for _ in range(min(5, total_passwords)):
        pwd = password_queue.get()
        samples.append(pwd)
        temp_queue.put(pwd)
    
    # 还原队列
    while not temp_queue.empty():
        password_queue.put(temp_queue.get())
    
    for i, sample in enumerate(samples, 1):
        print(f"   {i}. {sample}")
    
    return password_queue, total_passwords

#  测试特定密码 
def test_specific_passwords(drive_letter, custom_keywords):
    """测试一些最有可能的密码"""
    test_passwords = []
    special_dates = ["20070406", "20071229", "20070223", "0406"]
    for kw in custom_keywords[:10]:
        for date in special_dates[:3]:
            test_passwords.append(kw + date)
    
    print(f"\n🎯 测试关键密码 ({len(test_passwords)}个)...")
    
    for i, password in enumerate(test_passwords, 1):
        print(f"\n  测试 {i}/{len(test_passwords)}: {password}")
        
        # 使用PowerShell测试
        ps_script = f"""
        $securePassword = ConvertTo-SecureString '{password}' -AsPlainText -Force
        try {{
            Unlock-BitLocker -MountPoint '{drive_letter}:' -Password $securePassword -ErrorAction Stop
            Write-Host "✅ 成功"
            exit 0
        }} catch {{
            Write-Host "❌ 失败"
            exit 1
        }}
        """
        
        try:
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                timeout=5,
                encoding='gbk'
            )
            
            if result.returncode == 0:
                print(f"      🎉 成功！密码是: {password}")
                return password
            else:
                print(f"      ❌ 失败")
                
        except Exception as e:
            print(f"      ⚠ 错误: {e}")
    
    return None

# ================ 主函数 ================
def main():
    global unlock_success, found_password, total_attempts, start_time
    
    # 检查管理员权限
    if not is_admin():
        print("🛡️ 需要管理员权限运行此工具")
        request_admin_permission()
    
    print("=" * 80)
    print("🔓 BitLocker密码恢复工具")
    print("=" * 80)
    
    # 获取驱动器盘符
    while True:
        drive_input = input("\n请输入要解锁的驱动器盘符 (例如 E): ").strip().upper()
        if drive_input and len(drive_input) == 1 and 'A' <= drive_input <= 'Z':
            drive_letter = drive_input
            break
        print("❌ 无效的盘符，请输入单个字母 (A-Z)")
    
    # 检查驱动器状态
    if not check_drive_status(drive_letter):
        choice = input("\n⚠ 驱动器可能不支持密码解锁，是否继续尝试？(y/n): ").lower()
        if choice != 'y':
            print("操作取消")
            return
    
    # 获取自定义关键字
    custom_keywords = get_custom_keywords()
    
    # 先测试关键密码
    quick_password = test_specific_passwords(drive_letter, custom_keywords)
    if quick_password:
        print(f"\n🎉 快速测试成功！密码: {quick_password}")
        input("\n按Enter键退出...")
        return
    
    # 生成密码队列
    password_queue, total_passwords = generate_passwords(custom_keywords)
    
    if total_passwords == 0:
        print("❌ 没有生成任何密码，请检查配置")
        return
    
    # 获取线程数量
    try:
        num_threads = int(input("\n请输入线程数量 (1-32，建议4-8): ").strip())
        num_threads = max(1, min(32, num_threads))
    except:
        num_threads = 4
        print(f"使用默认值: {num_threads} 线程")
    
    print(f"\n🚀 开始解锁尝试...")
    print("   提示: 按 Ctrl+C 可中断程序")
    print("-" * 80)
    
    # 记录开始时间
    start_time = time.time()
    
    # 创建并启动线程
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(
            target=unlock_worker,
            args=(drive_letter, password_queue, total_passwords, i),
            daemon=True,
            name=f"Worker-{i}"
        )
        thread.start()
        threads.append(thread)
    
    # 主线程监控
    try:
        # 等待所有任务完成
        password_queue.join()
        
    except KeyboardInterrupt:
        print("\n\n🛑 用户中断，正在停止...")
        unlock_success = True  # 设置标志让线程退出
        
        # 等待线程结束
        for thread in threads:
            thread.join(timeout=1)
    
    # 计算总耗时
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # 显示最终结果
    print(f"\n{'='*80}")
    print("📊 解锁尝试完成")
    print(f"{'='*80}")
    print(f"⏱️  总耗时: {elapsed_time:.2f}秒")
    print(f"🔑 尝试密码数: {total_attempts}")
    
    if elapsed_time > 0:
        print(f"🚀 平均速度: {total_attempts/elapsed_time:.1f} 密码/秒")
    
    if unlock_success and found_password:
        print(f"\n🎉 解锁成功！")
        print(f"🔑 密码: {found_password}")
        
        # 验证解锁状态
        print("\n🔍 验证解锁状态...")
        result = run_command(f'manage-bde -status {drive_letter}:')
        if "已解锁" in result.stdout or "Unlocked" in result.stdout.lower():
            print("✅ 驱动器已成功解锁")
        else:
            print("⚠ 密码验证成功，但状态未更新")
    else:
        print("\n❌ 未找到正确密码")
        print("\n可能原因:")
        print("1. 🔑 密码不在生成列表中")
        print("2. 🔢 驱动器使用恢复密钥（48位数字）而非密码")
        print("3. 🛡️  密码保护器被禁用")
        print("4. 💾 驱动器未启用BitLocker")
        print("5. ⚙️  系统配置问题")
    
    input("\n按Enter键退出...")

# ================ 程序入口 ================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序发生错误: {e}")
        traceback.print_exc()
        input("\n按Enter键退出...")