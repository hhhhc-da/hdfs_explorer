<template>
  <div class="app-container">
    <header class="app-header">
      <h1>🗄️ HDFS Explorer</h1>
      <span class="app-version">FastAPI + Vue3</span>
    </header>

    <main class="app-main">
      <section class="panel panel-browser">
        <h2>📂 文件浏览</h2>
        <FileBrowser ref="browserRef" />
      </section>

      <section class="panel panel-upload">
        <FileUpload @uploaded="onFileUploaded" />
      </section>
    </main>

    <footer class="app-footer">
      <p>HDFS 地址：<code>{{ hdfsUrl }}</code></p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import FileBrowser from './components/FileBrowser.vue'
import FileUpload from './components/FileUpload.vue'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const hdfsUrl = ref('—')
const browserRef = ref(null)

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/api/health`)
    const data = await res.json()
    hdfsUrl.value = data.hdfs === 'connected' ? '已连接' : `状态：${data.hdfs}`
  } catch {
    hdfsUrl.value = '无法连接后端'
  }
})

function onFileUploaded() {
  // 上传成功后刷新文件列表
  browserRef.value?.loadDirectory()
}
</script>

<style scoped>
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: baseline;
  gap: 16px;
  padding: 24px 0 16px;
  border-bottom: 2px solid #ebeef5;
  margin-bottom: 24px;
}

.app-header h1 {
  margin: 0;
  font-size: 26px;
  color: #303133;
}

.app-version {
  color: #909399;
  font-size: 13px;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.panel h2 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #606266;
}

.app-footer {
  text-align: center;
  padding: 20px 0;
  color: #909399;
  font-size: 13px;
  margin-top: auto;
}

.app-footer code {
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
}
</style>
