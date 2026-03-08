import threading
import time
import traceback
import queue
from utils import is_admin, request_admin_permission, run_command, unlock_success, found_password, total_attempts
from drive_status import check_drive_status
from password_generator import get_custom_keywords, get_custom_dates, get_custom_years, generate_passwords
from unlock_worker import unlock_worker, test_specific_passwords


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
    
    # 获取自定义日期
    custom_dates = get_custom_dates()
    
    # 获取自定义年份范围
    start_year, end_year = get_custom_years()
    
    # 先测试关键密码
    quick_password = test_specific_passwords(drive_letter, custom_keywords, custom_dates)
    if quick_password:
        print(f"\n🎉 快速测试成功！密码: {quick_password}")
        input("\n按Enter键退出...")
        return
    
    # 生成密码队列
    password_queue, total_passwords = generate_passwords(custom_keywords, custom_dates, start_year, end_year)
    
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
        # 等待所有任务完成，定期检查解锁状态
        while not unlock_success:
            try:
                # 等待一小段时间，然后检查解锁状态
                password_queue.join(timeout=0.5)
                break
            except queue.Empty:
                continue
        
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
    if unlock_success and found_password:
        print(f"\n{'='*80}")
        print("🎉 登陆成功！")
        print(f"{'='*80}")
        print(f"🔑 密码: {found_password}")
        print(f"⏱️  耗时: {elapsed_time:.2f}秒")
        print(f"🚀 尝试次数: {total_attempts}")
        
        if elapsed_time > 0:
            print(f"📊 平均速度: {total_attempts/elapsed_time:.1f} 密码/秒")
        
        # 验证解锁状态
        print("\n🔍 验证解锁状态...")
        result = run_command(f'manage-bde -status {drive_letter}:')
        if "已解锁" in result.stdout or "Unlocked" in result.stdout.lower():
            print("✅ 驱动器已成功解锁")
        else:
            print("⚠ 密码验证成功，但状态未更新")
        
        print("\n📝 破解尝试过的密码已保存到 output.txt 文件中")
        print("\n✅ 您现在可以正常访问您的设备")
        
        input("\n按任意键退出...")
        return
    else:
        print(f"\n{'='*80}")
        print("📊 解锁尝试完成")
        print(f"{'='*80}")
        print(f"⏱️  总耗时: {elapsed_time:.2f}秒")
        print(f"🔑 尝试密码数: {total_attempts}")
        
        if elapsed_time > 0:
            print(f"🚀 平均速度: {total_attempts/elapsed_time:.1f} 密码/秒")
        
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
