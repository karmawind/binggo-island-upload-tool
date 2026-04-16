<template>
  <div class="about">
    <el-card class="about-card">
      <div class="about-header">
        <h1>灵感岛推文分发器</h1>
        <p class="version">v0.2.8</p>
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
    }
  }
}
</style>
