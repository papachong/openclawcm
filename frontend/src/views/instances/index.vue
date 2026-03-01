<template>
  <div class="page-container">
    <div class="page-header">
      <h2>实例管理</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>新增实例
      </el-button>
    </div>

    <!-- Search Bar -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="实例名称">
          <el-input v-model="searchForm.name" placeholder="搜索实例名称" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Data Table -->
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="实例名称" min-width="150" />
        <el-table-column prop="url" label="连接地址" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'danger'">
              {{ row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="group_name" label="分组" width="120" />
        <el-table-column prop="agent_count" label="Agent数" width="100" />
        <el-table-column prop="last_heartbeat" label="最后心跳" width="170">
          <template #default="{ row }">
            <span v-if="row.last_heartbeat">{{ row.last_heartbeat }}</span>
            <span v-else style="color: #909399">暂无</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="success" @click="handleHealthCheck(row)">检测</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showDialog"
      :title="editingId ? '编辑实例' : '新增实例'"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="实例名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入实例名称" />
        </el-form-item>
        <el-form-item label="连接地址" prop="url">
          <el-input v-model="form.url" placeholder="http://localhost:8080" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" placeholder="可选" show-password />
        </el-form-item>
        <el-form-item label="分组" prop="group_name">
          <el-input v-model="form.group_name" placeholder="如: 开发/测试/生产" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="实例描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { instanceApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const tableData = ref([])

const searchForm = reactive({ name: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  name: '',
  url: '',
  api_key: '',
  group_name: '',
  description: '',
})

const rules = {
  name: [{ required: true, message: '请输入实例名称', trigger: 'blur' }],
  url: [{ required: true, message: '请输入连接地址', trigger: 'blur' }],
}

async function loadData() {
  loading.value = true
  try {
    const res = await instanceApi.list({
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm,
    })
    tableData.value = res.data || []
    pagination.total = res.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function resetSearch() {
  searchForm.name = ''
  searchForm.status = ''
  pagination.page = 1
  loadData()
}

function handleEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    url: row.url,
    api_key: row.api_key || '',
    group_name: row.group_name || '',
    description: row.description || '',
  })
  showDialog.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editingId.value) {
      await instanceApi.update(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await instanceApi.create(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadData()
  } catch (e) {
    console.error(e)
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除实例 "${row.name}" 吗？`, '提示', { type: 'warning' })
  try {
    await instanceApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    console.error(e)
  }
}

async function handleHealthCheck(row) {
  try {
    await instanceApi.checkHealth(row.id)
    ElMessage.success('连通性检测成功')
    loadData()
  } catch (e) {
    ElMessage.error('连通性检测失败')
  }
}

function resetForm() {
  editingId.value = null
  Object.assign(form, { name: '', url: '', api_key: '', group_name: '', description: '' })
  formRef.value?.resetFields()
}

onMounted(() => loadData())

// Auto-refresh every 30 seconds
let pollTimer = null
onMounted(() => {
  pollTimer = setInterval(() => loadData(), 30000)
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.search-card {
  margin-bottom: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
