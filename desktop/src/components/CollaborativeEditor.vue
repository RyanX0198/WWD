<template>
  <div class="collaborative-editor">
    <!-- 顶部工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <span class="connection-status" :class="{ connected: isConnected }">
          <el-icon><Circle-Check v-if="isConnected" /><Circle-Close v-else /></el-icon>
          {{ isConnected ? '已连接' : '未连接' }}
        </span>
        <span class="version-info">版本 {{ revision }}</span>
      </div>
      
      <div class="toolbar-right">
        <!-- 在线用户头像 -->
        <div class="online-users">
          <span class="users-label">在线用户:</span>
          <el-tooltip
            v-for="user in onlineUsers"
            :key="user.user_id"
            :content="user.user_name"
            placement="bottom"
          >
            <el-avatar
              :size="32"
              :style="{ backgroundColor: user.color }"
              class="user-avatar"
            >
              {{ user.user_name.charAt(0) }}
            </el-avatar>
          </el-tooltip>
        </div>
        
        <el-button type="primary" size="small" @click="saveToServer">
          <el-icon><Check /></el-icon>
          保存
        </el-button>
      </div>
    </div>
    
    <!-- 编辑器主体 -->
    <div class="editor-body">
      <div class="editor-container">
        <div 
          ref="editorRef"
          class="rich-editor"
          contenteditable="true"
          @input="handleInput"
          @keydown="handleKeyDown"
          @mouseup="updateCursor"
          @keyup="updateCursor"
          v-html="content"
        ></div>
        
        <!-- 远程用户光标 -->
        <div
          v-for="user in remoteCursors"
          :key="user.user_id"
          class="remote-cursor"
          :style="{
            left: `${user.x}px`,
            top: `${user.y}px`,
            backgroundColor: user.color
          }"
        >
          <div class="cursor-label" :style="{ backgroundColor: user.color }">
            {{ user.user_name }}
          </div>
        </div>
      </div>
      
      <!-- 右侧操作日志 -->
      <div class="operation-log">
        <div class="log-header">操作日志</div>
        <div class="log-list" ref="logRef">
          <div
            v-for="(log, index) in operationLogs"
            :key="index"
            class="log-item"
          >
            <span class="log-time">{{ formatTime(log.time) }}</span>
            <span class="log-content">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, CircleClose, Check } from '@element-plus/icons-vue'
import { syncCollaborationDocApi } from '@/utils/api'

interface Props {
  documentId: string
  initialContent?: string
}

const props = defineProps<Props>()

// 状态
const isConnected = ref(false)
const content = ref(props.initialContent || '')
const revision = ref(0)
const onlineUsers = ref<any[]>([])
const remoteCursors = ref<any[]>([])
const operationLogs = ref<any[]>([])

// DOM 引用
const editorRef = ref<HTMLDivElement>()
const logRef = ref<HTMLDivElement>()

// WebSocket
let ws: WebSocket | null = null
let heartbeatInterval: NodeJS.Timeout | null = null
let userId = ''
let userName = ''

// 添加日志
const addLog = (message: string) => {
  operationLogs.value.unshift({
    time: Date.now(),
    message
  })
  // 限制日志数量
  if (operationLogs.value.length > 50) {
    operationLogs.value = operationLogs.value.slice(0, 50)
  }
}

// 格式化时间
const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 连接 WebSocket
const connectWebSocket = () => {
  // 生成或获取用户ID
  userId = localStorage.getItem('collab_user_id') || `user_${Date.now()}`
  userName = localStorage.getItem('collab_user_name') || `用户${Math.floor(Math.random() * 1000)}`
  localStorage.setItem('collab_user_id', userId)
  localStorage.setItem('collab_user_name', userName)
  
  const wsUrl = `ws://localhost:8000/ws/collaborate/${props.documentId}?user_id=${userId}&user_name=${encodeURIComponent(userName)}`
  
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    isConnected.value = true
    addLog('已连接到协作服务器')
    
    // 启动心跳
    heartbeatInterval = setInterval(() => {
      ws?.send(JSON.stringify({ type: 'ping' }))
    }, 30000)
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    handleWebSocketMessage(data)
  }
  
  ws.onclose = () => {
    isConnected.value = false
    addLog('连接已断开')
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
    }
    // 尝试重连
    setTimeout(() => {
      if (!isConnected.value) {
        addLog('尝试重新连接...')
        connectWebSocket()
      }
    }, 3000)
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    addLog('连接错误')
  }
}

// 处理 WebSocket 消息
const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'init':
      content.value = data.content
      revision.value = data.revision
      onlineUsers.value = data.users || []
      addLog('初始化完成')
      nextTick(() => {
        if (editorRef.value) {
          editorRef.value.innerHTML = data.content
        }
      })
      break
      
    case 'operation':
      applyRemoteOperation(data.operation)
      revision.value = data.operation.revision
      break
      
    case 'cursor':
      updateRemoteCursor(data)
      break
      
    case 'user_joined':
      addLog(`用户 "${data.user.user_name}" 加入协作`)
      onlineUsers.value.push(data.user)
      break
      
    case 'user_left':
      addLog(`用户离开`)
      onlineUsers.value = onlineUsers.value.filter(u => u.user_id !== data.user_id)
      remoteCursors.value = remoteCursors.value.filter(c => c.user_id !== data.user_id)
      break
      
    case 'pong':
      // 心跳响应
      break
  }
}

// 应用远程操作
const applyRemoteOperation = (operation: any) => {
  if (!editorRef.value) return
  
  // 简化处理：直接更新内容（实际应该用更精细的 OT）
  // 这里为了保持简单，直接替换内容
  if (operation.type === 'insert') {
    const text = editorRef.value.innerText
    const before = text.substring(0, operation.position)
    const after = text.substring(operation.position)
    editorRef.value.innerText = before + operation.text + after
    addLog(`用户插入文本: "${operation.text.substring(0, 20)}..."`)
  } else if (operation.type === 'delete') {
    const text = editorRef.value.innerText
    const before = text.substring(0, operation.position)
    const after = text.substring(operation.position + operation.length)
    editorRef.value.innerText = before + after
    addLog(`用户删除 ${operation.length} 个字符`)
  }
  
  content.value = editorRef.value.innerHTML
}

// 更新远程光标位置
const updateRemoteCursor = (data: any) => {
  const existingIndex = remoteCursors.value.findIndex(c => c.user_id === data.user_id)
  
  // 简化：使用随机位置模拟（实际应该根据字符位置计算坐标）
  const mockPosition = {
    x: Math.random() * 200 + 50,
    y: Math.random() * 300 + 50
  }
  
  const cursorData = {
    user_id: data.user_id,
    user_name: onlineUsers.value.find(u => u.user_id === data.user_id)?.user_name || '未知用户',
    color: onlineUsers.value.find(u => u.user_id === data.user_id)?.color || '#999',
    position: data.position,
    ...mockPosition
  }
  
  if (existingIndex >= 0) {
    remoteCursors.value[existingIndex] = cursorData
  } else {
    remoteCursors.value.push(cursorData)
  }
}

// 处理编辑器输入
let lastContent = ''
const handleInput = () => {
  if (!editorRef.value || !ws) return
  
  const newContent = editorRef.value.innerText
  
  // 检测变化并发送操作
  if (newContent.length > lastContent.length) {
    // 插入
    const position = getCaretPosition()
    const insertedText = newContent.substring(position - (newContent.length - lastContent.length), position)
    
    ws.send(JSON.stringify({
      type: 'operation',
      operation: {
        type: 'insert',
        position: position - insertedText.length,
        text: insertedText
      }
    }))
  } else if (newContent.length < lastContent.length) {
    // 删除
    const position = getCaretPosition()
    const deletedLength = lastContent.length - newContent.length
    
    ws.send(JSON.stringify({
      type: 'operation',
      operation: {
        type: 'delete',
        position: position,
        length: deletedLength
      }
    }))
  }
  
  lastContent = newContent
  content.value = editorRef.value.innerHTML
}

// 获取光标位置
const getCaretPosition = () => {
  const selection = window.getSelection()
  if (!selection || !selection.rangeCount) return 0
  
  const range = selection.getRangeAt(0)
  const preCaretRange = range.cloneRange()
  preCaretRange.selectNodeContents(editorRef.value!)
  preCaretRange.setEnd(range.endContainer, range.endOffset)
  
  return preCaretRange.toString().length
}

// 处理键盘事件
const handleKeyDown = (e: KeyboardEvent) => {
  // 可以在这里处理特殊快捷键
  if (e.ctrlKey || e.metaKey) {
    if (e.key === 's') {
      e.preventDefault()
      saveToServer()
    }
  }
}

// 更新光标位置
let cursorTimeout: NodeJS.Timeout | null = null
const updateCursor = () => {
  if (!ws || cursorTimeout) return
  
  cursorTimeout = setTimeout(() => {
    const position = getCaretPosition()
    ws!.send(JSON.stringify({
      type: 'cursor',
      position: position
    }))
    cursorTimeout = null
  }, 100)
}

// 保存到服务器
const saveToServer = async () => {
  try {
    await syncCollaborationDocApi(props.documentId)
    addLog('文档已保存到服务器')
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('Failed to save:', error)
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  connectWebSocket()
  lastContent = props.initialContent || ''
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
  }
  if (cursorTimeout) {
    clearTimeout(cursorTimeout)
  }
})
</script>

<style scoped>
.collaborative-editor {
  display: flex;
  flex-direction: column;
  height: 600px;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #f5f7fa;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
}

.connection-status.connected {
  color: #67c23a;
}

.version-info {
  font-size: 13px;
  color: #606266;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.online-users {
  display: flex;
  align-items: center;
  gap: 8px;
}

.users-label {
  font-size: 13px;
  color: #606266;
}

.user-avatar {
  color: #fff;
  font-weight: 600;
  font-size: 14px;
}

.editor-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.editor-container {
  flex: 1;
  position: relative;
  overflow: auto;
}

.rich-editor {
  min-height: 100%;
  padding: 20px;
  outline: none;
  line-height: 1.8;
  font-size: 14px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.rich-editor:empty:before {
  content: '开始协作编辑...';
  color: #c0c4cc;
}

.remote-cursor {
  position: absolute;
  width: 2px;
  height: 20px;
  pointer-events: none;
  transition: all 0.1s ease;
}

.cursor-label {
  position: absolute;
  top: -22px;
  left: 0;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  color: #fff;
  white-space: nowrap;
}

.operation-log {
  width: 250px;
  border-left: 1px solid #e4e7ed;
  background: #fafafa;
  display: flex;
  flex-direction: column;
}

.log-header {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
}

.log-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.log-item {
  padding: 6px 16px;
  font-size: 12px;
  display: flex;
  gap: 8px;
}

.log-time {
  color: #909399;
  flex-shrink: 0;
}

.log-content {
  color: #606266;
  word-break: break-all;
}
</style>
