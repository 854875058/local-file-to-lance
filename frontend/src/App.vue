<template>
  <div id="app">
    <el-container style="min-height: 100vh;">
      <!-- 侧边栏 -->
      <el-aside width="240px" style="background: linear-gradient(180deg, rgba(239,246,255,0.95) 0%, rgba(255,255,255,0.90) 50%, rgba(239,246,255,0.92) 100%); backdrop-filter: blur(18px); border-right: 1px solid rgba(147,197,253,0.25);">
        <div style="padding: 1.5rem 1rem;">
          <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="background: linear-gradient(135deg, #1e3a5f, #2563eb); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.5rem; margin: 0;">DataVerse Pro</h2>
            <p style="color: #64748b; font-size: 0.85rem; margin: 0.3rem 0 0 0;">多模态数据湖</p>
          </div>

          <el-menu
            :default-active="$route.path"
            router
            background-color="transparent"
            text-color="#1e3a5f"
            active-text-color="#2563eb"
          >
            <el-menu-item index="/dashboard">
              <el-icon><DataAnalysis /></el-icon>
              <span>仪表盘</span>
            </el-menu-item>
            <el-menu-item index="/upload">
              <el-icon><Upload /></el-icon>
              <span>文件上传</span>
            </el-menu-item>
            <el-menu-item index="/search">
              <el-icon><Search /></el-icon>
              <span>向量搜索</span>
            </el-menu-item>
            <el-menu-item index="/files">
              <el-icon><Folder /></el-icon>
              <span>文件管理</span>
            </el-menu-item>
            <el-menu-item index="/logs">
              <el-icon><Document /></el-icon>
              <span>应用日志</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-main style="padding: 2rem;">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { DataAnalysis, Upload, Search, Folder, Document } from '@element-plus/icons-vue'
</script>

<style scoped>
.el-menu-item {
  border-radius: 10px;
  margin: 0.3rem 0;
}

.el-menu-item:hover {
  background: rgba(59,130,246,0.06) !important;
}

.el-menu-item.is-active {
  background: rgba(59,130,246,0.10) !important;
  font-weight: 700;
}
</style>
