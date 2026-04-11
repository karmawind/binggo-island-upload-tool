# 什么值得买自动发帖 — 成功分析报告

## 结论

在经过多轮调试后，什么值得买图文文章自动发布功能已成功通过端到端测试。成功的关键因素有两个：**JS 点击方式修复** 和 **编辑器状态清空**。

## 一、成功因素

### 1. 修复 JS 点击 bug（根本原因）

**问题**：`svg.zicon-picture` 工具栏图片按钮的点击代码使用了 `.click()` 方法，报错 `btn.click is not a function`。

**原因分析**：smzdm 页面的 DOM 结构中，`svg.zicon-picture` 的祖先元素不一定是有原生 `.click()` 方法的标准 DOM 节点。`Element.closest('button')` 可能返回非标准元素，或者返回值的 `.click()` 被框架覆盖/未继承。

**修复方案**：将所有 JS 点击统一改为 `dispatchEvent`：
```javascript
// 修复前（两处不同写法，都有问题）
// 写法1: btn.closest('button')?.click() || btn.click()
// 写法2: if (btn) { btn.click(); return; }

// 修复后（统一安全写法）
const svg = document.querySelector('svg.zicon-picture');
if (!svg) return;
const btn = svg.closest('button');
const target = btn || svg;
target.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
```

`dispatchEvent` 是 DOM EventTarget 的标准接口，所有 DOM 元素都支持，不受框架覆盖影响。

**影响范围**：
- `upload_images_to_content` — 点击工具栏图片按钮打开上传面板
- `upload_cover_image` — 点击工具栏图片按钮上传封面

### 2. 编辑器状态清空（关键流程保障）

**问题**：在 `--headed` 模式下连续测试时，浏览器复用了上一次的编辑器状态，残留的标题、正文、图片、遮罩面板导致后续操作不可预测。

**修复方案**：添加 `clear_editor()` 方法，在每次发布前彻底清空编辑器：
- 清空标题（Ctrl+A + Backspace）
- 清空正文 ProseMirror 内容（Ctrl+A + Backspace）
- 删除残留图片（移除 ProseMirror 内的 img 标签）
- 关闭所有弹窗/面板（3 次 Escape）
- 删除残留的遮罩面板 DOM（`.upload-container-scroll`, `.insert-wrap`, `.pic-upload-btn`, `.pics`）

### 3. 其他已验证的交互经验

| 操作 | 解决方案 |
|------|---------|
| 升级弹窗 | 自动点击 `div.upgrade-tip-btn` 关闭 |
| ProseMirror 正文填入 | `document.execCommand('insertHTML')` 一次性写入 |
| 图片上传面板 | 工具栏 `svg.zicon-picture` → `input[type=file].set_input_files()` |
| 图片插入正文 | 上传后必须点击"插入正文"（`div.btn-item`）关闭面板 |
| 封面图设置 | 点击上传的图片本身 → 确定此图 → 确认 |
| 创作声明 radio | `el.click()` via `evaluate()` 绕过 mask 遮罩 |
| 发布按钮 | `dispatchEvent(MouseEvent)` 三连（mousedown + mouseup + click） |
| 发布验证 | 检测页面文本含"提交成功"等关键词 |

## 二、干净编辑器 vs 残留编辑器对比

### 延续残留状态的失败模式

| 阶段 | 残留状态导致的问题 |
|------|-------------------|
| 标题填写 | 上次标题残留，`fill()` 可能追加而非替换 |
| 正文填写 | 上次正文+图片残留，ProseMirror 状态混乱 |
| 图片上传 | 上传面板（`.upload-container-scroll`、`.insert-wrap`）仍在 DOM 中，遮挡工具栏按钮 |
| 封面设置 | 已有封面图，再次操作可能找不到正确按钮或触发意外弹窗 |
| 发布 | 遮罩层叠加，按钮点击被拦截 |

### 干净编辑器的优势

| 阶段 | 干净状态的表现 |
|------|--------------|
| 标题填写 | `fill()` 直接替换空值，结果确定 |
| 正文填写 | ProseMirror 从空状态开始，`insertHTML` 行为可预测 |
| 图片上传 | 无残留面板遮挡，工具栏按钮可正常点击 |
| 封面设置 | 无已有封面干扰，流程按预期执行 |
| 发布 | 无遮罩层，发布按钮可正常触发 |

### 核心结论

> **浏览器自动化测试中，每次测试必须从已知的干净状态开始。残留状态会引入不可控变量，导致错误难以定位和复现。**

smzdm 编辑器尤其容易出现这个问题，因为：
1. 它是 SPA（单页应用），页面不刷新就保持状态
2. 图片上传会创建大量遮罩面板 DOM，即使视觉上关闭了，DOM 节点仍在
3. ProseMirror 编辑器维护内部状态模型，残留内容会影响后续写入

## 三、最终验证的完整发布流程

```
Cookie 校验 → 启动浏览器 → 导航编辑器 → 等待加载 → 关闭升级弹窗
→ 清空编辑器 → 填写标题 → 填写正文
→ 上传封面图（工具栏图片按钮 → file input → 点击图片设为封面 → 确定此图 → 确认）
→ 上传正文图片（工具栏图片按钮 → file input → 插入正文）
→ 设置创作声明 → 发布 → 验证"提交成功"
```

## 四、经验教训总结

1. **JS 点击优先用 `dispatchEvent`**：`.click()` 可能被框架覆盖或不存在，`dispatchEvent` 更可靠
2. **每次测试必须清空状态**：尤其是 SPA 页面，残留 DOM 和编辑器状态是 bug 的主要来源
3. **遇到问题先分析再重试**：不要盲目重试，先通过日志和页面状态定位根因
4. **遮罩层是常态而非例外**：smzdm 页面大量使用 `div.mask`、浮层面板，所有交互都要考虑被遮挡的可能
5. **`--headed` 模式用于调试，`--headless` 用于生产**：调试时观察页面状态，生产时信任已验证的流程
