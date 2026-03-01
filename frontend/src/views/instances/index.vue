<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ $t('instances.title') }}</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>{{ $t('instances.addInstance') }}
      </el-button>
    </div>

    <!-- Search Bar -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item :label="$t('instances.instanceName')">
          <el-input v-model="searchForm.name" :placeholder="$t('instances.searchPlaceholder')" clearable />
        </el-form-item>
        <el-form-item :label="$t('common.status')">
          <el-select v-model="searchForm.status" :placeholder="$t('common.all')" clearable>
            <el-option :label="$t('instances.online')" value="online" />
            <el-option :label="$t('instances.offline')" value="offline" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">{{ $t('common.query') }}</el-button>
          <el-button @click="resetSearch">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Data Table -->
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" :label="$t('instances.instanceName')" min-width="150" />
        <el-table-column prop="url" :label="$t('instances.connectionUrl')" min-width="200" />
        <el-table-column prop="status" :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'danger'">
              {{ row.status === 'online' ? $t('instances.online') : $t('instances.offline') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="group_name" :label="$t('instances.group')" width="120" />
        <el-table-column prop="agent_count" :label="$t('instances.agentCount')" width="100" />
        <el-table-column prop="last_heartbeat" :label="$t('instances.lastHeartbeat')" width="170">
          <template #default="{ row }">
            <span v-if="row.last_heartbeat">{{ row.last_heartbeat }}</span>
            <span v-else style="color: #909399">{{ $t('instances.noHeartbeat') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="$t('common.description')" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" :label="$t('common.createdAt')" width="180" />
        <el-table-column :label="$t('common.operation')" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" type="success" @click="handleHealthCheck(row)">{{ $t('instances.healthCheck') }}</el-button>
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
    <el-dialog
      v-model="showDialog"
      :title="editingId ? $t('instances.editInstance') : $t('instances.addInstance')"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item :label="$t('instances.instanceName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('instances.pleaseInputName')" />
        </el-form-item>
        <el-form-item :label="$t('instances.connectionUrl')" prop="url">
          <el-input v-model="form.url" placeholder="http://localhost:8080" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" :placeholder="$t('instances.optional')" show-password />
        </el-form-item>
        <el-form-item :label="$t('instances.group')" prop="group_name">
          <el-input v-model="form.group_name" :placeholder="$t('instances.groupPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('common.description')" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" :placeholder="$t('instances.descriptionPlaceholder')" />
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
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { instanceApi } from '@/api'

const { t } = useI18n()
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

const rules = computed(() => ({
  name: [{ required: true, message: t('instances.pleaseInputName'), trigger: 'blur' }],
  url: [{ required: true, message: t('instances.pleaseInputUrl'), trigger: 'blur' }],
}))

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
      ElMessage.success(t('common.success.update'))
    } else {
      await instanceApi.create(form)
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
  await ElMessageBox.confirm(t('instances.confirmDelete', { name: row.name }), t('common.tip'), { type: 'warning' })
  try {
    await instanceApi.delete(row.id)
    ElMessage.success(t('common.success.delete'))
    loadData()
  } catch (e) {
    console.error(e)
  }
}

async function handleHealthCheck(row) {
  try {
    await instanceApi.checkHealth(row.id)
    ElMessage.success(t('instances.healthCheckSuccess'))
    loadData()
  } catch (e) {
    ElMessage.error(t('instances.healthCheckFail'))
  }
}

function resetForm() {
  editingId.value = null
  Object.assign(form, { name: '', url: '', api_key: '', group_name: '', description: '' })
  formRef.value?.resetFields()
}

onMounted(() => loadData())

let pollTimer = null
onMounted(() => {
  pollTimer = setInterval(() => loadData(), 30000)
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h2 { margin: 0; color: #303133; }
.search-card { margin-bottom: 0; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
