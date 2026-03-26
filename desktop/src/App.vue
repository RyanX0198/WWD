<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <el-icon><Document-Copy /></el-icon>
        <span>公文写作助手</span>
      </div>
      
      <el-menu
        :default-active="$route.path"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><Edit-Pen /></el-icon>
          <span>智能写作</span>
        </el-menu-item>
        
        <el-menu-item index="/knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        
        <el-menu-item index="/templates">
          <el-icon><Folder /></el-icon>
          <span>模板中心</span>
        </el-menu-item>
        
        <el-menu-item index="/documents">
          <el-icon><Document /></el-icon>
          <span>我的文档</span>
        </el-menu-item>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </aside>
    
    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
// App 根组件
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
}

.sidebar {
  width: 220px;
  background-color: #304156;
  flex-shrink: 0;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #1f2d3d;
}

.logo .el-icon {
  margin-right: 10px;
  font-size: 24px;
}

.sidebar-menu {
  border-right: none;
}

.main-content {
  flex: 1;
  overflow: auto;
  background-color: #f0f2f5;
}
</style>