# 故障排查

## 升级弹窗阻塞

- 症状：页面卡在"立即体验"弹窗
- 解决：代码已自动处理，点击 `div.upgrade-tip-btn` 关闭

## JS 点击报 `btn.click is not a function`

- 症状：点击工具栏图片按钮时报错
- 原因：`svg.closest('button')` 返回的元素可能没有标准 `.click()` 方法
- 解决：统一使用 `dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))`

## 编辑器残留状态

- 症状：连续测试时出现不可预测的错误（标题重复、图片面板遮挡、发布失败）
- 原因：SPA 页面不刷新，上次的标题/正文/图片/遮罩面板残留在 DOM 中
- 解决：代码已自动处理，每次发布前调用 `clear_editor()` 彻底清空

## 正文图片上传后无法操作

- 症状：点击其他按钮被遮挡
- 原因：图片上传面板未关闭
- 解决：点击"插入正文"（`div.btn-item`）关闭面板

## 封面图设置

- 症状：找不到"添加长图"按钮或 file input
- 原因：封面图需通过工具栏图片按钮上传，不是独立的"添加长图"按钮
- 解决：通过 `svg.zicon-picture` → file input → 点击图片 → 确定此图 → 确认

## 创作声明 radio 无法点击

- 症状：`.click()` 报 Timeout，`div.mask` 拦截
- 解决：代码使用 JS `evaluate("el.click()")` 绕过遮罩

## 发布按钮被遮挡

- 症状：`.click()` 报 Timeout
- 解决：代码使用 JS `dispatchEvent(MouseEvent)` mousedown+mouseup+click 三连

## Cookie 失效

- 症状：被重定向到登录页
- 解决：重新执行 `sau smzdm login --account <name> --headed`

## 图片小于 500KB 上传失败

- smzdm 要求图片 500KB~8MB
- 小于 500KB 会警告但继续尝试
