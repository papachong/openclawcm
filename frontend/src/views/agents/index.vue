<template>
  <div class="page-container">
    <div class="page-header">
      <h2>Agent管理</h2>
      <el-button type="primary" @click="openCreateDialog">
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
        <el-table-column prop="memory_type" label="记忆类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ memoryTypeLabel(row.memory_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="skills_count" label="Skills数" width="80" />
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="primary" @click="openSkillsDialog(row)">Skills</el-button>
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

    <!-- Create/Edit Agent Dialog (Tabbed) -->
    <el-dialog v-model="showDialog" :title="editingId ? '编辑Agent' : '新增Agent'" width="720px" @close="resetForm">
      <el-tabs v-model="activeTab">
        <!-- Tab 1: Basic Info -->
        <el-tab-pane label="基本信息" name="basic">
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
        </el-tab-pane>

        <!-- Tab 2: Memory Config -->
        <el-tab-pane label="记忆配置" name="memory">
          <el-form :model="form" label-width="140px">
            <el-form-item label="记忆类型">
              <el-select v-model="form.memory_type" placeholder="选择记忆类型">
                <el-option label="缓冲记忆(Buffer)" value="buffer" />
                <el-option label="摘要记忆(Summary)" value="summary" />
                <el-option label="混合记忆(Buffer+Summary)" value="buffer_summary" />
                <el-option label="无记忆(None)" value="none" />
              </el-select>
            </el-form-item>
            <el-form-item label="最大历史消息数" v-if="form.memory_type !== 'none'">
              <el-input-number v-model="form.max_history_messages" :min="1" :max="200" />
              <span class="form-tip">保留最近N轮对话</span>
            </el-form-item>
            <el-form-item label="最大Token限制" v-if="form.memory_type !== 'none'">
              <el-input-number v-model="form.max_token_limit" :min="100" :max="128000" :step="500" />
              <span class="form-tip">记忆内容的最大Token数</span>
            </el-form-item>
            <el-form-item label="摘要用模型" v-if="form.memory_type === 'summary' || form.memory_type === 'buffer_summary'">
              <el-select v-model="form.summary_model_id" placeholder="默认使用Agent主模型" clearable>
                <el-option v-for="m in modelConfigs" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
              <div class="form-tip">可选择低成本模型用于摘要生成</div>
            </el-form-item>
            <el-form-item label="持久化记忆" v-if="form.memory_type !== 'none'">
              <el-switch v-model="memoryPersistence" active-text="是" inactive-text="否" />
              <span class="form-tip">Agent重启后是否恢复记忆</span>
            </el-form-item>
            <el-form-item label="自动清理(天)" v-if="form.memory_type !== 'none'">
              <el-input-number v-model="form.auto_cleanup_days" :min="0" :max="365" />
              <span class="form-tip">0 为不自动清理</span>
            </el-form-item>
            <!-- Memory type description -->
            <el-alert v-if="form.memory_type === 'buffer'" type="info" :closable="false" class="memory-tip">
              <template #title>缓冲记忆：保留最近N轮对话的原始内容，适合短期任务和简单对话场景。</template>
            </el-alert>
            <el-alert v-if="form.memory_type === 'summary'" type="info" :closable="false" class="memory-tip">
              <template #title>摘要记忆：用LLM对历史对话进行摘要压缩，适合长对话、低Token消耗场景。</template>
            </el-alert>
            <el-alert v-if="form.memory_type === 'buffer_summary'" type="info" :closable="false" class="memory-tip">
              <template #title>混合记忆：近期对话保留原文 + 早期对话压缩为摘要，平衡精度与成本。</template>
            </el-alert>
            <el-alert v-if="form.memory_type === 'none'" type="warning" :closable="false" class="memory-tip">
              <template #title>无记忆模式：每次调用无状态，不保留历史上下文，适合单次任务。</template>
            </el-alert>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- Skills Binding Dialog -->
    <el-dialog v-model="showSkillsDialog" :title="`${currentAgentName} - Skills管理`" width="650px">
      <div style="margin-bottom: 16px; display: flex; gap: 8px;">
        <el-select v-model="skillToAdd" placeholder="选择要绑定的Skill" filterable style="flex: 1;">
          <el-option v-for="s in availableSkills" :key="s.id" :label="`${s.name} (v${s.version})`" :value="s.id" />
        </el-select>
        <el-button type="primary" @click="handleBindSkill" :disabled="!skillToAdd">绑定</el-button>
      </div>
      <el-table :data="agentSkills" v-loading="skillsLoading" stripe>
        <el-table-column prop="skill_name" label="Skill名称" min-width="150" />
        <el-table-column prop="skill_version" label="版本" width="100" />
        <el-table-column prop="skill_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.skill_status === 'installed' ? 'success' : 'info'" size="small">
              {{ row.skill_status === 'installed' ? '已安装' : '可用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleUnbindSkill(row)">解绑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="agentSkills.length === 0 && !skillsLoading" description="暂无绑定的Skills" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { agentApi, instanceApi, modelApi, skillApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
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

const searchForm = reactive({ instance_id: '', name: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  name: '', instance_id: null, role: '', model_config_id: null,
  system_prompt: '', description: '',
  // Memory config
  memory_type: 'buffer', max_history_messages: 20, max_token_limit: 4000,
  summary_model_id: null, memory_persistence: 1, auto_cleanup_days: 0,
})

const rules = {
  name: [{ required: true, message: '请输入Agent名称', trigger: 'blur' }],
  instance_id: [{ required: true, message: '请选择所属实例', trigger: 'change' }],
}

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
const statusLabel = (s) => ({ running: '运行中', stopped: '已停止', error: '异常' }[s] || s)
const memoryTypeLabel = (t) => ({
  buffer: '缓冲', summary: '摘要', buffer_summary: '混合', none: '无记忆'
}[t] || t)

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
  await ElMessageBox.confirm(`复制 "${row.name}"？`, '复制Agent')
  await agentApi.copy(row.id, {})
  ElMessage.success('复制成功')
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
    ElMessage.success('绑定成功')
    skillToAdd.value = null
    await loadAgentSkills()
    loadData() // refresh skills_count in table
  } catch (e) { console.error(e) }
}

async function handleUnbindSkill(row) {
  await ElMessageBox.confirm(`确定解绑 "${row.skill_name}" 吗？`, '提示', { type: 'warning' })
  await agentApi.unbindSkill(currentAgentId.value, row.skill_id)
  ElMessage.success('解绑成功')
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

onMounted(() => { loadData(); loadRefs() })
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
