<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">文件上传</h1>
      <p class="page-subtitle">支持批量上传文本、图片、音频、视频等多模态文件</p>
    </div>

    <div class="glass-card">
      <el-upload
        ref="uploadRef"
        drag
        multiple
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        :limit="50"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击选择文件</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 txt, pdf, docx, pptx, jpg, png, mp3, wav, mp4 等格式，单次最多 50 个文件
          </div>
        </template>
      </el-upload>

      <div style="margin-top: 2rem; text-align: center;">
        <el-button type="primary" size="large" @click="submitUpload" :loading="uploading" :disabled="fileList.length === 0">
          <el-icon><Upload /></el-icon>
          开始上传 ({{ fileList.length }} 个文件)
        </el-button>
        <el-button size="large" @click="clearFiles" :disabled="fileList.length === 0">
          清空列表
        </el-button>
      </div>

      <el-progress
        v-if="uploading"
        :percentage="uploadProgress"
        :status="uploadStatus"
        style="margin-top: 1rem;"
      />

      <el-alert
        v-if="uploadMessage"
        :title="uploadMessage"
        :type="uploadMessageType"
        style="margin-top: 1rem;"
        show-icon
        closable
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const uploadRef = ref(null)
const fileList = ref([])
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const uploadMessage = ref('')
const uploadMessageType = ref('success')

const handleFileChange = (file, files) => {
  fileList.value = files
}

const clearFiles = () => {
  uploadRef.value.clearFiles()
  fileList.value = []
  uploadMessage.value = ''
}

const submitUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''
  uploadMessage.value = ''

  try {
    // 模拟进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    const files = fileList.value.map(f => f.raw)
    const result = await api.uploadFiles(files)

    clearInterval(progressInterval)
    uploadProgress.value = 100
    uploadStatus.value = 'success'

    if (result.success) {
      uploadMessage.value = result.message
      uploadMessageType.value = 'success'
      ElMessage.success('文件上传成功，正在后台处理')

      // 3秒后清空列表
      setTimeout(() => {
        clearFiles()
        uploadProgress.value = 0
      }, 3000)
    } else {
      uploadMessage.value = result.message
      uploadMessageType.value = 'error'
      uploadStatus.value = 'exception'
    }

  } catch (error) {
    console.error('上传失败:', error)
    uploadProgress.value = 100
    uploadStatus.value = 'exception'
    uploadMessage.value = `上传失败: ${error.message}`
    uploadMessageType.value = 'error'
    ElMessage.error('上传失败，请重试')
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.el-upload-dragger {
  border: 2px dashed rgba(59,130,246,0.25);
  border-radius: 14px;
  background: rgba(239,246,255,0.4);
  transition: all 0.3s;
}

.el-upload-dragger:hover {
  border-color: rgba(59,130,246,0.45);
  background: rgba(239,246,255,0.6);
}

.el-icon--upload {
  font-size: 67px;
  color: #3b82f6;
  margin: 40px 0 16px;
}
</style>
