package burp

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
)

func BurpUnlocker(drvice string, dic []string) string {
	fmt.Printf("开始暴力破解，盘符: %s，字典大小: %d\n", drvice, len(dic))
	
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	var success atomic.Bool
	var foundPassword string
	var passwordMu sync.Mutex

	type job struct {
		idx int
		pwd string
	}
	jobs := make(chan job, len(dic))
	const numWorkers = 4
	var wg sync.WaitGroup

	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					fmt.Printf("[Worker %d] 收到取消信号，退出\n", workerID)
					return
				case j, ok := <-jobs:
					if !ok {
						fmt.Printf("[Worker %d] 任务通道关闭，退出\n", workerID)
						return
					}
					if success.Load() {
						fmt.Printf("[Worker %d] 已有成功结果，跳过密码 %s\n", workerID, j.pwd)
						return
					}
					
					fmt.Printf("[Worker %d] 尝试第%d个密码: %s\n", workerID, j.idx, j.pwd)
					status := UnlockBitlocker(drvice, j.pwd)
					
					switch status {
					case "success":
						if success.CompareAndSwap(false, true) {
							passwordMu.Lock()
							foundPassword = j.pwd
							passwordMu.Unlock()
							fmt.Printf("[Worker %d] 成功找到密码: %s\n", workerID, j.pwd)
							cancel()
						}
						return
					case "wrong_password":
						fmt.Printf("[Worker %d] 第%d个密码错误: %s\n", workerID, j.idx, j.pwd)
					case "already_unlocked":
						if success.CompareAndSwap(false, true) {
							fmt.Printf("[Worker %d] 驱动器已解锁，无需继续尝试\n", workerID)
							cancel()
						}
						return
					default:
						fmt.Printf("[Worker %d] 未知状态: %s\n", workerID, status)
					}
				}
			}
		}(w)
	}

	fmt.Println("开始分发任务...")
	for i, pwd := range dic {
		select {
		case <-ctx.Done():
			fmt.Println("收到取消信号，停止分发任务")
			break
		case jobs <- job{idx: i, pwd: pwd}:
			fmt.Printf("分发任务: 第%d个密码 %s\n", i, pwd)
		}
	}
	close(jobs)
	fmt.Println("任务分发完成，等待工作线程结束...")
	
	wg.Wait()
	fmt.Println("所有工作线程已结束")

	if success.Load() {
		passwordMu.Lock()
		pwd := foundPassword
		passwordMu.Unlock()
		if pwd != "" {
			fmt.Printf("暴力破解成功，密码是: %s\n", pwd)
		} else {
			fmt.Println("驱动器已解锁")
		}
		return "success"
	}
	fmt.Println("暴力破解失败，未找到正确密码")
	return "failed"
}
