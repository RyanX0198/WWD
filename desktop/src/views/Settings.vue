<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>
    
    <el-card class="settings-card">
      <template #header>
        <span>模型配置</span>
      </template>
      
      <el-form label-width="160px">
        <el-form-item label="主力模型">
          <el-select v-model="settings.primaryModel" style="width: 300px">
            <el-option label="Kimi K2.5" value="kimi-k2p5" />
            <el-option label="通义千问 Max" value="qwen-max" />
            <el-option label="ChatGLM-4" value="glm-4" />
            <el-option label="MiniMax" value="minimax-ab6" />
          </el-select>
          <div class="form-tip">国内模型优先，支持 Kimi、千问、GLM、MiniMax</div>
        </el-form-item>
        
        <el-form-item label="Kimi API Key">
          <el-input
            v-model="settings.kimiKey"
            type="password"
            show-password
            placeholder="sk-..."
            style="width: 400px"
          />
          <div class="form-tip">获取地址：<a href="https://platform.moonshot.cn/" target="_blank">https://platform.moonshot.cn/</a></div>
        </el-form-item>
        
        <el-form-item label="通义千问 API Key">
          <el-input
            v-model="settings.qwenKey"
            type="password"
            show-password
            placeholder="sk-..."
            style="width: 400px"
          />
          <div class="form-tip">获取地址：<a href="https://dashscope.aliyun.com/" target="_blank">https://dashscope.aliyun.com/</a></div>
        </el-form-item>
        
        <el-form-item label="ChatGLM API Key">
          <el-input
            v-model="settings.glmKey"
            type="password"
            show-password
            placeholder="..."
            style="width: 400px"
          />
          <div class="form-tip">获取地址：<a href="https://open.bigmodel.cn/" target="_blank">https://open.bigmodel.cn/</a></div>
        </el-form-item>
        
        <el-form-item label="MiniMax API Key">
          <el-input
            v-model="settings.minimaxKey"
            type="password"
            show-password
            placeholder="..."
            style="width: 400px"
          />
          <div class="form-tip">获取地址：<a href="https://www.minimaxi.com/" target="_blank">https://www.minimaxi.com/</a></div>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="settings-card" style="margin-top: 20px">
      <template #header>
        <span>关于</span>
      </template>
      
      <div class="about-info">
        <p><strong>政府公文智能写作助手</strong></p>
        <p>版本：v0.1.0</p>
        <p>基于 Agent Harness 架构</p>
        <p>GitHub: <a href="https://github.com/RyanX0198/WWD" target="_blank">https://github.com/RyanX0198/WWD</a></p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const settings = ref({
  primaryModel: 'kimi-k2p5',
  kimiKey: '',
  qwenKey: '',
  glmKey: '',
  minimaxKey: ''
})
</script>

<style scoped>
.settings-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.settings-card {
  max-width: 800px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.form-tip a {
  color: #409EFF;
}

.about-info {
  line-height: 2;
  color: #606266;
}

.about-info p {
  margin: 8px 0;
}
</style>