import subprocess
import threading
import queue
import time
from utils import unlock_success, found_password, total_attempts

# 全局变量
lock = threading.Lock()
start_time = 0


#  解锁工作线程
def unlock_worker(drive_letter, password_queue, total_passwords, thread_id):
    """解锁工作线程 - 使用PowerShell的Unlock-BitLocker命令"""
    global unlock_success, found_password, total_attempts, start_time
    
    # 打开 output.txt 文件以追加模式写入
    with open('output.txt', 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"开始破解尝试 - 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*80}\n")
    
    while not password_queue.empty() and not unlock_success:
        try:
            password = password_queue.get(timeout=0.1)
        except queue.Empty:
            break

        success = False
        
        # 记录尝试的密码到 output.txt
        with open('output.txt', 'a', encoding='utf-8') as f:
            f.write(f"尝试密码: {password}\n")
        
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
            
            # 不仅检查返回码，还要检查输出内容，确保确实解锁成功
            success = (result.returncode == 0) and ("SUCCESS" in result.stdout or "成功" in result.stdout)
            
            # 调试信息（前几次尝试）
            if total_attempts < 3 and thread_id == 0:
                print(f"[DEBUG] 线程{thread_id}尝试: {password}")
                print(f"[DEBUG] 返回码: {result.returncode}")
                if result.stdout:
                    print(f"[DEBUG] 输出: {result.stdout[:100]}")
                
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
            
            # 记录成功的密码到 output.txt
            with open('output.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"🎉 破解成功！\n")
                f.write(f"🔑 密码: {found_password}\n")
                f.write(f"⏱️  耗时: {elapsed:.2f}秒\n")
                f.write(f"🚀 尝试次数: {total_attempts}\n")
                f.write(f"📊 平均速度: {speed:.1f} 密码/秒\n")
                f.write(f"{'='*80}\n")
            
            # 解锁成功，立即退出函数
            return
        
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


#  测试特定密码 
def test_specific_passwords(drive_letter, custom_keywords, custom_dates):
    """测试一些最有可能的密码"""
    test_passwords = []
    # 生成测试密码：关键字 + 日期（带年份和不带年份）
    for kw in custom_keywords[:10]:
        for date in custom_dates[:3]:
            # 测试带年份的组合
            test_passwords.append(kw + "2007" + date)
            # 测试不带年份的组合
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
            
            # 不仅检查返回码，还要检查输出内容，确保确实解锁成功
            if result.returncode == 0 and ("成功" in result.stdout or "SUCCESS" in result.stdout):
                print(f"      🎉 成功！密码是: {password}")
                return password
            else:
                print(f"      ❌ 失败")
                
        except Exception as e:
            print(f"      ⚠ 错误: {e}")
    
    return None
