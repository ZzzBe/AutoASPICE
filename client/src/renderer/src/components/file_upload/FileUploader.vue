<template>
  <div
    class="file-uploader"
    :class="{ 'is-dragover': isDragover }"
    @dragover.prevent="isDragover = true"
    @dragleave.prevent="isDragover = false"
    @drop.prevent="handleDrop"
  >
    <div class="upload-zone">
      <div class="upload-icon">
        <el-icon :size="20"><UploadFilled /></el-icon>
      </div>
      <div class="upload-text">
        <span class="upload-primary">Drop files here</span>
        <span class="upload-secondary">or click to browse</span>
      </div>
      <input
        ref="fileInputRef"
        type="file"
        multiple
        class="file-input-hidden"
        @change="handleFileSelect"
      />
      <el-button size="small" @click="openFilePicker" text>
        Browse Files
      </el-button>
    </div>

    <!-- Selected Files List -->
    <div v-if="selectedFiles.length > 0" class="selected-files">
      <div
        v-for="(file, index) in selectedFiles"
        :key="index"
        class="selected-file-item"
      >
        <el-icon :size="14" class="file-type-icon">
          <Document v-if="getFileType(file) === 'doc'" />
          <Picture v-else-if="getFileType(file) === 'image'" />
          <Tickets v-else />
        </el-icon>
        <span class="file-name truncate">{{ file.name }}</span>
        <span class="file-size">{{ formatSize(file.size) }}</span>
        <el-icon
          class="file-remove"
          :size="14"
          @click="removeFile(index)"
        >
          <Close />
        </el-icon>
        <el-progress
          v-if="file.uploading"
          :percentage="file.progress || 0"
          :stroke-width="2"
          :show-text="false"
          class="file-progress"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['files-selected', 'files-uploaded'])

const isDragover = ref(false)
const selectedFiles = ref([])
const fileInputRef = ref(null)

function openFilePicker() {
  fileInputRef.value?.click()
}

function handleFileSelect(event) {
  const files = Array.from(event.target.files || [])
  addFiles(files)
  event.target.value = ''
}

function handleDrop(event) {
  isDragover.value = false
  const files = Array.from(event.dataTransfer.files || [])
  addFiles(files)
}

function addFiles(files) {
  const fileEntries = files.map((file) => ({
    name: file.name,
    size: file.size,
    path: file.path || null,
    type: file.type,
    uploading: false,
    progress: 0,
    file
  }))
  selectedFiles.value = [...selectedFiles.value, ...fileEntries]
  emit('files-selected', selectedFiles.value)
}

function removeFile(index) {
  selectedFiles.value.splice(index, 1)
  emit('files-selected', selectedFiles.value)
}

function getFileType(file) {
  const name = file.name.toLowerCase()
  if (/\.(png|jpg|jpeg|gif|svg|webp)$/.test(name)) return 'image'
  if (/\.(pdf|doc|docx|txt|md)$/.test(name)) return 'doc'
  return 'code'
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function uploadFiles(projectId) {
  for (const fileEntry of selectedFiles.value) {
    if (fileEntry.uploading) continue
    fileEntry.uploading = true
    fileEntry.progress = 0

    try {
      const result = await window.autodev.uploadFile({
        filePath: fileEntry.path || fileEntry.name,
        projectId
      })
      if (result.success) {
        fileEntry.progress = 100
        fileEntry.uploaded = true
      } else {
        ElMessage.error(`Failed to upload ${fileEntry.name}: ${result.error}`)
      }
    } catch (err) {
      ElMessage.error(`Upload failed: ${err.message}`)
    } finally {
      fileEntry.uploading = false
    }
  }

  emit('files-uploaded', selectedFiles.value.filter((f) => f.uploaded))
}
</script>

<style scoped>
.file-uploader {
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.file-uploader.is-dragover {
  border-color: var(--color-accent);
  background: rgba(88, 166, 255, 0.05);
}

.upload-zone {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
}

.upload-icon {
  color: var(--color-text-muted);
}

.upload-text {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.upload-primary {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.upload-secondary {
  font-size: 11px;
  color: var(--color-text-muted);
}

.file-input-hidden {
  display: none;
}

.selected-files {
  border-top: 1px solid var(--color-border);
  padding: 8px;
  max-height: 160px;
  overflow-y: auto;
}

.selected-file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  position: relative;
}

.selected-file-item:hover {
  background: var(--color-bg-hover);
}

.file-type-icon {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.file-name {
  flex: 1;
  color: var(--color-text-primary);
  min-width: 0;
}

.file-size {
  color: var(--color-text-muted);
  font-size: 11px;
  flex-shrink: 0;
}

.file-remove {
  color: var(--color-text-muted);
  cursor: pointer;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.selected-file-item:hover .file-remove {
  opacity: 1;
}

.file-remove:hover {
  color: var(--color-error);
}

.file-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
}
</style>
