<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ $t('agents.title') }}</h2>
      <div style="display: flex; gap: 8px;">
        <el-button type="warning" @click="handleSyncAll" :loading="syncing">
          <el-icon><Refresh /></el-icon>同步远端配置
        </el-button>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>{{ $t('agents.addAgent') }}
        </el-button>
      </div>
    </div>

    <!-- Filter -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item :label="$t('agents.belongInstance')">
          <el-select v-model="searchForm.instance_id" :placeholder="$t('agents.allInstances')" clearable>
            <el-option v-for="inst in instances" :key="inst.id" :label="inst.name" :value="inst.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('agents.agentName')">
          <el-input v-model="searchForm.name" :placeholder="$t('common.search')" clearable />
        </el-form-item>
        <el-form-item :label="$t('common.status')">
          <el-select v-model="searchForm.status" :placeholder="$t('common.all')" clearable>
            <el-option :label="$t('agents.running')" value="running" />
            <el-option :label="$t('agents.stopped')" value="stopped" />
            <el-option :label="$t('agents.error')" value="error" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">{{ $t('common.query') }}</el-button>
          <el-button @click="resetSearch">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Agent Table -->
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" :label="$t('agents.agentName')" min-width="150" />
        <el-table-column prop="instance_name" :label="$t('agents.belongInstance')" width="150" />
        <el-table-column prop="role" :label="$t('agents.role')" width="120" />
        <el-table-column prop="model_name" :label="$t('agents.useModel')" width="150" />
        <el-table-column prop="memory_type" :label="$t('agents.memoryType')" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ memoryTypeLabel(row.memory_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="skills_count" :label="$t('agents.skillsCount')" width="80" />
        <el-table-column :label="$t('common.operation')" width="320" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" type="primary" @click="openSkillsDialog(row)">Skills</el-button>
            <el-button size="small" type="success" v-if="row.status !== 'running'" @click="handleStart(row)">{{ $t('agents.start') }}</el-button>
            <el-button size="small" type="warning" v-if="row.status === 'running'" @click="handleStop(row)">{{ $t('agents.stop') }}</el-button>
            <el-button size="small" @click="handleCopy(row)">{{ $t('agents.copy') }}</el-button>
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

    <!-- Create/Edit Agent Dialog (Tabbed) -->
    <el-dialog v-model="showDialog" :title="editingId ? $t('agents.editAgent') : $t('agents.addAgent')" width="720px" @close="resetForm">
      <el-tabs v-model="activeTab">
        <!-- Tab 1: Basic Info -->
        <el-tab-pane :label="$t('agents.basicInfo')" name="basic">
          <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
            <el-form-item :label="$t('agents.agentName')" prop="name">
              <el-input v-model="form.name" :placeholder="$t('agents.agentNamePlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('agents.belongInstance')" prop="instance_id">
              <el-select v-model="form.instance_id" :placeholder="$t('agents.selectInstance')">
                <el-option v-for="inst in instances" :key="inst.id" :label="inst.name" :value="inst.id" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('agents.role')" prop="role">
              <el-input v-model="form.role" :placeholder="$t('agents.rolePlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('agents.useModel')" prop="model_config_id">
              <el-select v-model="form.model_config_id" :placeholder="$t('agents.selectModel')" clearable>
                <el-option v-for="m in modelConfigs" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('agents.systemPrompt')" prop="system_prompt">
              <el-input v-model="form.system_prompt" type="textarea" :rows="5" :placeholder="$t('agents.systemPromptPlaceholder')" />
            </el-form-item>
            <el-form-item :label="$t('common.description')">
              <el-input v-model="form.description" type="textarea" :rows="2" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Tab 2: Memory Config -->
        <el-tab-pane :label="$t('agents.memoryConfig')" name="memory">
          <el-form :model="form" label-width="140px">
            <el-form-item :label="$t('agents.memoryType')">
              <el-select v-model="form.memory_type" :placeholder="$t('agents.selectMemoryType')">
                <el-option :label="$t('agents.memoryBuffer')" value="buffer" />
                <el-option :label="$t('agents.memorySummary')" value="summary" />
                <el-option :label="$t('agents.memoryMixed')" value="buffer_summary" />
                <el-option :label="$t('agents.memoryNone')" value="none" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('agents.maxHistoryMessages')" v-if="form.memory_type !== 'none'">
              <el-input-number v-model="form.max_history_messages" :min="1" :max="200" />
              <span class="form-tip">{{ $t('agents.keepRecentN') }}</span>
            </el-form-item>
            <el-form-item :label="$t('agents.maxTokenLimit')" v-if="form.memory_type !== 'none'">
              <el-input-number v-model="form.max_token_limit" :min="100" :max="128000" :step="500" />
              <span class="form-tip">{{ $t('agents.maxTokenTip') }}</span>
            </el-form-item>
            <el-form-item :label="$t('agents.summaryModel')" v-if="form.memory_type === 'summary' || form.memory_type === 'buffer_summary'">
              <el-select v-model="form.summary_model_id" :placeholder="$t('agents.summaryModelDefault')" clearable>
                <el-option v-for="m in modelConfigs" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
              <div class="form-tip">{{ $t('agents.summaryModelTip') }}</div>
            </el-form-item>
            <el-form-item :label="$t('agents.memoryPersistence')" v-if="form.memory_type !== 'none'">
              <el-switch v-model="memoryPersistence" :active-text="$t('agents.yes')" :inactive-text="$t('agents.no')" />
              <span class="form-tip">{{ $t('agents.persistenceTip') }}</span>
            </el-form-item>
            <el-form-item :label="$t('agents.autoCleanup')" v-if="form.memory_type !== 'none'">
              <el-input-number v-model="form.auto_cleanup_days" :min="0" :max="365" />
              <span class="form-tip">{{ $t('agents.autoCleanupTip') }}</span>
            </el-form-item>
            <!-- Memory type description -->
            <el-alert v-if="form.memory_type === 'buffer'" type="info" :closable="false" class="memory-tip">
              <template #title>{{ $t('agents.bufferDesc') }}</template>
            </el-alert>
            <el-alert v-if="form.memory_type === 'summary'" type="info" :closable="false" class="memory-tip">
              <template #title>{{ $t('agents.summaryDesc') }}</template>
            </el-alert>
            <el-alert v-if="form.memory_type === 'buffer_summary'" type="info" :closable="false" class="memory-tip">
              <template #title>{{ $t('agents.mixedDesc') }}</template>
            </el-alert>
            <el-alert v-if="form.memory_type === 'none'" type="warning" :closable="false" class="memory-tip">
              <template #title>{{ $t('agents.noneDesc') }}</template>
            </el-alert>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- Skills Binding Dialog -->
    <el-dialog v-model="showSkillsDialog" :title="$t('agents.skillsManage', { name: currentAgentName })" width="650px">
      <div style="margin-bottom: 16px; display: flex; gap: 8px;">
        <el-select v-model="skillToAdd" :placeholder="$t('agents.selectSkill')" filterable style="flex: 1;">
          <el-option v-for="s in availableSkills" :key="s.id" :label="`${s.name} (v${s.version})`" :value="s.id" />
        </el-select>
        <el-button type="primary" @click="handleBindSkill" :disabled="!skillToAdd">{{ $t('agents.bind') }}</el-button>
      </div>
      <el-table :data="agentSkills" v-loading="skillsLoading" stripe>
        <el-table-column prop="skill_name" :label="$t('agents.skillName')" min-width="150" />
        <el-table-column prop="skill_version" :label="$t('agents.version')" width="100" />
        <el-table-column prop="skill_status" :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="row.skill_status === 'installed' ? 'success' : 'info'" size="small">
              {{ row.skill_status === 'installed' ? $t('agents.installed') : $t('agents.available') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleUnbindSkill(row)">{{ $t('agents.unbind') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="agentSkills.length === 0 && !skillsLoading" :description="$t('agents.noSkills')" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { agentApi, instanceApi, modelApi, skillApi } from '@/api'

const { t } = useI18n()
const loading = ref(false)
const submitting = ref(false)
const syncing = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const tableData = ref([])
const instances = ref([])
const modelConfigs = ref([])
const activeTab = ref('basic')

// Skills binding state
const showSkillsDialog = ref(false)
const currentAgentId = ref(null)
const currentAgentName = ref('')
const agentSkills = ref([])
const allSkills = ref([])
const skillToAdd = ref(null)
const skillsLoading = ref(false)

const searchForm = reactive({ instance_id: null, name: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  name: '', instance_id: null, role: '', model_config_id: null,
  system_prompt: '', description: '',
  // Memory config
  memory_type: 'buffer', max_history_messages: 20, max_token_limit: 4000,
  summary_model_id: null, memory_persistence: 1, auto_cleanup_days: 0,
})

const rules = computed(() => ({
  name: [{ required: true, message: t('agents.pleaseInputName'), trigger: 'blur' }],
  instance_id: [{ required: true, message: t('agents.pleaseSelectInstance'), trigger: 'change' }],
}))

// Computed: switch boolean <-> int for memory_persistence
const memoryPersistence = computed({
  get: () => form.memory_persistence === 1,
  set: (val) => { form.memory_persistence = val ? 1 : 0 },
})

// Available skills = all skills minus already bound ones
const availableSkills = computed(() => {
  const boundIds = new Set(agentSkills.value.map(s => s.skill_id))
  return allSkills.value.filter(s => !boundIds.has(s.id))
})

const statusType = (s) => ({ running: 'success', stopped: 'info', error: 'danger' }[s] || 'info')
const statusLabel = (s) => ({
  running: t('agents.running'), stopped: t('agents.stopped'), error: t('agents.error')
}[s] || s)
const memoryTypeLabel = (mt) => ({
  buffer: t('agents.memoryBufferShort'), summary: t('agents.memorySummaryShort'),
  buffer_summary: t('agents.memoryMixedShort'), none: t('agents.memoryNoneShort')
}[mt] || mt)

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...(searchForm.instance_id ? { instance_id: searchForm.instance_id } : {}),
      ...(searchForm.name ? { name: searchForm.name } : {}),
      ...(searchForm.status ? { status: searchForm.status } : {}),
    }
    const res = await agentApi.list(params)
    tableData.value = res.data || []
    pagination.total = res.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function resetSearch() {
  Object.assign(searchForm, { instance_id: null, name: '', status: '' })
  pagination.page = 1
  loadData()
}

function openCreateDialog() {
  resetForm()
  showDialog.value = true
}

function handleEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name, instance_id: row.instance_id, role: row.role,
    model_config_id: row.model_config_id, system_prompt: row.system_prompt,
    description: row.description,
    memory_type: row.memory_type || 'buffer',
    max_history_messages: row.max_history_messages || 20,
    max_token_limit: row.max_token_limit || 4000,
    summary_model_id: row.summary_model_id,
    memory_persistence: row.memory_persistence !== undefined ? row.memory_persistence : 1,
    auto_cleanup_days: row.auto_cleanup_days || 0,
  })
  activeTab.value = 'basic'
  showDialog.value = true
}

async function handleSubmit() {
  if (activeTab.value === 'basic') {
    await formRef.value.validate()
  }
  submitting.value = true
  try {
    if (editingId.value) {
      await agentApi.update(editingId.value, form)
      ElMessage.success(t('common.success.update'))
    } else {
      await agentApi.create(form)
      ElMessage.success(t('common.success.create'))
    }
    showDialog.value = false
    loadData()
  } catch (e) { console.error(e) }
  finally { submitting.value = false }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('agents.confirmDelete', { name: row.name }), t('common.tip'), { type: 'warning' })
  await agentApi.delete(row.id)
  ElMessage.success(t('common.success.delete'))
  loadData()
}

async function handleStart(row) { await agentApi.start(row.id); ElMessage.success(t('agents.startSuccess')); loadData() }
async function handleStop(row) { await agentApi.stop(row.id); ElMessage.success(t('agents.stopSuccess')); loadData() }
async function handleCopy(row) {
  await ElMessageBox.confirm(t('agents.confirmCopy', { name: row.name }), t('agents.copyAgent'))
  await agentApi.copy(row.id, {})
  ElMessage.success(t('agents.copySuccess'))
  loadData()
}

function resetForm() {
  editingId.value = null
  activeTab.value = 'basic'
  Object.assign(form, {
    name: '', instance_id: null, role: '', model_config_id: null,
    system_prompt: '', description: '',
    memory_type: 'buffer', max_history_messages: 20, max_token_limit: 4000,
    summary_model_id: null, memory_persistence: 1, auto_cleanup_days: 0,
  })
}

// ==================== Skills Binding ====================
async function openSkillsDialog(row) {
  currentAgentId.value = row.id
  currentAgentName.value = row.name
  skillToAdd.value = null
  showSkillsDialog.value = true
  await loadAgentSkills()
}

async function loadAgentSkills() {
  skillsLoading.value = true
  try {
    const res = await agentApi.listSkills(currentAgentId.value)
    agentSkills.value = res || []
  } catch (e) { console.error(e) }
  finally { skillsLoading.value = false }
}

async function handleBindSkill() {
  if (!skillToAdd.value) return
  try {
    await agentApi.bindSkill(currentAgentId.value, { skill_id: skillToAdd.value })
    ElMessage.success(t('agents.bindSuccess'))
    skillToAdd.value = null
    await loadAgentSkills()
    loadData()
  } catch (e) { console.error(e) }
}

async function handleUnbindSkill(row) {
  await ElMessageBox.confirm(t('agents.confirmUnbind', { name: row.skill_name }), t('common.tip'), { type: 'warning' })
  await agentApi.unbindSkill(currentAgentId.value, row.skill_id)
  ElMessage.success(t('agents.unbindSuccess'))
  await loadAgentSkills()
  loadData()
}

async function loadRefs() {
  try {
    const [instRes, modelRes, skillRes] = await Promise.all([
      instanceApi.list(), modelApi.list(), skillApi.list()
    ])
    instances.value = instRes.data || []
    modelConfigs.value = modelRes.data || []
    allSkills.value = skillRes.data || []
  } catch (e) { console.error(e) }
}

async function handleSyncAll() {
  syncing.value = true
  try {
    const res = await instanceApi.syncAll()
    const d = res.data || res
    ElMessage.success(`同步完成，共 ${d.total || 0} 个实例`)
    await loadData()
    await loadRefs()
  } catch (e) {
    ElMessage.error(`同步失败: ${e.message || '未知错误'}`)
  } finally {
    syncing.value = false
  }
}

onMounted(async () => {
  await loadRefs()
  // Auto-sync all instances on page load, then reload data
  instanceApi.syncAll().then(() => { loadData(); loadRefs() }).catch(() => {})
  loadData()
})
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h2 { margin: 0; color: #303133; }
.search-card { margin-bottom: 0; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
.form-tip { margin-left: 12px; color: #909399; font-size: 12px; }
.memory-tip { margin-top: 16px; }
</style>
