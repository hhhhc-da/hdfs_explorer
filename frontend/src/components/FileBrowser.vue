<template>
  <div class="file-browser">
    <!-- Breadcrumb / Current Path -->
    <div class="breadcrumb">
      <span class="path-label">当前路径：</span>
      <span class="path-segments">
        <template v-for="(seg, idx) in pathSegments" :key="idx">
          <a href="#" @click.prevent="navigateTo(idx)">{{ seg.label || '/' }}</a>
          <span class="separator" v-if="idx < pathSegments.length - 1">/</span>
        </template>
      </span>
      <button class="btn-refresh" @click="loadDirectory" :disabled="loading">
        🔄 刷新
      </button>
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="status-message">加载中...</div>
    <div v-else-if="error" class="status-message error">{{ error }}</div>

    <!-- File Table -->
    <table v-else class="file-table">
      <thead>
        <tr>
          <th class="col-name">名称</th>
          <th class="col-kind">类型</th>
          <th class="col-size">大小</th>
          <th class="col-time">修改时间</th>
          <th class="col-actions">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="parentPath !== null">
          <td colspan="5">
            <a href="#" class="parent-link" @click.prevent="navigateUp">📁 ..</a>
          </td>
        </tr>
        <tr v-for="item in items" :key="item.path" :class="{ 'is-dir': item.kind === 'directory' }">
          <td class="col-name">
            <span v-if="item.kind === 'directory'" class="icon">📁</span>
            <span v-else class="icon">📄</span>
            <a
              href="#"
              v-if="item.kind === 'directory'"
              @click.prevent="navigateToPath(item.path)"
              class="name-link"
            >
              {{ item.name }}
            </a>
            <span v-else class="file-name">{{ item.name }}</span>
          </td>
          <td class="col-kind">
            <span class="badge" :class="item.kind">
              {{ item.kind === 'directory' ? '目录' : '文件' }}
            </span>
          </td>
          <td class="col-size">{{ item.kind === 'directory' ? '-' : formatSize(item.size) }}</td>
          <td class="col-time">{{ item.modification_time || '-' }}</td>
          <td class="col-actions">
            <button
              v-if="item.kind === 'file'"
              class="btn-action btn-download"
              @click="downloadFile(item)"
            >
              下载
            </button>
            <button class="btn-action btn-delete" @click="deleteItem(item)">删除</button>
          </td>
        </tr>
        <tr v-if="items.length === 0 && parentPath === null">
          <td colspan="5" class="empty-msg">目录为空</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const currentPath = ref('/')
const items = ref([])
const loading = ref(false)
const error = ref(null)

// 将当前路径分解为面包屑片段
const pathSegments = computed(() => {
  const parts = currentPath.value.replace(/\/$/, '').split('/')
  return parts.map((p, i) => ({
    label: p || '根',
    path: parts.slice(0, i + 1).join('/') || '/',
  }))
})

// 父目录路径
const parentPath = computed(() => {
  const trimmed = currentPath.value.replace(/\/$/, '')
  if (!trimmed || trimmed === '/') return null
  const idx = trimmed.lastIndexOf('/')
  return idx === 0 ? '/' : trimmed.substring(0, idx)
})

onMounted(() => {
  loadDirectory()
})

async function loadDirectory() {
  loading.value = true
  error.value = null
  try {
    const url = `${API_BASE}/api/browse?path=${encodeURIComponent(currentPath.value)}`
    const res = await fetch(url)
    if (!res.ok) {
      const detail = (await res.json()).detail || res.statusText
      throw new Error(detail)
    }
    const data = await res.json()
    items.value = data.items
  } catch (e) {
    error.value = `加载失败: ${e.message}`
    items.value = []
  } finally {
    loading.value = false
  }
}

function navigateToPath(path) {
  currentPath.value = path
  loadDirectory()
}

function navigateTo(idx) {
  const seg = pathSegments.value[idx]
  currentPath.value = seg.path
  loadDirectory()
}

function navigateUp() {
  if (parentPath.value !== null) {
    currentPath.value = parentPath.value
    loadDirectory()
  }
}

async function downloadFile(item) {
  const url = `${API_BASE}/api/download?path=${encodeURIComponent(item.path)}`
  window.open(url, '_blank')
}

async function deleteItem(item) {
  const type = item.kind === 'directory' ? '目录' : '文件'
  if (!confirm(`确定要删除${type} "${item.name}" 吗？此操作不可撤销。`)) return
  try {
    const url = `${API_BASE}/api/delete?path=${encodeURIComponent(item.path)}`
    const res = await fetch(url, { method: 'DELETE' })
    if (!res.ok) {
      const detail = (await res.json()).detail || res.statusText
      throw new Error(detail)
    }
    loadDirectory()
  } catch (e) {
    alert(`删除失败: ${e.message}`)
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
.file-browser {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.path-label {
  font-weight: 600;
  color: #555;
  white-space: nowrap;
}

.path-segments a {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
}
.path-segments a:hover {
  text-decoration: underline;
}

.separator {
  color: #aaa;
  margin: 0 2px;
}

.btn-refresh {
  margin-left: auto;
  padding: 6px 14px;
  border: 1px solid #dcdfe6;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}
.btn-refresh:hover:not(:disabled) {
  background: #ecf5ff;
  border-color: #b3d8ff;
}

.status-message {
  padding: 40px;
  text-align: center;
  color: #909399;
  font-size: 15px;
}
.status-message.error {
  color: #f56c6c;
}

.file-table {
  width: 100%;
  border-collapse: collapse;
}

.file-table th {
  text-align: left;
  padding: 10px 12px;
  font-weight: 600;
  color: #606266;
  border-bottom: 2px solid #ebeef5;
  font-size: 13px;
  white-space: nowrap;
}

.file-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #ebeef5;
  font-size: 14px;
}

.file-table tr:hover td {
  background: #f5f7fa;
}

.col-name { width: auto; }
.col-kind { width: 80px; }
.col-size { width: 100px; }
.col-time { width: 160px; }
.col-actions { width: 140px; text-align: center; }

.icon {
  margin-right: 6px;
  font-size: 16px;
}

.name-link {
  color: #409eff;
  text-decoration: none;
}
.name-link:hover {
  text-decoration: underline;
}

.file-name {
  color: #303133;
}

.parent-link {
  color: #909399;
  text-decoration: none;
  font-size: 14px;
}
.parent-link:hover {
  color: #409eff;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}
.badge.directory {
  background: #e6f0ff;
  color: #409eff;
}
.badge.file {
  background: #f0f9eb;
  color: #67c23a;
}

.btn-action {
  padding: 4px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin: 0 2px;
}
.btn-download {
  background: #409eff;
  color: #fff;
}
.btn-download:hover {
  background: #337ecc;
}
.btn-delete {
  background: #f56c6c;
  color: #fff;
}
.btn-delete:hover {
  background: #d9534f;
}

.empty-msg {
  text-align: center;
  color: #bbb;
  padding: 30px;
}
</style>
