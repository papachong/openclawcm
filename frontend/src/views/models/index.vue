<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ $t('models.title') }}</h2>
      <div>
        <el-button @click="activeTab = 'providers'">{{ $t('models.providerManage') }}</el-button>
        <el-button type="primary" @click="showDialog = true">
          <el-icon><Plus /></el-icon>{{ $t('models.addModelConfig') }}
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="model-tabs">
      <!-- 全局模型配置 -->
      <el-tab-pane :label="$t('models.modelConfig')" name="configs">
        <el-card>
          <el-table :data="tableData" v-loading="loading" stripe>
            <el-table-column prop="name" :label="$t('models.configName')" min-width="150" />
            <el-table-column prop="provider_name" :label="$t('models.provider')" width="120" />
            <el-table-column prop="model_name" :label="$t('models.model')" width="180" />
            <el-table-column prop="scope" :label="$t('models.scope')" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.scope === 'global'" type="primary">{{ $t('models.scopeGlobal') }}</el-tag>
                <el-tag v-else-if="row.scope === 'instance'" type="success">{{ $t('models.scopeInstance') }}</el-tag>
                <el-tag v-else type="warning">{{ $t('models.scopeAgent') }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="temperature" label="Temperature" width="120" />
            <el-table-column prop="max_tokens" label="Max Tokens" width="120" />
            <el-table-column prop="description" :label="$t('common.description')" min-width="200" show-overflow-tooltip />
            <el-table-column :label="$t('common.operation')" width="160" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="handleEdit(row)">{{ $t('common.edit') }}</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 供应商管理 -->
      <el-tab-pane :label="$t('models.modelProvider')" name="providers">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ $t('models.modelProvider') }}</span>
              <el-button type="primary" size="small" @click="showProviderDialog = true">{{ $t('models.addProvider') }}</el-button>
            </div>
          </template>
          <el-table :data="providerData" stripe>
            <el-table-column prop="name" :label="$t('models.providerName')" width="150" />
            <el-table-column prop="api_type" :label="$t('models.apiType')" width="120" />
            <el-table-column prop="base_url" :label="$t('models.apiUrl')" min-width="250" />
            <el-table-column prop="status" :label="$t('common.status')" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                  {{ row.status === 'active' ? $t('models.statusActive') : $t('models.statusUnknown') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('common.operation')" width="160">
              <template #default="{ row }">
                <el-button size="small" @click="handleEditProvider(row)">{{ $t('common.edit') }}</el-button>
                <el-button size="small" type="danger" @click="handleDeleteProvider(row)">{{ $t('common.delete') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 参数模板 -->
      <el-tab-pane :label="$t('models.paramTemplates')" name="templates">
        <el-card>
          <el-empty :description="$t('models.noParamTemplates')" />
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- Create/Edit Model Config Dialog -->
    <el-dialog v-model="showDialog" :title="editingId ? $t('models.editModelConfig') : $t('models.addModelConfig')" width="600px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item :label="$t('models.configName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('models.configNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('models.provider')" prop="provider_id">
          <el-select v-model="form.provider_id" :placeholder="$t('models.selectProvider')">
            <el-option v-for="p in providerData" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('models.modelName')" prop="model_name">
          <el-input v-model="form.model_name" :placeholder="$t('models.modelNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('models.scope')" prop="scope">
          <el-radio-group v-model="form.scope">
            <el-radio value="global">{{ $t('models.scopeGlobal') }}</el-radio>
            <el-radio value="instance">{{ $t('models.scopeInstance') }}</el-radio>
            <el-radio value="agent">{{ $t('models.scopeAgent') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Temperature" prop="temperature">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>
        <el-form-item label="Max Tokens" prop="max_tokens">
          <el-input-number v-model="form.max_tokens" :min="1" :max="128000" />
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

    <!-- Provider Dialog -->
    <el-dialog v-model="showProviderDialog" :title="editingProviderId ? $t('models.editProvider') : $t('models.addProvider')" width="500px" @close="resetProviderForm">
      <el-form :model="providerForm" label-width="100px">
        <el-form-item :label="$t('models.providerName')">
          <el-input v-model="providerForm.name" :placeholder="$t('models.providerNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('models.apiType')">
          <el-select v-model="providerForm.api_type">
            <el-option label="OpenAI Compatible" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option :label="$t('models.apiTypeSelf')" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('models.apiUrl')">
          <el-input v-model="providerForm.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="providerForm.api_key" show-password placeholder="sk-..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProviderDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmitProvider">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { modelApi } from '@/api'

const { t } = useI18n()
const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const showProviderDialog = ref(false)
const editingId = ref(null)
const editingProviderId = ref(null)
const formRef = ref(null)
const activeTab = ref('configs')
const tableData = ref([])
const providerData = ref([])

const form = reactive({
  name: '', provider_id: null, model_name: '', scope: 'global',
  temperature: 0.7, max_tokens: 4096, description: '',
})

const providerForm = reactive({
  name: '', api_type: 'openai', base_url: '', api_key: '',
})

const rules = computed(() => ({
  name: [{ required: true, message: t('models.pleaseInputConfigName'), trigger: 'blur' }],
  model_name: [{ required: true, message: t('models.pleaseInputModelName'), trigger: 'blur' }],
}))

async function loadData() {
  loading.value = true
  try {
    const res = await modelApi.list()
    tableData.value = res.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadProviders() {
  try {
    const res = await modelApi.listProviders()
    providerData.value = res.data || []
  } catch (e) {
    console.error(e)
  }
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
      await modelApi.update(editingId.value, form)
      ElMessage.success(t('common.success.update'))
    } else {
      await modelApi.create(form)
      ElMessage.success(t('common.success.create'))
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
  await ElMessageBox.confirm(t('models.confirmDelete', { name: row.name }), t('common.tip'), { type: 'warning' })
  await modelApi.delete(row.id)
  ElMessage.success(t('common.success.delete'))
  loadData()
}

function handleEditProvider(row) {
  editingProviderId.value = row.id
  Object.assign(providerForm, {
    name: row.name,
    api_type: row.api_type || 'openai',
    base_url: row.base_url || '',
    api_key: row.api_key || '',
  })
  showProviderDialog.value = true
}
async function handleDeleteProvider(row) {
  await ElMessageBox.confirm(t('models.confirmDeleteProvider', { name: row.name }), t('common.tip'), { type: 'warning' })
  await modelApi.deleteProvider(row.id)
  ElMessage.success(t('common.success.delete'))
  loadProviders()
}

async function handleSubmitProvider() {
  if (editingProviderId.value) {
    await modelApi.updateProvider(editingProviderId.value, providerForm)
    ElMessage.success(t('models.providerUpdateSuccess'))
  } else {
    await modelApi.createProvider(providerForm)
    ElMessage.success(t('models.providerAddSuccess'))
  }
  showProviderDialog.value = false
  loadProviders()
}

function resetProviderForm() {
  editingProviderId.value = null
  Object.assign(providerForm, { name: '', api_type: 'openai', base_url: '', api_key: '' })
}

function resetForm() {
  editingId.value = null
  Object.assign(form, { name: '', provider_id: null, model_name: '', scope: 'global', temperature: 0.7, max_tokens: 4096, description: '' })
}

onMounted(() => { loadData(); loadProviders() })
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h2 { margin: 0; color: #303133; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.model-tabs { margin-top: -8px; }
</style>
