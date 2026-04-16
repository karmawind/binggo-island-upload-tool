# Troubleshooting — weibo

## Cookie 相关
- **Cookie 失效**：运行 `sau weibo login --account <name> --headed` 重新登录
- **CDP 连接失败**：确保 Chrome 以 `--remote-debugging-port=9222` 启动
- **注入 cookie 后仍显示未登录**：微博认证涉及多个域名（.weibo.cn/.weibo.com/.sina.com.cn），确保 cookie 文件包含所有域名

## 发帖相关
- **发送按钮点击无效**：按钮是 `a.m-send-btn`，可能被 JS 拦截，已内置 JS 兜底点击
- **图片上传无反应**：检查图片格式（支持 jpg/jpeg/png/gif/webp/bmp），大小限制
- **正文截断**：微博限制约 2000 字，超出部分自动截断
- **图片超过 9 张**：自动截断为前 9 张
