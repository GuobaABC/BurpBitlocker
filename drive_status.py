from utils import run_command


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
