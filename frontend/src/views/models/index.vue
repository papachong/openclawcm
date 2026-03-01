<template>
  <div class="page-container">
    <div class="page-header">
      <h2>模型管理</h2>
      <div>
        <el-button @click="activeTab = 'providers'">供应商管理</el-button>
        <el-button type="primary" @click="showDialog = true">
          <el-icon><Plus /></el-icon>新增模型配置
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="model-tabs">
      <!-- 全局模型配置 -->
      <el-tab-pane label="模型配置" name="configs">
        <el-card>
          <el-table :data="tableData" v-loading="loading" stripe>
            <el-table-column prop="name" label="配置名称" min-width="150" />
            <el-table-column prop="provider_name" label="供应商" width="120" />
            <el-table-column prop="model_name" label="模型" width="180" />
            <el-table-column prop="scope" label="作用域" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.scope === 'global'" type="primary">全局</el-tag>
                <el-tag v-else-if="row.scope === 'instance'" type="success">实例级</el-tag>
                <el-tag v-else type="warning">Agent级</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="temperature" label="Temperature" width="120" />
            <el-table-column prop="max_tokens" label="Max Tokens" width="120" />
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 供应商管理 -->
      <el-tab-pane label="模型供应商" name="providers">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>模型供应商</span>
              <el-button type="primary" size="small" @click="showProviderDialog = true">新增供应商</el-button>
            </div>
          </template>
          <el-table :data="providerData" stripe>
            <el-table-column prop="name" label="供应商名称" width="150" />
            <el-table-column prop="api_type" label="API类型" width="120" />
            <el-table-column prop="base_url" label="API地址" min-width="250" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                  {{ row.status === 'active' ? '正常' : '未知' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button size="small" @click="handleEditProvider(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDeleteProvider(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 参数模板 -->
      <el-tab-pane label="参数模板" name="templates">
        <el-card>
          <el-empty description="暂无参数模板" />
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- Create/Edit Model Config Dialog -->
    <el-dialog v-model="showDialog" :title="editingId ? '编辑模型配置' : '新增模型配置'" width="600px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" placeholder="如: GPT-4 默认配置" />
        </el-form-item>
        <el-form-item label="供应商" prop="provider_id">
          <el-select v-model="form.provider_id" placeholder="选择供应商">
            <el-option v-for="p in providerData" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="form.model_name" placeholder="如: gpt-4, claude-3-opus" />
        </el-form-item>
        <el-form-item label="作用域" prop="scope">
          <el-radio-group v-model="form.scope">
            <el-radio value="global">全局</el-radio>
            <el-radio value="instance">实例级</el-radio>
            <el-radio value="agent">Agent级</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Temperature" prop="temperature">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>
        <el-form-item label="Max Tokens" prop="max_tokens">
          <el-input-number v-model="form.max_tokens" :min="1" :max="128000" />
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

    <!-- Provider Dialog -->
    <el-dialog v-model="showProviderDialog" :title="editingProviderId ? '编辑供应商' : '新增供应商'" width="500px" @close="resetProviderForm">
      <el-form :model="providerForm" label-width="100px">
        <el-form-item label="供应商名称">
          <el-input v-model="providerForm.name" placeholder="如: OpenAI" />
        </el-form-item>
        <el-form-item label="API类型">
          <el-select v-model="providerForm.api_type">
            <el-option label="OpenAI Compatible" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="API地址">
          <el-input v-model="providerForm.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="providerForm.api_key" show-password placeholder="sk-..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProviderDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitProvider">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { modelApi } from '@/api'

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

const rules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
}

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
      ElMessage.success('更新成功')
    } else {
      await modelApi.create(form)
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
  await ElMessageBox.confirm(`确定删除 "${row.name}" 吗？`, '提示', { type: 'warning' })
  await modelApi.delete(row.id)
  ElMessage.success('删除成功')
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
  await ElMessageBox.confirm(`确定删除供应商 "${row.name}" 吗？`, '提示', { type: 'warning' })
  await modelApi.deleteProvider(row.id)
  ElMessage.success('删除成功')
  loadProviders()
}

async function handleSubmitProvider() {
  if (editingProviderId.value) {
    await modelApi.updateProvider(editingProviderId.value, providerForm)
    ElMessage.success('供应商更新成功')
  } else {
    await modelApi.createProvider(providerForm)
    ElMessage.success('供应商添加成功')
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
