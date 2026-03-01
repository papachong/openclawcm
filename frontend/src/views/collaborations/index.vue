<template>
  <div class="page-container">
    <div class="page-header">
      <h2>多Agent协作配置</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>新建协作流程
      </el-button>
    </div>

    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="流程名称" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="openEditor(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="协作类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ flowTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="agent_count" label="Agent数" width="90" />
        <el-table-column label="节点/连线" width="100">
          <template #default="{ row }">
            {{ row.node_count || 0 }} / {{ row.edge_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEditor(row)">编辑器</el-button>
            <el-button size="small" @click="handleEdit(row)">属性</el-button>
            <el-button v-if="row.status !== 'running'" size="small" type="success" @click="handleStart(row)">启动</el-button>
            <el-button v-else size="small" type="warning" @click="handleStop(row)">停止</el-button>
            <el-button size="small" @click="handleSaveTemplate(row)">模板</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && tableData.length === 0" description="暂无协作配置" />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showDialog" :title="editingId ? '编辑协作流程' : '新建协作流程'" width="700px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="流程名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="协作类型" prop="type">
          <el-select v-model="form.type">
            <el-option label="链式协作" value="chain" />
            <el-option label="并行协作" value="parallel" />
            <el-option label="条件分支" value="conditional" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行模式">
          <el-select v-model="form.execution_mode">
            <el-option label="顺序执行" value="sequential" />
            <el-option label="并行执行" value="parallel" />
            <el-option label="条件执行" value="conditional" />
          </el-select>
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { collaborationApi } from '@/api'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const tableData = ref([])

const form = reactive({ name: '', type: 'chain', execution_mode: 'sequential', description: '' })
const rules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }

const flowTypeLabel = (t) => ({ chain: '链式', parallel: '并行', conditional: '条件分支', custom: '自定义' }[t] || t)
const statusType = (s) => ({ running: 'success', inactive: 'info', error: 'danger', active: 'success' }[s] || 'info')
const statusLabel = (s) => ({ running: '运行中', inactive: '已停止', error: '错误', active: '运行中' }[s] || s)

async function loadData() {
  loading.value = true
  try {
    const res = await collaborationApi.list()
    tableData.value = res.data || []
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function openEditor(row) {
  router.push(`/collaborations/${row.id}/editor`)
}

function handleEdit(row) {
  editingId.value = row.id
  Object.assign(form, { name: row.name, type: row.type, execution_mode: row.execution_mode || 'sequential', description: row.description })
  showDialog.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editingId.value) {
      await collaborationApi.update(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      const res = await collaborationApi.create(form)
      ElMessage.success('创建成功')
      // Navigate to editor for new flow
      if (res?.id) router.push(`/collaborations/${res.id}/editor`)
    }
    showDialog.value = false
    loadData()
  } catch (e) { console.error(e) }
  finally { submitting.value = false }
}

async function handleStart(row) {
  try {
    await collaborationApi.start(row.id)
    row.status = 'running'
    ElMessage.success('已启动')
  } catch (e) { console.error(e) }
}

async function handleStop(row) {
  try {
    await collaborationApi.stop(row.id)
    row.status = 'inactive'
    ElMessage.success('已停止')
  } catch (e) { console.error(e) }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除 "${row.name}" 吗？将同时删除所有节点和连线。`, '提示', { type: 'warning' })
  await collaborationApi.delete(row.id)
  ElMessage.success('删除成功')
  loadData()
}

async function handleSaveTemplate(row) {
  await collaborationApi.saveAsTemplate(row.id)
  ElMessage.success('已保存为模板')
}

function resetForm() {
  editingId.value = null
  Object.assign(form, { name: '', type: 'chain', execution_mode: 'sequential', description: '' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h2 { margin: 0; color: #303133; }
</style>
