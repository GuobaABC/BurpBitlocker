package burp

import (
	"fmt"
	"os/exec"
	"strings"
)

func UnlockBitlocker(drvice string, pwd string) string {
	cmdLine := fmt.Sprintf("$ErrorActionPreference = 'Stop'; try { $securePassword = ConvertTo-SecureString '%s' -AsPlainText -Force; Unlock-BitLocker -MountPoint '%s:' -Password $securePassword; Write-Host 'SUCCESS'; exit 0 } catch { Write-Host 'FAILED: $_'; exit 1 }", pwd, drvice)
	cmd_output, err := exec.Command("powershell", "-ExecutionPolicy", "Bypass", "-Command", cmdLine).Output()
	if err != nil {
		// 检查是否是已经解锁的错误
		if strings.Contains(string(cmd_output), "已解锁") || strings.Contains(err.Error(), "已解锁") {
			fmt.Printf("密码 %s: 驱动器已解锁\n", pwd)
			return "already_unlocked"
		}
		fmt.Printf("密码 %s: 解锁失败\n", pwd)
		return "wrong_password"
	}
	if strings.Contains(string(cmd_output), "SUCCESS") {
		fmt.Printf("密码 %s: 解锁成功!\n", pwd)
		return "success"
	}
	fmt.Printf("密码 %s: 解锁失败\n", pwd)
	return "wrong_password"
}
