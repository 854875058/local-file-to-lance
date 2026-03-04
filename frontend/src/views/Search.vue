<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">向量搜索</h1>
      <p class="page-subtitle">基于语义的智能检索，支持文本、图像、音频多模态搜索</p>
    </div>

    <div class="glass-card" style="margin-bottom: 2rem;">
      <el-row :gutter="16">
        <el-col :span="18">
          <el-input
            v-model="query"
            placeholder="输入搜索内容..."
            size="large"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="searchMode" size="large" style="width: 100%;">
            <el-option label="文本搜索" value="text" />
            <el-option label="图像搜索" value="image" />
          </el-select>
        </el-col>
      </el-row>

      <div style="margin-top: 1rem;">
        <el-button type="primary" size="large" @click="handleSearch" :loading="searching" :disabled="!query">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button size="large" @click="clearSearch">清空</el-button>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searching" style="text-align: center; padding: 3rem;">
      <el-icon class="is-loading" :size="40" color="#3b82f6"><Loading /></el-icon>
      <p style="margin-top: 1rem; color: #64748b;">正在搜索...</p>
    </div>

    <div v-else-if="results.length > 0">
      <div class="section-title">搜索结果 ({{ results.length }} 条)</div>
      <div v-for="(result, index) in results" :key="index" class="glass-card" style="margin-bottom: 1rem; border-left: 4px solid #3b82f6;">
        <el-row :gutter="16">
          <el-col :span="18">
            <div style="margin-bottom: 0.5rem;">
              <el-tag type="primary" size="small">{{ result.doc_type }}</el-tag>
              <span style="margin-left: 0.5rem; font-weight: 600; color: #1e3a5f;">{{ result.doc_name }}</span>
            </div>
            <div v-if="result.text" style="color: #475569; line-height: 1.6;">
              {{ result.text }}
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.85rem; color: #94a3b8;">
              <el-icon><Link /></el-icon>
              {{ result.source_uri }}
            </div>
          </el-col>
          <el-col :span="6" style="text-align: right;">
            <div style="font-size: 0.9rem; color: #64748b;">
              相似度
            </div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #2563eb;">
              {{ (1 - result.distance).toFixed(3) }}
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <el-empty v-else-if="searched" description="未找到相关结果" :image-size="150" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search, Loading, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const query = ref('')
const searchMode = ref('text')
const searching = ref(false)
const searched = ref(false)
const results = ref([])

const handleSearch = async () => {
  if (!query.value.trim()) {
    ElMessage.warning('请输入搜索内容')
    return
  }

  searching.value = true
  searched.value = false
  results.value = []

  try {
    const response = await api.search(query.value, searchMode.value, 10)

    if (response.success) {
      results.value = response.results
      searched.value = true

      if (results.value.length === 0) {
        ElMessage.info('未找到相关结果')
      } else {
        ElMessage.success(`找到 ${results.value.length} 条结果`)
      }
    } else {
      ElMessage.error(response.message || '搜索失败')
    }

  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败，请重试')
  } finally {
    searching.value = false
  }
}

const clearSearch = () => {
  query.value = ''
  results.value = []
  searched.value = false
}
</script>
