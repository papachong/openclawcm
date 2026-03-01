<template>
  <div class="page-container">
    <div class="page-header">
      <h2>共享记忆池</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>新建记忆池
      </el-button>
    </div>

    <!-- Pool List -->
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="记忆池名称" min-width="160" />
        <el-table-column prop="memory_type" label="记忆类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ memoryTypeLabel(row.memory_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="max_history_messages" label="最大消息数" width="110" />
        <el-table-column prop="max_token_limit" label="Token上限" width="110" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="agent_count" label="Agent数" width="90" />
        <el-table-column label="运行时统计" width="200">
          <template #default="{ row }">
            <span>消息: {{ row.message_count || 0 }}</span>
            <el-divider direction="vertical" />
            <span>Token: {{ row.total_tokens || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="primary" @click="openAgentsDialog(row)">Agent绑定</el-button>
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
    <el-dialog v-model="showDialog" :title="editingId ? '编辑记忆池' : '新建记忆池'" width="600px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="130px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="记忆池名称" />
        </el-form-item>
        <el-form-item label="记忆类型" prop="memory_type">
          <el-select v-model="form.memory_type">
            <el-option label="缓冲记忆(Buffer)" value="buffer" />
            <el-option label="摘要记忆(Summary)" value="summary" />
            <el-option label="混合记忆(Buffer+Summary)" value="buffer_summary" />
          </el-select>
        </el-form-item>
        <el-form-item label="最大历史消息数">
          <el-input-number v-model="form.max_history_messages" :min="1" :max="500" />
        </el-form-item>
        <el-form-item label="最大Token限制">
          <el-input-number v-model="form.max_token_limit" :min="100" :max="256000" :step="1000" />
        </el-form-item>
        <el-form-item label="关联协作流程">
          <el-select v-model="form.collaboration_id" placeholder="可选 - 关联协作流程" clearable>
            <el-option v-for="c in collaborations" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" v-if="editingId">
          <el-select v-model="form.status">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="inactive" />
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

    <!-- Agent Binding Dialog -->
    <el-dialog v-model="showAgentsDialog" :title="`${currentPoolName} - Agent绑定`" width="650px">
      <div style="margin-bottom: 16px; display: flex; gap: 8px;">
        <el-select v-model="agentToAdd" placeholder="选择Agent" filterable style="flex: 1;">
          <el-option v-for="a in availableAgents" :key="a.id" :label="`${a.name} (${a.instance_name || ''})`" :value="a.id" />
        </el-select>
        <el-select v-model="permissionToAdd" style="width: 130px;">
          <el-option label="读写" value="readwrite" />
          <el-option label="只读" value="read" />
          <el-option label="只写" value="write" />
        </el-select>
        <el-button type="primary" @click="handleBindAgent" :disabled="!agentToAdd">绑定</el-button>
      </div>
      <el-table :data="poolAgents" v-loading="agentsLoading" stripe>
        <el-table-column prop="agent_name" label="Agent名称" min-width="150" />
        <el-table-column prop="permission" label="权限" width="120">
          <template #default="{ row }">
            <el-tag :type="row.permission === 'readwrite' ? 'success' : row.permission === 'read' ? 'info' : 'warning'" size="small">
              {{ { readwrite: '读写', read: '只读', write: '只写' }[row.permission] || row.permission }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleUnbindAgent(row)">解绑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="poolAgents.length === 0 && !agentsLoading" description="暂无绑定的Agent" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { memoryPoolApi, agentApi, collaborationApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const tableData = ref([])
const collaborations = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

// Agent binding state
const showAgentsDialog = ref(false)
const currentPoolId = ref(null)
const currentPoolName = ref('')
const poolAgents = ref([])
const allAgents = ref([])
const agentToAdd = ref(null)
const permissionToAdd = ref('readwrite')
const agentsLoading = ref(false)

const form = reactive({
  name: '', description: '', memory_type: 'buffer',
  max_history_messages: 50, max_token_limit: 8000,
  collaboration_id: null, status: 'active',
})

const rules = {
  name: [{ required: true, message: '请输入记忆池名称', trigger: 'blur' }],
}

const memoryTypeLabel = (t) => ({
  buffer: '缓冲', summary: '摘要', buffer_summary: '混合',
}[t] || t)

const availableAgents = computed(() => {
  const boundIds = new Set(poolAgents.value.map(a => a.agent_id))
  return allAgents.value.filter(a => !boundIds.has(a.id))
})

async function loadData() {
  loading.value = true
  try {
    const res = await memoryPoolApi.list({ page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data || []
    pagination.total = res.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function openCreateDialog() {
  resetForm()
  showDialog.value = true
}

function handleEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name, description: row.description, memory_type: row.memory_type,
    max_history_messages: row.max_history_messages, max_token_limit: row.max_token_limit,
    collaboration_id: row.collaboration_id, status: row.status,
  })
  showDialog.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editingId.value) {
      await memoryPoolApi.update(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await memoryPoolApi.create(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadData()
  } catch (e) { console.error(e) }
  finally { submitting.value = false }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除记忆池 "${row.name}" 吗？绑定的Agent关系将一并删除。`, '提示', { type: 'warning' })
  await memoryPoolApi.delete(row.id)
  ElMessage.success('删除成功')
  loadData()
}

function resetForm() {
  editingId.value = null
  Object.assign(form, {
    name: '', description: '', memory_type: 'buffer',
    max_history_messages: 50, max_token_limit: 8000,
    collaboration_id: null, status: 'active',
  })
}

// ==================== Agent Binding ====================
async function openAgentsDialog(row) {
  currentPoolId.value = row.id
  currentPoolName.value = row.name
  agentToAdd.value = null
  permissionToAdd.value = 'readwrite'
  showAgentsDialog.value = true
  await loadPoolAgents()
}

async function loadPoolAgents() {
  agentsLoading.value = true
  try {
    const res = await memoryPoolApi.listAgents(currentPoolId.value)
    poolAgents.value = res || []
  } catch (e) { console.error(e) }
  finally { agentsLoading.value = false }
}

async function handleBindAgent() {
  if (!agentToAdd.value) return
  try {
    await memoryPoolApi.bindAgent(currentPoolId.value, {
      agent_id: agentToAdd.value, permission: permissionToAdd.value,
    })
    ElMessage.success('绑定成功')
    agentToAdd.value = null
    await loadPoolAgents()
    loadData()
  } catch (e) { console.error(e) }
}

async function handleUnbindAgent(row) {
  await ElMessageBox.confirm(`确定解绑 "${row.agent_name}" 吗？`, '提示', { type: 'warning' })
  await memoryPoolApi.unbindAgent(currentPoolId.value, row.agent_id)
  ElMessage.success('解绑成功')
  await loadPoolAgents()
  loadData()
}

async function loadRefs() {
  try {
    const [agentRes, collabRes] = await Promise.all([agentApi.list(), collaborationApi.list()])
    allAgents.value = agentRes.data || []
    collaborations.value = collabRes.data || []
  } catch (e) { console.error(e) }
}

onMounted(() => { loadData(); loadRefs() })
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h2 { margin: 0; color: #303133; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
