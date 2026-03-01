<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ $t('memoryPools.title') }}</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>{{ $t('memoryPools.addPool') }}
      </el-button>
    </div>

    <!-- Pool List -->
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" :label="$t('memoryPools.poolName')" min-width="160" />
        <el-table-column prop="memory_type" :label="$t('memoryPools.memoryType')" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ memoryTypeLabel(row.memory_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="max_history_messages" :label="$t('memoryPools.maxMessages')" width="110" />
        <el-table-column prop="max_token_limit" :label="$t('memoryPools.tokenLimit')" width="110" />
        <el-table-column prop="status" :label="$t('common.status')" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? $t('common.enabled') : $t('common.disabled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="agent_count" :label="$t('memoryPools.agentCount')" width="90" />
        <el-table-column :label="$t('memoryPools.runtimeStats')" width="200">
          <template #default="{ row }">
            <span>{{ $t('memoryPools.messageCount') }} {{ row.message_count || 0 }}</span>
            <el-divider direction="vertical" />
            <span>{{ $t('memoryPools.tokenCount') }} {{ row.total_tokens || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="$t('common.description')" min-width="150" show-overflow-tooltip />
        <el-table-column :label="$t('common.operation')" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" type="primary" @click="openAgentsDialog(row)">{{ $t('memoryPools.agentBinding') }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
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
    <el-dialog v-model="showDialog" :title="editingId ? $t('memoryPools.editPool') : $t('memoryPools.addPool')" width="600px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="130px">
        <el-form-item :label="$t('common.name')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('memoryPools.poolNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('memoryPools.memoryType')" prop="memory_type">
          <el-select v-model="form.memory_type">
            <el-option :label="$t('memoryPools.memoryBuffer')" value="buffer" />
            <el-option :label="$t('memoryPools.memorySummary')" value="summary" />
            <el-option :label="$t('memoryPools.memoryMixed')" value="buffer_summary" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('memoryPools.maxHistoryMessages')">
          <el-input-number v-model="form.max_history_messages" :min="1" :max="500" />
        </el-form-item>
        <el-form-item :label="$t('memoryPools.maxTokenLimit')">
          <el-input-number v-model="form.max_token_limit" :min="100" :max="256000" :step="1000" />
        </el-form-item>
        <el-form-item :label="$t('memoryPools.relatedCollaboration')">
          <el-select v-model="form.collaboration_id" :placeholder="$t('memoryPools.relatedCollaborationPlaceholder')" clearable>
            <el-option v-for="c in collaborations" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.status')" v-if="editingId">
          <el-select v-model="form.status">
            <el-option :label="$t('common.enabled')" value="active" />
            <el-option :label="$t('common.disabled')" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.description')">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- Agent Binding Dialog -->
    <el-dialog v-model="showAgentsDialog" :title="$t('memoryPools.agentBindingTitle', { name: currentPoolName })" width="650px">
      <div style="margin-bottom: 16px; display: flex; gap: 8px;">
        <el-select v-model="agentToAdd" :placeholder="$t('memoryPools.selectAgent')" filterable style="flex: 1;">
          <el-option v-for="a in availableAgents" :key="a.id" :label="`${a.name} (${a.instance_name || ''})`" :value="a.id" />
        </el-select>
        <el-select v-model="permissionToAdd" style="width: 130px;">
          <el-option :label="$t('memoryPools.readwrite')" value="readwrite" />
          <el-option :label="$t('memoryPools.readonly')" value="read" />
          <el-option :label="$t('memoryPools.writeonly')" value="write" />
        </el-select>
        <el-button type="primary" @click="handleBindAgent" :disabled="!agentToAdd">{{ $t('agents.bind') }}</el-button>
      </div>
      <el-table :data="poolAgents" v-loading="agentsLoading" stripe>
        <el-table-column prop="agent_name" :label="$t('memoryPools.agentName')" min-width="150" />
        <el-table-column prop="permission" :label="$t('memoryPools.permission')" width="120">
          <template #default="{ row }">
            <el-tag :type="row.permission === 'readwrite' ? 'success' : row.permission === 'read' ? 'info' : 'warning'" size="small">
              {{ { readwrite: $t('memoryPools.readwrite'), read: $t('memoryPools.readonly'), write: $t('memoryPools.writeonly') }[row.permission] || row.permission }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleUnbindAgent(row)">{{ $t('agents.unbind') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="poolAgents.length === 0 && !agentsLoading" :description="$t('memoryPools.noAgentBound')" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { memoryPoolApi, agentApi, collaborationApi } from '@/api'

const { t } = useI18n()
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

const rules = computed(() => ({
  name: [{ required: true, message: t('memoryPools.pleaseInputName'), trigger: 'blur' }],
}))

const memoryTypeLabel = (mt) => ({
  buffer: t('memoryPools.memoryBufferShort'), summary: t('memoryPools.memorySummaryShort'),
  buffer_summary: t('memoryPools.memoryMixedShort'),
}[mt] || mt)

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
      ElMessage.success(t('common.success.update'))
    } else {
      await memoryPoolApi.create(form)
      ElMessage.success(t('common.success.create'))
    }
    showDialog.value = false
    loadData()
  } catch (e) { console.error(e) }
  finally { submitting.value = false }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('memoryPools.confirmDelete', { name: row.name }), t('common.tip'), { type: 'warning' })
  await memoryPoolApi.delete(row.id)
  ElMessage.success(t('common.success.delete'))
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
    ElMessage.success(t('memoryPools.bindSuccess'))
    agentToAdd.value = null
    await loadPoolAgents()
    loadData()
  } catch (e) { console.error(e) }
}

async function handleUnbindAgent(row) {
  await ElMessageBox.confirm(t('memoryPools.confirmUnbind', { name: row.agent_name }), t('common.tip'), { type: 'warning' })
  await memoryPoolApi.unbindAgent(currentPoolId.value, row.agent_id)
  ElMessage.success(t('memoryPools.unbindSuccess'))
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
