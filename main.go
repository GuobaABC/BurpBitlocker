package main

import (
	"burpbitlocker/burp"
	"burpbitlocker/dict"
	"fmt"
)

func main() {
	fmt.Println(" ______     __  __     ______     ______   ______     __     ______   __         ______     ______     __  __     ______     ______    ")
	fmt.Println("/\\  == \\   /\\ \\/\\ \\   /\\  == \\   /\\  == \\ /\\  == \\   /\\ \\   /\\__  _\\ /\\ \\       /\\  __ \\   /\\  ___\\   /\\ \\/ /    /\\  ___\\   /\\  == \\   ")
	fmt.Println("\\ \\  __<   \\ \\ \\_\\ \\  \\ \\  __<   \\ \\  _-/ \\ \\  __<   \\ \\ \\  \\/_/\\ \\/ \\ \\ \\____  \\ \\ \\/\\ \\  \\ \\ \\____  \\ \\  _\"-.  \\ \\  __\\   \\ \\  __<   ")
	fmt.Println(" \\ \\_____\\  \\ \\_____\\  \\ \\_\\ \\_\\  \\ \\_\\    \\ \\_____\\  \\ \\_\\    \\ \\_\\  \\ \\_____\\  \\ \\_____\\  \\ \\_____\\  \\ \\_\\ \\_\\  \\ \\_____\\  \\ \\_\\ \\_\\ ")
	fmt.Println("  \\/_____/   \\/_____/   \\/_/ /_/   \\/_/     \\/_____/   \\/_/     \\/_/   \\/_____/   \\/_____/   \\/_____/   \\/_/\\/_/   \\/_____/   \\/_/ /_/ ")
	fmt.Print("请输入盘符：")
	var drvice string
	fmt.Scanln(&drvice)
	status, _ := burp.CheckStatus(drvice)
	if status == "On" {
		fmt.Print("请输入字典路径：")
		var dict_name string
		fmt.Scanln(&dict_name)
		dic := dict.ReadDict(dict_name)
		end := burp.BurpUnlocker(drvice, dic)
		fmt.Println(end)
	} else if status == "Off" {
		fmt.Println("BitLocker 未开启，无需破解")
	} else {
		fmt.Println("未知状态，无法破解")
	}

	//等待程序结束
	fmt.Println("输入回车键退出")
	fmt.Scanln()
}
