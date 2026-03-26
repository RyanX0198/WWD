<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h2>知识库管理</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon> 添加人物
      </el-button>
    </div>
    
    <div class="knowledge-content">
      <!-- 人物档案 -->
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <span>人物档案</span>
            <el-input
              v-model="searchQuery"
              placeholder="搜索人物"
              style="width: 200px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </template>
        
        <el-table :data="peopleList" style="width: 100%">
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="current_position" label="现任职务" />
          <el-table-column prop="level" label="级别" width="120" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button link type="primary" @click="viewPerson(row)">查看</el-button>
              <el-button link type="danger" @click="deletePerson(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
      
      <!-- 政策文件 -->
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <span>政策文件</span>
            <el-button type="primary" size="small">
              <el-icon><Upload /></el-icon> 上传文件
            </el-button>
          </div>
        </template>
        
        <el-empty description="政策文件管理功能开发中..." />
      </el-card>
    </div>
    
    <!-- 添加人物对话框 -->
    <el-dialog v-model="showAddDialog" title="添加人物档案" width="600px">
      <el-form :model="personForm" label-width="100px">
        <el-form-item label="姓名">
          <el-input v-model="personForm.name" />
        </el-form-item>
        <el-form-item label="现任职务">
          <el-input v-model="personForm.current_position" />
        </el-form-item>
        <el-form-item label="行政级别">
          <el-select v-model="personForm.level" style="width: 100%">
            <el-option label="正部级" value="正部级" />
            <el-option label="副部级" value="副部级" />
            <el-option label="正厅级" value="正厅级" />
            <el-option label="副厅级" value="副厅级" />
            <el-option label="正处级" value="正处级" />
            <el-option label="副处级" value="副处级" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addPerson">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getPeopleListApi, createPersonApi } from '@/utils/api'

const searchQuery = ref('')
const peopleList = ref([])
const showAddDialog = ref(false)

const personForm = ref({
  name: '',
  current_position: '',
  level: '',
  addressing_rules: {},
  career: [],
  responsibilities: []
})

const loadPeople = async () => {
  try {
    const res = await getPeopleListApi() as any
    // TODO: 转换数据格式
    peopleList.value = res.people.map((name: string) => ({
      name,
      current_position: '待完善',
      level: '待完善'
    }))
  } catch (error) {
    console.error('加载人物列表失败:', error)
  }
}

const addPerson = async () => {
  try {
    await createPersonApi(personForm.value)
    ElMessage.success('添加成功')
    showAddDialog.value = false
    loadPeople()
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

const viewPerson = (row: any) => {
  ElMessage.info(`查看 ${row.name} 的详情`)
}

const deletePerson = (row: any) => {
  ElMessage.warning(`删除 ${row.name} 的功能开发中`)
}

onMounted(() => {
  loadPeople()
})
</script>

<style scoped>
.knowledge-page {
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

.knowledge-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>