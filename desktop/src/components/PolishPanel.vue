<template>
  <div class="polish-panel">
    <div class="polish-layout">
      <!-- 左侧：原始文本 -->
      <div class="text-panel">
        <div class="panel-header">
          <span>原始文本</span>
          <el-tag type="info" size="small">{{ originalText.length }} 字</el-tag>
        </div>
        <div class="panel-body">
          <pre class="text-content">{{ originalText }}</pre>
        </div>
      </div>
      
      <!-- 中间：操作区 -->
      <div class="action-panel">
        <div class="mode-selector">
          <div class="selector-label">润色模式</div>
          <el-radio-group v-model="polishMode" class="mode-options">
            <el-radio-button label="general">通用润色</el-radio-button>
            <el-radio-button label="formal">正式化</el-radio-button>
            <el-radio-button label="concise">精简</el-radio-button>
            <el-radio-button label="expand">扩充</el-radio-button>
            <el-radio-button label="policy">政策化</el-radio-button>
          </el-radio-group>
        </div>
        
        <el-divider />
        
        <div class="custom-input">
          <div class="input-label">具体要求（可选）</div>
          <el-input
            v-model="customRequirement"
            type="textarea"
            :rows="4"
            placeholder="例如：增加数据支撑、调整语气更严肃、补充背景说明..."
          />
        </div>
        
        <el-button
          type="primary"
          size="large"
          class="polish-btn"
          :loading="polishing"
          @click="startPolish"
        >
          <el-icon><Magic-Stick /></el-icon>
          {{ polishing ? '润色中...' : '开始润色' }}
        </el-button>
        
        <el-divider />
        
        <div class="history-list" v-if="polishHistory.length > 0">
          <div class="history-label">润色历史</div>
          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in polishHistory"
              :key="index"
              :type="index === 0 ? 'primary' : ''"
            >
              <div class="history-item" @click="selectHistory(item)">
                <div class="history-mode">{{ getModeLabel(item.mode) }}</div>
                <div class="history-time">{{ formatTime(item.time) }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
      
      <!-- 右侧：润色结果 -->
      <div class="text-panel result-panel">
        <div class="panel-header">
          <span>润色结果</span>
          <el-tag type="success" size="small" v-if="polishedText">{{ polishedText.length }} 字</el-tag>
        </div>
        
        <div class="panel-body">
          <div v-if="!polishedText && !polishing" class="empty-tip">
            <el-empty description="点击「开始润色」生成结果" />
          </div>
          
          <div v-else-if="polishing" class="loading-tip">
            <el-skeleton :rows="6" animated />
          </div>
          
          <pre v-else class="text-content polished">{{ polishedText }}</pre>
        </div>
        
        <div v-if="polishedText" class="panel-footer">
          <el-button @click="copyResult">
            <el-icon><Copy-Document /></el-icon>
            复制
          </el-button>
          <el-button type="primary" @click="applyResult">
            <el-icon><Check /></el-icon>
            应用修改
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, CopyDocument, Check } from '@element-plus/icons-vue'
import { polishDocumentApi } from '@/utils/api'

interface Props {
  initialText: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'apply', text: string): void
}>()

const originalText = computed(() => props.initialText)

const polishMode = ref('general')
const customRequirement = ref('')
const polishing = ref(false)
const polishedText = ref('')

const polishHistory = ref<any[]>([])

const modeLabels: Record<string, string> = {
  general: '通用润色',
  formal: '正式化',
  concise: '精简',
  expand: '扩充',
  policy: '政策化'
}

const getModeLabel = (mode: string) => {
  return modeLabels[mode] || mode
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const startPolish = async () => {
  if (!originalText.value) {
    ElMessage.warning('没有可润色的文本')
    return
  }
  
  polishing.value = true
  try {
    // 构建润色提示
    let instruction = modeLabels[polishMode.value]
    if (customRequirement.value) {
      instruction += `，${customRequirement.value}`
    }
    
    // 调用润色 API
    const res = await polishDocumentApi({
      text: originalText.value,
      instruction: instruction,
      mode: polishMode.value
    })
    
    polishedText.value = res.polished_text || res.text || '润色失败，请重试'
    
    // 添加到历史
    polishHistory.value.unshift({
      mode: polishMode.value,
      text: polishedText.value,
      time: Date.now()
    })
    
    // 限制历史数量
    if (polishHistory.value.length > 10) {
      polishHistory.value = polishHistory.value.slice(0, 10)
    }
    
  } catch (error) {
    console.error('Polish failed:', error)
    ElMessage.error('润色失败，请重试')
  } finally {
    polishing.value = false
  }
}

const selectHistory = (item: any) => {
  polishedText.value = item.text
  polishMode.value = item.mode
}

const copyResult = () => {
  navigator.clipboard.writeText(polishedText.value)
  ElMessage.success('已复制到剪贴板')
}

const applyResult = () => {
  emit('apply', polishedText.value)
}
</script>

<style scoped>
.polish-panel {
  height: 600px;
}

.polish-layout {
  display: grid;
  grid-template-columns: 1fr 280px 1fr;
  gap: 20px;
  height: 100%;
}

.text-panel {
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 600;
  font-size: 14px;
}

.panel-body {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.text-content {
  margin: 0;
  padding: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
}

.text-content.polished {
  background: #f6ffed;
  padding: 16px;
  border-radius: 4px;
  border: 1px solid #b7eb8f;
}

.panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
}

.action-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mode-selector,
.custom-input {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.selector-label,
.input-label,
.history-label {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 12px;
  color: #303133;
}

.mode-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mode-options :deep(.el-radio-button__inner) {
  width: 100%;
  text-align: center;
}

.polish-btn {
  width: 100%;
}

.history-list {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.history-item:hover {
  background: #f5f7fa;
}

.history-mode {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.history-time {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.empty-tip,
.loading-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
