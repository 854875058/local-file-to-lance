<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">应用日志</h1>
      <p class="page-subtitle">查看系统运行日志和错误信息</p>
    </div>

    <div class="glass-card" style="margin-bottom: 1rem;">
      <el-row :gutter="16" align="middle">
        <el-col :span="6">
          <el-select v-model="logLines" @change="loadLogs">
            <el-option label="最后 100 行" :value="100" />
            <el-option label="最后 500 行" :value="500" />
            <el-option label="最后 1000 行" :value="1000" />
            <el-option label="最后 2000 行" :value="2000" />
          </el-select>
        </el-col>
        <el-col :span="18" style="text-align: right;">
          <el-button type="primary" :icon="Refresh" @click="loadLogs">刷新</el-button>
          <el-button :icon="Download" @click="downloadLogs">下载日志</el-button>
        </el-col>
      </el-row>
    </div>

    <div class="glass-card" v-loading="loading">
      <div v-if="logs" style="background: #1e293b; border-radius: 8px; padding: 1rem; overflow: auto; max-height: 70vh;">
        <pre style="color: #e2e8f0; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.85rem; margin: 0; line-height: 1.6;">{{ logs }}</pre>
      </div>
      <el-empty v-else description="暂无日志" :image-size="100" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const logs = ref('')
const logLines = ref(500)

const loadLogs = async () => {
  loading.value = true
  try {
    const response = await api.getLogs(logLines.value)
    logs.value = response.logs || '暂无日志'
  } catch (error) {
    console.error('加载日志失败:', error)
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

const downloadLogs = () => {
  if (!logs.value) {
    ElMessage.warning('暂无日志可下载')
    return
  }

  const blob = new Blob([logs.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `app_log_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('日志下载成功')
}

onMounted(() => {
  loadLogs()
})
</script>
