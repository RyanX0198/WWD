<template>
  <div class="documents-page">
    <div class="page-header">
      <h2>我的文档</h2>
    </div>
    
    <el-empty description="文档管理功能开发中...">
      <template #description>
        <p>将支持：</p>
        <ul style="text-align: left; display: inline-block; margin-top: 12px;">
          <li>历史生成文档管理</li>
          <li>版本历史</li>
          <li>文档导出</li>
          <li>文件夹分类</li>
        </ul>
      </template>
    </el-empty>
  </div>
</template>

<style scoped>
.documents-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}
</style>