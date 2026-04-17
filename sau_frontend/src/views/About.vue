<template>
  <div class="about">
    <el-card class="about-card">
      <div class="about-header">
        <h1>灵感岛推文分发器</h1>
        <p class="version">v0.3.1</p>
      </div>

      <el-divider />

      <div class="about-section">
        <h3>系统简介</h3>
        <p>
          灵感岛推文分发器是一款面向内容创作者和运营人员的一站式内容分发工具。支持图文文章和视频内容一键发布到多个主流社交媒体平台，提供账号管理、素材管理、批量发布等完整工作流。
        </p>
      </div>

      <div class="about-section">
        <h3>支持平台</h3>
        <div class="platform-group">
          <p class="group-label">视频平台</p>
          <div class="platform-tags">
            <el-tag type="danger">抖音</el-tag>
            <el-tag type="success">快手</el-tag>
            <el-tag type="warning">视频号</el-tag>
            <el-tag type="info">小红书</el-tag>
          </div>
        </div>
        <div class="platform-group">
          <p class="group-label">图文平台</p>
          <div class="platform-tags">
            <el-tag>百家号</el-tag>
            <el-tag type="danger">什么值得买</el-tag>
            <el-tag type="warning">头条号</el-tag>
            <el-tag>携程</el-tag>
            <el-tag type="success">搜狐号</el-tag>
            <el-tag type="danger">微博</el-tag>
          </div>
        </div>
      </div>

      <div class="about-section">
        <h3>核心功能</h3>
        <ul class="feature-list">
          <li>10 平台账号管理（扫码登录 / CLI 登录 / Cookie 上传）</li>
          <li>视频素材上传与管理</li>
          <li>图文帖子编辑、保存草稿、一键发布</li>
          <li>帖子批量管理，多选批量发布</li>
          <li>视频一键多平台发布</li>
          <li>定时发布与批量发布</li>
          <li>发布任务进度实时跟踪</li>
          <li>Cookie 导入导出与自动校验</li>
          <li>CLI 命令行接口（支持 10 平台登录、校验、发布）</li>
        </ul>
      </div>

      <div class="about-section">
        <h3>发布须知</h3>
        <ul class="notice-list">
          <li class="notice-item">
            <el-tag type="danger" size="small" effect="dark">重要</el-tag>
            <span><strong>百家号发布需要图片</strong> — 百家号要求至少上传一张图片才能选择封面并发布，无图片的帖子会发布失败。CSV 导入时请务必填写"图片"列</span>
          </li>
          <li class="notice-item">
            <el-tag type="danger" size="small" effect="dark">重要</el-tag>
            <span><strong>百家号同账号间隔 3 分钟</strong> — 同一百家号账号连续发布会触发"操作过于频繁"，系统已自动处理（间隔 180 秒），排期时也建议间隔 3 分钟以上</span>
          </li>
          <li class="notice-item">
            <el-tag type="danger" size="small" effect="dark">重要</el-tag>
            <span><strong>微博无标题，需写正文</strong> — 微博是短文本平台，没有标题字段。CSV 导入时微博行标题留空，内容必须写在"正文"列</span>
          </li>
          <li class="notice-item">
            <el-tag type="warning" size="small" effect="dark">注意</el-tag>
            <span><strong>携程发布需填写地点</strong> — 携程游记要求至少一个地点，CSV"地点"列填写城市名即可（如"杭州"）</span>
          </li>
          <li class="notice-item">
            <el-tag type="warning" size="small" effect="dark">注意</el-tag>
            <span><strong>搜狐号使用真实 Chrome</strong> — 搜狐号通过 CDP 连接本地 Chrome 发帖（非模拟浏览器），系统会自动启动调试模式 Chrome，请确保已安装 Chrome 浏览器</span>
          </li>
          <li class="notice-item">
            <el-tag type="info" size="small" effect="dark">提示</el-tag>
            <span><strong>图文平台封面自动选取</strong> — 百家号、头条号、搜狐号的封面图均自动从正文配图中选取，无需单独上传封面</span>
          </li>
          <li class="notice-item">
            <el-tag type="info" size="small" effect="dark">提示</el-tag>
            <span><strong>Cookie 有效期</strong> — 各平台 Cookie 会过期，建议定期在账号管理页检查账号状态（状态图标变灰表示需要重新登录）</span>
          </li>
        </ul>
      </div>

      <div class="about-section">
        <h3>技术栈</h3>
        <div class="tech-tags">
          <el-tag effect="plain">Vue 3</el-tag>
          <el-tag effect="plain">Element Plus</el-tag>
          <el-tag effect="plain">Pinia</el-tag>
          <el-tag effect="plain">Flask</el-tag>
          <el-tag effect="plain">Patchright</el-tag>
          <el-tag effect="plain">SQLite</el-tag>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.about {
  max-width: 700px;
  margin: 0 auto;

  .about-card {
    .about-header {
      text-align: center;

      h1 {
        color: $text-primary;
        margin: 0 0 8px 0;
        font-size: 24px;
      }

      .version {
        color: $text-secondary;
        font-size: 14px;
        margin: 0;
      }
    }

    .about-section {
      margin-bottom: 24px;

      h3 {
        font-size: 16px;
        color: $text-primary;
        margin: 0 0 12px 0;
      }

      p {
        color: $text-secondary;
        line-height: 1.8;
        margin: 0;
      }

      .platform-group {
        margin-bottom: 12px;

        .group-label {
          font-size: 13px;
          color: $text-secondary;
          margin: 0 0 8px;
        }
      }

      .platform-tags,
      .tech-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .feature-list {
        margin: 0;
        padding-left: 20px;
        color: $text-secondary;
        line-height: 2;
      }

      .notice-list {
        margin: 0;
        padding: 0;
        list-style: none;

        .notice-item {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          margin-bottom: 12px;
          color: $text-secondary;
          line-height: 1.8;

          .el-tag {
            flex-shrink: 0;
            margin-top: 2px;
          }
        }
      }
    }
  }
}
</style>
