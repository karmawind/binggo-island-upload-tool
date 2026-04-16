# Runtime Requirements — weibo

## 必要条件
- Chrome 浏览器（用于 CDP 连接）
- Chrome 必须以远程调试模式启动：`chrome.exe --remote-debugging-port=9222`
- 已通过 `sau weibo login --account <name> --headed` 完成登录

## Cookie 文件
- 存储路径：`cookies/weibo_<account>.json`
- Cookie 域名覆盖：`.weibo.cn`、`.weibo.com`、`.sina.com.cn`
- 使用移动版 `m.weibo.cn` 发帖
