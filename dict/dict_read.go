package dict

import (
	"fmt"
	"os"
	"strings"
)

func ReadDict(filePath string) []string {
	// 读取字典内容，暴力破解字典
	content, err := os.ReadFile(filePath)
	if err != nil {
		fmt.Println("Error:", err)
		return nil
	}
	// 按行分割内容
	lines := strings.Split(string(content), "\n")
	return lines
}
