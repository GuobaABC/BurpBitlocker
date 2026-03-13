package burp

import (
	"fmt"
	"os/exec"
	"strings"
)

func CheckStatus(drive string) (string, error) {
	// PowerShell 脚本：仅输出 "On" 或 "Off"
	psScript := fmt.Sprintf(`
		$status = manage-bde -status %s: | Select-String 'BitLocker 版本'
		if ($status -match '无') {
			'Off'
		} else {
			'On'
		}
		`, drive)

	cmd := exec.Command("powershell", "-ExecutionPolicy", "Bypass", "-Command", psScript)
	output, err := cmd.Output()
	// fmt.Println(string(output))
	if err != nil {
		// 如果命令执行失败，尝试获取错误输出
		if exitErr, ok := err.(*exec.ExitError); ok {
			return "", fmt.Errorf("PowerShell 执行失败: %s", exitErr.Stderr)
		}
		return "", fmt.Errorf("执行命令失败: %v", err)
	}

	status := strings.TrimSpace(string(output))
	if status != "On" && status != "Off" {
		return "", fmt.Errorf("无法解析状态: %q", status)
	}
	return status, nil
}
