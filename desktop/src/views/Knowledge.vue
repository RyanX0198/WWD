<template>
  <div class="knowledge-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>知识库</h2>
        <el-tag type="info" size="small">管理人物档案、机构信息</el-tag>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索人物或机构..."
          style="width: 240px"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          新建档案
        </el-button>
      </div>
    </div>
    
    <!-- 标签页切换 -->
    <el-tabs v-model="activeTab" class="knowledge-tabs">
      <!-- 人物档案 -->
      <el-tab-pane label="人物档案" name="people">
        <div class="tab-content">
          <!-- 人物列表 -->
          <el-table :data="peopleList" v-loading="loading" stripe>
            <el-table-column prop="name" label="姓名" width="120">
              <template #default="{ row }">
                <div class="person-name">
                  <el-avatar :size="32" :icon="UserFilled" />
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="current_position" label="现任职务" min-width="200">
              <template #default="{ row }">
                <el-tag type="primary" size="small" v-if="row.current_position">
                  {{ row.current_position }}
                </el-tag>
                <span v-else class="empty-text">--</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="org_affiliation" label="所属机构" width="150">
              <template #default="{ row }">
                <span>{{ row.org_affiliation || '--' }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="level" label="级别" width="100">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" size="small">
                  {{ row.level || '未知' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column label="称谓规范" min-width="200">
              <template #default="{ row }">
                <el-tooltip
                  v-if="row.addressing_rules"
                  :content="formatAddressingRules(row.addressing_rules)"
                  placement="top"
                >
                  <el-tag type="info" size="small">查看称谓</el-tag>
                </el-tooltip>
                <span v-else class="empty-text">未设置</span>
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="editPerson(row)">编辑</el-button>
                <el-button link type="danger" @click="deletePerson(row.name)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 空状态 -->
          <el-empty v-if="!loading && peopleList.length === 0" description="暂无人物档案">
            <template #image>
              <el-icon :size="60" color="#dcdfe6"><User /></el-icon>
            </template>
            <el-button type="primary" @click="showAddDialog = true">创建第一个档案</el-button>
          </el-empty>
        </div>
      </el-tab-pane>
      
      <!-- 机构管理 -->
      <el-tab-pane label="机构管理" name="organizations">
        <div class="tab-content">
          <div class="org-tree-container">
            <el-tree
              :data="orgTree"
              :props="{ label: 'full_name', children: 'children' }"
              node-key="id"
              default-expand-all
              highlight-current
              @node-click="handleOrgClick"
            >
              <template #default="{ node, data }">
                <div class="org-tree-node">
                  <el-icon><Office-Building /></el-icon>
                  <span class="org-name">{{ data.short_name || data.full_name }}</span>
                  <el-tag size="small" :type="getOrgTypeColor(data.org_type)" v-if="data.org_type">
                    {{ data.org_type }}
                  </el-tag>
                </div>
              </template>
            </el-tree>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 新建/编辑人物对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="isEditing ? '编辑人物档案' : '新建人物档案'"
      width="600px"
      destroy-on-close
    >
      <el-form :model="personForm" label-width="100px">
        <el-form-item label="姓名" required>
          <el-input v-model="personForm.name" placeholder="请输入姓名" />
        </el-form-item>
        
        <el-form-item label="现任职务">
          <el-input v-model="personForm.current_position" placeholder="如：省长、市委书记" />
        </el-form-item>
        
        <el-form-item label="所属机构">
          <el-input v-model="personForm.org_affiliation" placeholder="如：省政府、市委" />
        </el-form-item>
        
        <el-form-item label="级别">
          <el-select v-model="personForm.level" placeholder="选择级别" style="width: 100%">
            <el-option label="正部级" value="正部级" />
            <el-option label="副部级" value="副部级" />
            <el-option label="正厅级" value="正厅级" />
            <el-option label="副厅级" value="副厅级" />
            <el-option label="正处级" value="正处级" />
            <el-option label="副处级" value="副处级" />
            <el-option label="正科级" value="正科级" />
            <el-option label="副科级" value="副科级" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="性别">
          <el-radio-group v-model="personForm.gender">
            <el-radio label="男">男</el-radio>
            <el-radio label="女">女</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-divider content-position="left">称谓规范</el-divider>
        
        <el-form-item label="正式场合">
          <el-input v-model="personForm.addressing_rules_formal" placeholder="如：XX省长、XX书记" />
        </el-form-item>
        
        <el-form-item label="公开场合">
          <el-input v-model="personForm.addressing_rules_public" placeholder="如：XX同志" />
        </el-form-item>
        
        <el-form-item label="避免使用">
          <el-input v-model="personForm.addressing_rules_avoid" placeholder="如：直呼其名" />
        </el-form-item>
        
        <el-divider content-position="left">其他信息</el-divider>
        
        <el-form-item label="分管工作">
          <el-input 
            v-model="personForm.responsibilities" 
            type="textarea" 
            :rows="3"
            placeholder="分管领域和工作职责"
          />
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input 
            v-model="personForm.notes" 
            type="textarea" 
            :rows="2"
            placeholder="其他需要记录的信息"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="savePerson" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UserFilled, User, Search, Plus, OfficeBuilding } from '@element-plus/icons-vue'
import {
  getPeopleListApi,
  createPersonApi,
  updatePersonApi,
  deletePersonApi,
  getOrgTreeApi
} from '@/utils/api'

const activeTab = ref('people')
const loading = ref(false)
const saving = ref(false)
const searchQuery = ref('')
const showAddDialog = ref(false)
const isEditing = ref(false)

const peopleList = ref<any[]>([])
const orgTree = ref<any[]>([])

const personForm = ref({
  name: '',
  current_position: '',
  org_affiliation: '',
  level: '',
  gender: '男',
  addressing_rules_formal: '',
  addressing_rules_public: '',
  addressing_rules_avoid: '',
  responsibilities: '',
  notes: ''
})

// 加载人物列表
const loadPeople = async () => {
  loading.value = true
  try {
    const res = await getPeopleListApi()
    peopleList.value = res.people || []
  } catch (error) {
    console.error('Failed to load people:', error)
    ElMessage.error('加载人物列表失败')
  } finally {
    loading.value = false
  }
}

// 加载机构树
const loadOrgTree = async () => {
  try {
    const res = await getOrgTreeApi()
    orgTree.value = res.tree || []
  } catch (error) {
    console.error('Failed to load org tree:', error)
  }
}

// 保存人物
const savePerson = async () => {
  if (!personForm.value.name) {
    ElMessage.warning('请输入姓名')
    return
  }

  saving.value = true
  try {
    const data = {
      ...personForm.value,
      addressing_rules: {
        '正式场合': personForm.value.addressing_rules_formal,
        '公开场合': personForm.value.addressing_rules_public,
        '避免使用': personForm.value.addressing_rules_avoid
      }
    }

    if (isEditing.value) {
      await updatePersonApi(personForm.value.name, data)
      ElMessage.success('更新成功')
    } else {
      await createPersonApi(data)
      ElMessage.success('创建成功')
    }

    showAddDialog.value = false
    loadPeople()
  } catch (error) {
    console.error('Failed to save person:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 编辑人物
const editPerson = (row: any) => {
  isEditing.value = true
  personForm.value = {
    ...row,
    addressing_rules_formal: row.addressing_rules?.['正式场合'] || '',
    addressing_rules_public: row.addressing_rules?.['公开场合'] || '',
    addressing_rules_avoid: row.addressing_rules?.['避免使用'] || ''
  }
  showAddDialog.value = true
}

// 删除人物
const deletePerson = async (name: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除人物 "${name}" 的档案吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deletePersonApi(name)
    ElMessage.success('删除成功')
    loadPeople()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete person:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 搜索
const handleSearch = () => {
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    peopleList.value = peopleList.value.filter(p =>
      p.name.toLowerCase().includes(query) ||
      (p.current_position && p.current_position.toLowerCase().includes(query))
    )
  } else {
    loadPeople()
  }
}

// 获取级别标签类型
const getLevelType = (level?: string) => {
  const map: Record<string, string> = {
    '正部级': 'danger',
    '副部级': 'warning',
    '正厅级': 'primary',
    '副厅级': 'success',
    '正处级': 'info',
    '副处级': '',
    '正科级': '',
    '副科级': ''
  }
  return map[level || ''] || ''
}

// 格式化称谓规则
const formatAddressingRules = (rules: any) => {
  if (!rules) return '未设置'
  return Object.entries(rules)
    .map(([k, v]) => `${k}: ${v}`)
    .join(' | ')
}

// 机构类型颜色
const getOrgTypeColor = (type?: string) => {
  const map: Record<string, string> = {
    '政府': 'primary',
    '党委': 'danger',
    '人大': 'warning',
    '政协': 'success',
    '司法机关': 'info'
  }
  return map[type || ''] || ''
}

// 机构点击
const handleOrgClick = (data: any) => {
  console.log('Selected org:', data)
  // 可以在这里打开机构详情
}

// 重置表单
const resetForm = () => {
  isEditing.value = false
  personForm.value = {
    name: '',
    current_position: '',
    org_affiliation: '',
    level: '',
    gender: '男',
    addressing_rules_formal: '',
    addressing_rules_public: '',
    addressing_rules_avoid: '',
    responsibilities: '',
    notes: ''
  }
}

// 监听对话框关闭
const handleDialogClose = () => {
  resetForm()
}

onMounted(() => {
  loadPeople()
  loadOrgTree()
})
</script>

<style scoped>
.knowledge-page {
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

.knowledge-tabs {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.tab-content {
  padding: 10px 0;
}

.person-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.empty-text {
  color: #909399;
}

.org-tree-container {
  max-height: 600px;
  overflow-y: auto;
}

.org-tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.org-tree-node .el-icon {
  color: #909399;
}

.org-name {
  flex: 1;
}

:deep(.el-tree-node__content) {
  height: 40px;
}
</style>
