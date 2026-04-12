<template>
  <div id="app">
    <el-container>
      <el-aside :width="isCollapse ? '64px' : '200px'">
        <div class="sidebar">
          <div class="logo">
            <div class="logo-icon">
              <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="32" height="32" rx="8" fill="url(#logo-grad)"/>
                <path d="M10 16l4 4 8-8" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                <defs><linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32"><stop stop-color="#f97316"/><stop offset="1" stop-color="#6366f1"/></linearGradient></defs>
              </svg>
            </div>
            <h2 v-show="!isCollapse">灵感岛</h2>
          </div>
          <el-menu
            :router="true"
            :default-active="activeMenu"
            :collapse="isCollapse"
            class="sidebar-menu"
            background-color="transparent"
            text-color="rgba(255,255,255,0.7)"
            active-text-color="#fff"
          >
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/account-management">
              <el-icon><User /></el-icon>
              <span>账号管理</span>
            </el-menu-item>
            <el-menu-item index="/material-management">
              <el-icon><Picture /></el-icon>
              <span>素材管理</span>
            </el-menu-item>
            <el-menu-item index="/publish-center">
              <el-icon><Upload /></el-icon>
              <span>发布中心</span>
            </el-menu-item>
            <el-menu-item index="/article-publish">
              <el-icon><EditPen /></el-icon>
              <span>图文发布</span>
            </el-menu-item>
            <el-menu-item index="/article-management">
              <el-icon><Document /></el-icon>
              <span>帖子管理</span>
            </el-menu-item>
            <el-menu-item index="/about">
              <el-icon><DataAnalysis /></el-icon>
              <span>关于</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-aside>
      <el-container>
        <el-header>
          <div class="header-content">
            <div class="header-left">
              <el-icon class="toggle-sidebar" @click="toggleSidebar"><Fold /></el-icon>
            </div>
            <div class="header-right">
              <!-- 账号信息已移除 -->
            </div>
          </div>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  HomeFilled, User, DataAnalysis,
  Fold, Picture, Upload, EditPen, Document
} from '@element-plus/icons-vue'

const route = useRoute()

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path
})

// 侧边栏折叠状态
const isCollapse = ref(false)

// 切换侧边栏折叠状态
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

#app {
  min-height: 100vh;
}

.el-container {
  height: 100vh;
}

.el-aside {
  background: $sidebar-gradient;
  color: #fff;
  height: 100vh;
  overflow: hidden;
  transition: width 0.3s ease;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.15);

  .sidebar {
    display: flex;
    flex-direction: column;
    height: 100%;

    .logo {
      height: 64px;
      padding: 0 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      overflow: hidden;

      .logo-icon {
        flex-shrink: 0;
        width: 36px;
        height: 36px;

        svg {
          width: 100%;
          height: 100%;
        }
      }

      h2 {
        color: #fff;
        font-size: 17px;
        font-weight: 700;
        white-space: nowrap;
        margin: 0;
        background: linear-gradient(135deg, #f97316, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }

    .sidebar-menu {
      border-right: none;
      flex: 1;
      padding: 8px;

      .el-menu-item {
        display: flex;
        align-items: center;
        border-radius: $border-radius-sm;
        margin-bottom: 2px;
        height: 44px;
        line-height: 44px;
        transition: all 0.2s ease;

        .el-icon {
          margin-right: 10px;
          font-size: 18px;
        }

        &.is-active {
          background: linear-gradient(135deg, rgba(249, 115, 22, 0.2), rgba(99, 102, 241, 0.2)) !important;
          color: #fff !important;
          font-weight: 600;

          .el-icon {
            color: #f97316;
          }
        }

        &:hover:not(.is-active) {
          background-color: rgba(255, 255, 255, 0.08) !important;
        }
      }
    }
  }
}

.el-header {
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  padding: 0;
  height: 60px;
  border-bottom: 1px solid #f5f5f4;

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 100%;
    padding: 0 20px;

    .header-left {
      .toggle-sidebar {
        font-size: 20px;
        cursor: pointer;
        color: $text-secondary;
        padding: 6px;
        border-radius: $border-radius-sm;
        transition: all 0.2s ease;

        &:hover {
          color: $primary-color;
          background-color: #fff7ed;
        }
      }
    }

    .header-right {
      .user-dropdown {
        display: flex;
        align-items: center;
        cursor: pointer;

        .username {
          margin: 0 8px;
          color: $text-regular;
        }

        .el-icon {
          font-size: 12px;
          color: $text-secondary;
        }
      }
    }
  }
}

.el-main {
  background-color: $bg-color-page;
  padding: 24px;
  overflow-y: auto;
}
</style>
