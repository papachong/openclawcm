<template>
  <div class="page-container">
    <div class="page-header">
      <h2>Agent管理</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>新增Agent
      </el-button>
    </div>

    <!-- Filter -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="所属实例">
          <el-select v-model="searchForm.instance_id" placeholder="全部实例" clearable>
            <el-option v-for="inst in instances" :key="inst.id" :label="inst.name" :value="inst.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Agent名称">
          <el-input v-model="searchForm.name" placeholder="搜索" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="运行中" value="running" />
            <el-option label="已停止" value="stopped" />
            <el-option label="异常" value="error" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Agent Table -->
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="Agent名称" min-width="150" />
        <el-table-column prop="instance_name" label="所属实例" width="150" />
        <el-table-column prop="role" label="角色" width="120" />
        <el-table-column prop="model_name" label="使用模型" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="skills_count" label="Skills数" width="80" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="success" v-if="row.status !== 'running'" @click="handleStart(row)">启动</el-button>
            <el-button size="small" type="warning" v-if="row.status === 'running'" @click="handleStop(row)">停止</el-button>
            <el-button size="small" @click="handleCopy(row)">复制</el-button>
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

    <!-- Create/Edit Agent Dialog -->
    <el-dialog v-model="showDialog" :title="editingId ? '编辑Agent' : '新增Agent'" width="650px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="Agent名称" prop="name">
          <el-input v-model="form.name" placeholder="Agent名称" />
        </el-form-item>
        <el-form-item label="所属实例" prop="instance_id">
          <el-select v-model="form.instance_id" placeholder="选择实例">
            <el-option v-for="inst in instances" :key="inst.id" :label="inst.name" :value="inst.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-input v-model="form.role" placeholder="如: 代码生成、文档编写" />
        </el-form-item>
        <el-form-item label="使用模型" prop="model_config_id">
          <el-select v-model="form.model_config_id" placeholder="选择模型配置（或使用全局默认）" clearable>
            <el-option v-for="m in modelConfigs" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="System Prompt" prop="system_prompt">
          <el-input v-model="form.system_prompt" type="textarea" :rows="5" placeholder="Agent的系统提示词" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { agentApi, instanceApi, modelApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const tableData = ref([])
const instances = ref([])
const modelConfigs = ref([])

const searchForm = reactive({ instance_id: '', name: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  name: '', instance_id: null, role: '', model_config_id: null,
  system_prompt: '', description: '',
})

const rules = {
  name: [{ required: true, message: '请输入Agent名称', trigger: 'blur' }],
  instance_id: [{ required: true, message: '请选择所属实例', trigger: 'change' }],
}

const statusType = (s) => ({ running: 'success', stopped: 'info', error: 'danger' }[s] || 'info')
const statusLabel = (s) => ({ running: '运行中', stopped: '已停止', error: '异常' }[s] || s)

async function loadData() {
  loading.value = true
  try {
    const res = await agentApi.list({ page: pagination.page, page_size: pagination.pageSize, ...searchForm })
    tableData.value = res.data || []
    pagination.total = res.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function resetSearch() {
  Object.assign(searchForm, { instance_id: '', name: '', status: '' })
  pagination.page = 1
  loadData()
}

function handleEdit(row) {
  editingId.value = row.id
  Object.assign(form, row)
  showDialog.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editingId.value) {
      await agentApi.update(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await agentApi.create(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadData()
  } catch (e) { console.error(e) }
  finally { submitting.value = false }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除 "${row.name}" 吗？`, '提示', { type: 'warning' })
  await agentApi.delete(row.id)
  ElMessage.success('删除成功')
  loadData()
}

async function handleStart(row) { await agentApi.start(row.id); ElMessage.success('启动成功'); loadData() }
async function handleStop(row) { await agentApi.stop(row.id); ElMessage.success('已停止'); loadData() }
async function handleCopy(row) {
  await ElMessageBox.confirm(`复制 "${row.name}" 到其他实例？`, '复制Agent')
  await agentApi.copy(row.id, {})
  ElMessage.success('复制成功')
  loadData()
}

function resetForm() {
  editingId.value = null
  Object.assign(form, { name: '', instance_id: null, role: '', model_config_id: null, system_prompt: '', description: '' })
}

async function loadRefs() {
  try {
    const [instRes, modelRes] = await Promise.all([instanceApi.list(), modelApi.list()])
    instances.value = instRes.data || []
    modelConfigs.value = modelRes.data || []
  } catch (e) { console.error(e) }
}

onMounted(() => { loadData(); loadRefs() })
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h2 { margin: 0; color: #303133; }
.search-card { margin-bottom: 0; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
