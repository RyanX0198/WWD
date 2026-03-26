<template>
  <div class="writing-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="doc-type-selector">
        <span class="label">文档类型：</span>
        <el-select v-model="form.docType" placeholder="选择类型" style="width: 160px">
          <el-option label="领导讲话稿" value="讲话稿" />
          <el-option label="工作总结" value="工作总结" />
          <el-option label="活动策划" value="活动策划" />
          <el-option label="会议纪要" value="会议纪要" />
        </el-select>
      </div>
      
      <div class="actions">
        <el-button type="primary" @click="generateOutline" :loading="outlineLoading">
          <el-icon><List /></el-icon> 生成大纲
        </el-button>
        <el-button type="success" @click="generateDocument" :loading="writingLoading">
          <el-icon><Magic-Stick /></el-icon> AI写作
        </el-button>
        <el-button @click="exportDoc">
          <el-icon><Download /></el-icon> 导出
        </el-button>
      </div>
    </div>
    
    <!-- 主体内容区 -->
    <div class="content-area">
      <!-- 左侧：输入区 -->
      <div class="input-section">
        <div class="section-title">
          <span>写作要求</span>
          <el-tag type="info" size="small">{{ form.docType || '未选择' }}</el-tag>
        </div>
        
        <el-input
          v-model="form.topic"
          placeholder="请输入主题，例如：2026年全省经济工作会议讲话"
          size="large"
          class="topic-input"
        />
        
        <el-input
          v-model="form.requirements"
          type="textarea"
          :rows="8"
          placeholder="具体要求（可选）：&#10;- 会议/活动背景&#10;- 重点强调内容&#10;- 涉及人物&#10;- 其他要求"
          class="requirements-input"
        />
        
        <!-- 大纲预览 -->
        <div v-if="outline.length > 0" class="outline-preview">
          <div class="section-title">大纲预览</div>
          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in outline"
              :key="index"
              :type="index === 0 ? 'primary' : ''"
            >
              <div class="outline-item">
                <div class="outline-title">{{ item.title }}</div>
                <div class="outline-content">{{ item.content }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
      
      <!-- 右侧：输出区 -->
      <div class="output-section">
        <div class="section-title">
          <span>生成结果</span>
          <el-button-group v-if="result.content">
            <el-button size="small" @click="copyContent">
              <el-icon><Copy-Document /></el-icon> 复制
            </el-button>
            <el-button size="small" @click="polishDocument">
              <el-icon><Brush /></el-icon> 润色
            </el-button>
          </el-button-group>
        </div>
        
        <div v-if="!result.content" class="empty-state">
          <el-empty description="点击「AI写作」生成公文">
            <template #image>
              <el-icon :size="80" color="#dcdfe6"><Document-Add /></el-icon>
            </template>
          </el-empty>
        </div>
        
        <div v-else class="result-content">
          <div class="document-preview" v-html="renderedContent"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import { generateDocumentApi, generateOutlineApi } from '@/utils/api'

const md = new MarkdownIt()

const form = ref({
  docType: '讲话稿',
  topic: '',
  requirements: ''
})

const outline = ref<any[]>([])
const result = ref({
  content: '',
  type: ''
})

const outlineLoading = ref(false)
const writingLoading = ref(false)

const renderedContent = computed(() => {
  return md.render(result.value.content)
})

// 生成大纲
const generateOutline = async () => {
  if (!form.value.topic) {
    ElMessage.warning('请先输入主题')
    return
  }
  
  outlineLoading.value = true
  try {
    const res = await generateOutlineApi({
      document_type: form.value.docType,
      topic: form.value.topic,
      requirements: form.value.requirements
    })
    outline.value = res.outline || []
    ElMessage.success('大纲生成成功')
  } catch (error) {
    ElMessage.error('大纲生成失败')
  } finally {
    outlineLoading.value = false
  }
}

// 生成文档
const generateDocument = async () => {
  if (!form.value.topic) {
    ElMessage.warning('请先输入主题')
    return
  }
  
  writingLoading.value = true
  try {
    const res = await generateDocumentApi({
      document_type: form.value.docType,
      topic: form.value.topic,
      requirements: form.value.requirements
    })
    result.value.content = res.draft || ''
    outline.value = res.outline || []
    ElMessage.success('文档生成成功')
  } catch (error) {
    ElMessage.error('文档生成失败')
  } finally {
    writingLoading.value = false
  }
}

// 复制内容
const copyContent = () => {
  navigator.clipboard.writeText(result.value.content)
  ElMessage.success('已复制到剪贴板')
}

// 润色文档
const polishDocument = () => {
  ElMessage.info('润色功能开发中...')
}

// 导出文档
const exportDoc = () => {
  ElMessage.info('导出功能开发中...')
}
</script>

<style scoped>
.writing-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.doc-type-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-type-selector .label {
  color: #606266;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 12px;
}

.content-area {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.input-section,
.output-section {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.input-section {
  border-right: 1px solid #e4e7ed;
  background: #fff;
}

.output-section {
  background: #fafafa;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.topic-input {
  margin-bottom: 16px;
}

.requirements-input {
  margin-bottom: 20px;
}

.outline-preview {
  margin-top: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.outline-item {
  padding: 8px 0;
}

.outline-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.outline-content {
  font-size: 13px;
  color: #606266;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.result-content {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  min-height: 500px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.document-preview {
  line-height: 1.8;
  color: #303133;
}

.document-preview :deep(h1),
.document-preview :deep(h2),
.document-preview :deep(h3) {
  color: #303133;
  margin: 16px 0 12px;
}

.document-preview :deep(p) {
  margin: 12px 0;
  text-indent: 2em;
}
</style>