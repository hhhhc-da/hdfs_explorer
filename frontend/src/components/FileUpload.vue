<template>
  <div class="file-upload">
    <h3>📤 文件上传</h3>

    <!-- Remote target directory -->
    <div class="form-row">
      <label for="remote-dir">目标目录：</label>
      <input
        id="remote-dir"
        v-model="remoteDir"
        type="text"
        placeholder="HDFS 目标路径，如 /user/data"
      />
    </div>

    <!-- Drop zone -->
    <div
      class="drop-zone"
      :class="{ 'is-dragover': dragging }"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <p v-if="!selectedFile">拖拽文件到此处，或点击选择文件</p>
      <p v-else class="selected-info">
        已选择：<strong>{{ selectedFile.name }}</strong>
        ({{ formatSize(selectedFile.size) }})
      </p>
      <input
        ref="fileInput"
        type="file"
        class="file-input-hidden"
        @change="onFilePicked"
      />
    </div>

    <!-- Progress -->
    <div v-if="uploading" class="progress-bar">
      <div class="progress-fill" :style="{ width: progress + '%' }"></div>
    </div>
    <p v-if="uploading" class="progress-text">上传中 {{ progress }}%</p>

    <!-- Result message -->
    <div v-if="resultMessage" class="result-message" :class="{ success: uploadSuccess, error: !uploadSuccess }">
      {{ resultMessage }}
    </div>

    <!-- Buttons -->
    <div class="form-actions">
      <button
        class="btn-select"
        @click="$refs.fileInput.click()"
        :disabled="uploading"
      >
        选择文件
      </button>
      <button
        class="btn-upload"
        @click="startUpload"
        :disabled="!selectedFile || uploading"
      >
        {{ uploading ? '上传中...' : '开始上传' }}
      </button>
      <button
        v-if="selectedFile && !uploading"
        class="btn-clear"
        @click="clearSelection"
      >
        取消
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const emit = defineEmits(['uploaded'])

const remoteDir = ref('/')
const selectedFile = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const progress = ref(0)
const resultMessage = ref('')
const uploadSuccess = ref(false)
const fileInput = ref(null)

function onDrop(e) {
  dragging.value = false
  const files = e.dataTransfer.files
  if (files.length > 0) {
    selectedFile.value = files[0]
    resultMessage.value = ''
  }
}

function onFilePicked(e) {
  const files = e.target.files
  if (files.length > 0) {
    selectedFile.value = files[0]
    resultMessage.value = ''
  }
}

function clearSelection() {
  selectedFile.value = null
  progress.value = 0
  resultMessage.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

async function startUpload() {
  if (!selectedFile.value) return

  uploading.value = true
  progress.value = 0
  resultMessage.value = ''
  uploadSuccess.value = false

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const url = `${API_BASE}/api/upload?remote_dir=${encodeURIComponent(remoteDir.value)}`

    // 使用 XMLHttpRequest 以支持进度回调
    await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', url)

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          progress.value = Math.round((e.loaded / e.total) * 100)
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText))
        } else {
          let detail = xhr.statusText
          try {
            detail = JSON.parse(xhr.responseText).detail || detail
          } catch (_) {}
          reject(new Error(detail))
        }
      })

      xhr.addEventListener('error', () => reject(new Error('网络错误')))
      xhr.addEventListener('abort', () => reject(new Error('上传已取消')))

      xhr.send(formData)
    })

    uploadSuccess.value = true
    resultMessage.value = `文件 "${selectedFile.value.name}" 上传成功！`
    emit('uploaded')
    clearSelection()
  } catch (e) {
    uploadSuccess.value = false
    resultMessage.value = `上传失败: ${e.message}`
  } finally {
    uploading.value = false
  }
}

function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}
</script>

<style scoped>
.file-upload {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.file-upload h3 {
  margin: 0 0 16px;
  font-size: 17px;
  color: #303133;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.form-row label {
  font-weight: 600;
  color: #555;
  white-space: nowrap;
  font-size: 14px;
}

.form-row input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}
.form-row input:focus {
  border-color: #409eff;
}

.drop-zone {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 36px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 14px;
  position: relative;
}
.drop-zone:hover,
.drop-zone.is-dragover {
  border-color: #409eff;
  background: #ecf5ff;
}
.drop-zone p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
.drop-zone .selected-info {
  color: #303133;
}

.file-input-hidden {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.progress-bar {
  height: 6px;
  background: #ebeef5;
  border-radius: 3px;
  margin-bottom: 6px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 3px;
  transition: width 0.3s;
}
.progress-text {
  margin: 0 0 12px;
  color: #606266;
  font-size: 13px;
  text-align: center;
}

.result-message {
  padding: 10px 14px;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 14px;
}
.result-message.success {
  background: #f0f9eb;
  color: #67c23a;
}
.result-message.error {
  background: #fef0f0;
  color: #f56c6c;
}

.form-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.form-actions button {
  padding: 8px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-select {
  background: #f5f7fa;
  color: #606266;
  border: 1px solid #dcdfe6 !important;
}
.btn-select:hover:not(:disabled) {
  background: #ecf5ff;
  border-color: #b3d8ff !important;
}

.btn-upload {
  background: #409eff;
  color: #fff;
}
.btn-upload:hover:not(:disabled) {
  background: #337ecc;
}
.btn-upload:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-clear {
  background: #f56c6c;
  color: #fff;
}
.btn-clear:hover {
  background: #d9534f;
}
</style>
