<template>
  <div class="templates-page">
    <div class="page-header">
      <h2>模板中心</h2>
      <el-button type="primary">
        <el-icon><Plus /></el-icon> 新建模板
      </el-button>
    </div>
    
    <el-empty description="模板中心功能开发中...">
      <template #description>
        <p>将支持：</p>
        <ul style="text-align: left; display: inline-block; margin-top: 12px;">
          <li>历史优秀文档沉淀</li>
          <li>按文种、行业、场景分类</li>
          <li>智能模板匹配</li>
          <li>自定义模板上传</li>
        </ul>
      </template>
    </el-empty>
  </div>
</template>

<style scoped>
.templates-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}
</style>