<template>
  <div class="documents-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>我的文档</h2>
        <el-tag type="info" size="small">管理所有公文文档</el-tag>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索文档..."
          style="width: 240px"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="createNewDoc">
          <el-icon><Plus /></el-icon>
          新建文档
        </el-button>
      </div>
    </div>
    
    <!-- 文档列表 -->
    <el-card v-loading="loading" class="document-list">
      <el-table :data="documentList" stripe @row-click="handleRowClick">
        <el-table-column label="文档标题" min-width="300">
          <template #default="{ row }">
            <div class="doc-title-cell">
              <el-icon class="doc-icon"><Document /></el-icon>
              <div class="doc-info">
                <div class="doc-name">{{ row.title }}</div>
                <div class="doc-meta">
                  <el-tag size="small" :type="getDocTypeColor(row.doc_type)">
                    {{ row.doc_type }}
                  </el-tag>
                  <span class="doc-stats">{{ row.char_count || 0 }} 字 · 版本 {{ row.version }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="updated_at" label="最后修改" width="180">
          <template #default="{ row }">
            <span>{{ formatTime(row.updated_at) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="editDocument(row)">编辑</el-button>
            <el-button link type="primary" @click.stop="showVersions(row)">历史版本</el-button>
            <el-dropdown @command="(cmd) => handleCommand(cmd, row)">
              <el-button link type="primary">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="collaborate">
                    <el-icon><User /></el-icon> 协作编辑
                  </el-dropdown-item>
                  <el-dropdown-item command="export">
                    <el-icon><Download /></el-icon> 导出
                  </el-dropdown-item>
                  <el-dropdown-item divided command="delete" class="danger-item">
                    <el-icon><Delete /></el-icon> 删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 空状态 -->
      <el-empty v-if="!loading && documentList.length === 0" description="暂无文档">
        <template #image>
          <el-icon :size="60" color="#dcdfe6"><Document /></el-icon>
        </template>
        <el-button type="primary" @click="createNewDoc">创建第一篇文档</el-button>
      </el-empty>
      
      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        class="pagination"
      />
    </el-card>
    
    <!-- 版本历史对话框 -->
    <el-dialog v-model="versionDialogVisible" title="版本历史" width="700px">
      <el-timeline v-if="versions.length > 0">
        <el-timeline-item
          v-for="version in versions"
          :key="version.id"
          :timestamp="formatTime(version.created_at)"
          placement="top"
        >
          <el-card :body-style="{ padding: '12px' }">
            <div class="version-header">
              <span class="version-number">版本 {{ version.version_number }}</span>
              <el-tag size="small" type="info">{{ version.edited_by_name }}</el-tag>
            </div>
            <div v-if="version.change_summary" class="version-summary">
              {{ version.change_summary }}
            </div>
            <div class="version-actions">
              <el-button 
                link 
                type="primary" 
                size="small"
                @click="previewVersion(version)"
              >
                预览
              </el-button>
              <el-button 
                link 
                type="warning" 
                size="small"
                @click="restoreVersion(version)"
              >
                恢复此版本
              </el-button>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      
      <el-empty v-else description="暂无版本历史" />
    </el-dialog>
    
    <!-- 协作编辑对话框 -->
    <el-dialog 
      v-model="collabDialogVisible" 
      :title="`协作编辑 - ${currentDoc?.title}`" 
      width="900px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <CollaborativeEditor 
        v-if="currentDoc"
        :document-id="currentDoc.id"
        :initial-content="currentDoc.content"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Plus,
  Search,
  ArrowDown,
  User,
  Download,
  Delete
} from '@element-plus/icons-vue'
import {
  getDocumentsApi,
  deleteDocumentApi,
  getDocumentVersionsApi,
  restoreDocumentVersionApi,
  exportDocumentApi
} from '@/utils/api'
import CollaborativeEditor from '@/components/CollaborativeEditor.vue'

const router = useRouter()

const loading = ref(false)
const searchQuery = ref('')
const documentList = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const versionDialogVisible = ref(false)
const versions = ref<any[]>([])
const currentDoc = ref<any>(null)

const collabDialogVisible = ref(false)

// 加载文档列表
const loadDocuments = async () => {
  loading.value = true
  try {
    const res = await getDocumentsApi({
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: searchQuery.value || undefined
    })
    documentList.value = res.documents || []
    total.value = res.total || 0
  } catch (error) {
    console.error('Failed to load documents:', error)
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

// 创建新文档
const createNewDoc = () => {
  router.push('/')
}

// 编辑文档
const editDocument = (row: any) => {
  // 可以跳转到编辑页面或打开编辑器
  ElMessage.info('编辑功能开发中...')
}

// 显示版本历史
const showVersions = async (row: any) => {
  currentDoc.value = row
  try {
    const res = await getDocumentVersionsApi(row.id)
    versions.value = res.versions || []
    versionDialogVisible.value = true
  } catch (error) {
    console.error('Failed to load versions:', error)
    ElMessage.error('加载版本历史失败')
  }
}

// 预览版本
const previewVersion = (version: any) => {
  ElMessage.info('版本预览功能开发中...')
}

// 恢复版本
const restoreVersion = async (version: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要恢复到版本 ${version.version_number} 吗？`,
      '确认恢复',
      {
        confirmButtonText: '恢复',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await restoreDocumentVersionApi(currentDoc.value.id, version.id)
    ElMessage.success('版本恢复成功')
    loadDocuments()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to restore version:', error)
      ElMessage.error('恢复失败')
    }
  }
}

// 更多操作
const handleCommand = (command: string, row: any) => {
  currentDoc.value = row
  switch (command) {
    case 'collaborate':
      collabDialogVisible.value = true
      break
    case 'export':
      exportDocument(row)
      break
    case 'delete':
      deleteDocument(row)
      break
  }
}

// 导出文档
const exportDocument = async (row: any) => {
  try {
    const blob = await exportDocumentApi(row.id, 'docx')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${row.title}.docx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Failed to export:', error)
    ElMessage.error('导出失败')
  }
}

// 删除文档
const deleteDocument = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${row.title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteDocumentApi(row.id)
    ElMessage.success('删除成功')
    loadDocuments()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 行点击
const handleRowClick = (row: any) => {
  editDocument(row)
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadDocuments()
}

// 分页
const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadDocuments()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadDocuments()
}

// 格式化时间
const formatTime = (time?: string) => {
  if (!time) return '--'
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取文档类型颜色
const getDocTypeColor = (type?: string) => {
  const map: Record<string, string> = {
    '讲话稿': 'primary',
    '工作总结': 'success',
    '活动策划': 'warning',
    '会议纪要': 'info',
    '通知公告': '',
    '工作报告': 'danger'
  }
  return map[type || ''] || ''
}

// 获取状态类型
const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    'draft': 'info',
    'reviewing': 'warning',
    'published': 'success',
    'archived': ''
  }
  return map[status || ''] || ''
}

// 获取状态标签
const getStatusLabel = (status?: string) => {
  const map: Record<string, string> = {
    'draft': '草稿',
    'reviewing': '审核中',
    'published': '已发布',
    'archived': '已归档'
  }
  return map[status || ''] || status
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.documents-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-right {
  display: flex;
  gap: 12px;
}

.document-list {
  min-height: 400px;
}

.doc-title-cell {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.doc-icon {
  font-size: 40px;
  color: #409eff;
  flex-shrink: 0;
}

.doc-info {
  flex: 1;
}

.doc-name {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 6px;
}

.doc-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.doc-stats {
  font-size: 13px;
  color: #909399;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.version-number {
  font-weight: 600;
  font-size: 14px;
}

.version-summary {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
}

.version-actions {
  display: flex;
  gap: 12px;
}

.danger-item {
  color: #f56c6c;
}

:deep(.el-dropdown-menu__item.danger-item:hover) {
  color: #f56c6c;
  background-color: #fef0f0;
}
</style>
