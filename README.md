# BitLocker暴力破解工具 Go重制版

## 说明

- 版本: v20260313
- 该工具基于BurpBitLocker项目，使用Go语言编写
- 该工具仅用于学习和研究，不建议在生产环境中使用

## 使用

- 管理员身份运行 `.exe`
- 输入要破解的盘符
- 输入字典路径
- 等待破解完成
- 系统环境目前只支持 **UTF-8** 编码
- 内置一个500个密码的小字典

## 功能

- 检查BitLocker是否开启
- 暴力破解BitLocker密码
- 重置BitLocker密码

## 与 Python 版本的区别

- 取消了字典生成功能
- 目前只有4个continue，可以到 `burp.go` 修改

## 捐赠渠道

<img width="639" height="681" alt="image" src="https://github.com/user-attachments/assets/2c465007-1feb-499f-a61c-27dea0006b81" />
