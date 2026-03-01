<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ $t('collaborations.title') }}</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>{{ $t('collaborations.addFlow') }}
      </el-button>
    </div>

    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" :label="$t('collaborations.flowName')" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="openEditor(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="type" :label="$t('collaborations.collabType')" width="120">
          <template #default="{ row }">
            <el-tag>{{ flowTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="agent_count" :label="$t('collaborations.agentCount')" width="90" />
        <el-table-column :label="$t('collaborations.nodesEdges')" width="100">
          <template #default="{ row }">
            {{ row.node_count || 0 }} / {{ row.edge_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="$t('common.description')" min-width="180" show-overflow-tooltip />
        <el-table-column :label="$t('common.operation')" width="320" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEditor(row)">{{ $t('collaborations.editor') }}</el-button>
            <el-button size="small" @click="handleEdit(row)">{{ $t('collaborations.properties') }}</el-button>
            <el-button v-if="row.status !== 'running'" size="small" type="success" @click="handleStart(row)">{{ $t('collaborations.start') }}</el-button>
            <el-button v-else size="small" type="warning" @click="handleStop(row)">{{ $t('collaborations.stop') }}</el-button>
            <el-button size="small" @click="handleSaveTemplate(row)">{{ $t('collaborations.template') }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && tableData.length === 0" :description="$t('collaborations.noCollabConfig')" />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showDialog" :title="editingId ? $t('collaborations.editFlow') : $t('collaborations.addFlow')" width="700px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item :label="$t('collaborations.flowName')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="$t('collaborations.collabType')" prop="type">
          <el-select v-model="form.type">
            <el-option :label="$t('collaborations.typeChain')" value="chain" />
            <el-option :label="$t('collaborations.typeParallel')" value="parallel" />
            <el-option :label="$t('collaborations.typeConditional')" value="conditional" />
            <el-option :label="$t('collaborations.typeCustom')" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('collaborations.executionMode')">
          <el-select v-model="form.execution_mode">
            <el-option :label="$t('collaborations.modeSequential')" value="sequential" />
            <el-option :label="$t('collaborations.modeParallel')" value="parallel" />
            <el-option :label="$t('collaborations.modeConditional')" value="conditional" />
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { collaborationApi } from '@/api'

const { t } = useI18n()
const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const tableData = ref([])

const form = reactive({ name: '', type: 'chain', execution_mode: 'sequential', description: '' })
const rules = computed(() => ({
  name: [{ required: true, message: t('collaborations.pleaseInputName'), trigger: 'blur' }],
}))

const flowTypeLabel = (ft) => ({
  chain: t('collaborations.typeChainShort'), parallel: t('collaborations.typeParallelShort'),
  conditional: t('collaborations.typeConditionalShort'), custom: t('collaborations.typeCustomShort'),
}[ft] || ft)
const statusType = (s) => ({ running: 'success', inactive: 'info', error: 'danger', active: 'success' }[s] || 'info')
const statusLabel = (s) => ({
  running: t('collaborations.running'), inactive: t('collaborations.stopped'),
  error: t('collaborations.errorStatus'), active: t('collaborations.running'),
}[s] || s)

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
      ElMessage.success(t('common.success.update'))
    } else {
      const res = await collaborationApi.create(form)
      ElMessage.success(t('common.success.create'))
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
    ElMessage.success(t('collaborations.started'))
  } catch (e) { console.error(e) }
}

async function handleStop(row) {
  try {
    await collaborationApi.stop(row.id)
    row.status = 'inactive'
    ElMessage.success(t('collaborations.stoppedMsg'))
  } catch (e) { console.error(e) }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('collaborations.confirmDelete', { name: row.name }), t('common.tip'), { type: 'warning' })
  await collaborationApi.delete(row.id)
  ElMessage.success(t('common.success.delete'))
  loadData()
}

async function handleSaveTemplate(row) {
  await collaborationApi.saveAsTemplate(row.id)
  ElMessage.success(t('collaborations.savedAsTemplate'))
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
