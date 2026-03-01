<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ $t('settings.title') }}</h2>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <!-- ==================== 系统信息 ==================== -->
      <el-tab-pane :label="$t('settings.systemInfo')" name="info">
        <el-card>
          <el-descriptions :title="$t('settings.systemInfo')" :column="2" border>
            <el-descriptions-item :label="$t('settings.appName')">{{ systemInfo.app_name }}</el-descriptions-item>
            <el-descriptions-item :label="$t('settings.version')">{{ systemInfo.version }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <!-- ==================== 用户管理 ==================== -->
      <el-tab-pane :label="$t('settings.userManagement')" name="users">
        <el-card>
          <div class="tab-toolbar">
            <el-button type="primary" size="small" @click="showUserDialog = true">
              <el-icon><Plus /></el-icon>{{ $t('settings.addUser') }}
            </el-button>
          </div>
          <el-table :data="users" v-loading="usersLoading" stripe>
            <el-table-column prop="username" :label="$t('settings.username')" width="130" />
            <el-table-column prop="display_name" :label="$t('settings.displayName')" width="130" />
            <el-table-column prop="email" :label="$t('settings.email')" min-width="180" />
            <el-table-column prop="role" :label="$t('settings.role')" width="100">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">{{ row.role }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" :label="$t('settings.userStatus')" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? $t('settings.userEnabled') : $t('settings.userDisabled') }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" :label="$t('common.createdAt')" width="170" />
            <el-table-column :label="$t('common.operation')" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="handleEditUser(row)">{{ $t('common.edit') }}</el-button>
                <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="handleToggleUser(row)">
                  {{ row.is_active ? $t('settings.disable') : $t('settings.enable') }}
                </el-button>
                <el-button size="small" type="danger" @click="handleDeleteUser(row)">{{ $t('common.delete') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="usersPagination.page"
              v-model:page-size="usersPagination.pageSize"
              :total="usersPagination.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadUsers"
              @current-change="loadUsers"
            />
          </div>
        </el-card>

        <!-- User Create/Edit Dialog -->
        <el-dialog
          v-model="showUserDialog"
          :title="editingUserId ? $t('settings.editUser') : $t('settings.addUser')"
          width="480px"
          @close="resetUserForm"
        >
          <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="80px">
            <el-form-item :label="$t('settings.username')" prop="username">
              <el-input v-model="userForm.username" :disabled="!!editingUserId" :placeholder="$t('settings.pleaseInputUsername')" />
            </el-form-item>
            <el-form-item v-if="!editingUserId" :label="$t('settings.password')" prop="password">
              <el-input v-model="userForm.password" type="password" show-password :placeholder="$t('settings.pleaseInputPassword')" />
            </el-form-item>
            <el-form-item :label="$t('settings.displayName')" prop="display_name">
              <el-input v-model="userForm.display_name" :placeholder="$t('settings.optional')" />
            </el-form-item>
            <el-form-item :label="$t('settings.email')" prop="email">
              <el-input v-model="userForm.email" :placeholder="$t('settings.optional')" />
            </el-form-item>
            <el-form-item :label="$t('settings.role')" prop="role">
              <el-select v-model="userForm.role">
                <el-option :label="$t('settings.roleAdmin')" value="admin" />
                <el-option :label="$t('settings.roleOperator')" value="operator" />
                <el-option :label="$t('settings.roleViewer')" value="viewer" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showUserDialog = false">{{ $t('common.cancel') }}</el-button>
            <el-button type="primary" @click="handleUserSubmit" :loading="userSubmitting">{{ $t('common.confirm') }}</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <!-- ==================== 操作日志 ==================== -->
      <el-tab-pane :label="$t('settings.auditLogs')" name="logs">
        <el-card>
          <el-form :inline="true" :model="logFilter" class="filter-form">
            <el-form-item :label="$t('settings.action')">
              <el-select v-model="logFilter.action" :placeholder="$t('common.all')" clearable style="width: 120px">
                <el-option label="CREATE" value="CREATE" />
                <el-option label="UPDATE" value="UPDATE" />
                <el-option label="DELETE" value="DELETE" />
                <el-option label="LOGIN" value="LOGIN" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('settings.user')">
              <el-input v-model="logFilter.username" :placeholder="$t('settings.username')" clearable style="width: 120px" />
            </el-form-item>
            <el-form-item :label="$t('settings.resourceType')">
              <el-input v-model="logFilter.resource_type" :placeholder="$t('settings.resourceTypePlaceholder')" clearable style="width: 120px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadLogs">{{ $t('common.query') }}</el-button>
              <el-button @click="resetLogFilter">{{ $t('common.reset') }}</el-button>
            </el-form-item>
          </el-form>
          <el-table :data="logs" v-loading="logsLoading" stripe>
            <el-table-column prop="username" :label="$t('settings.user')" width="110" />
            <el-table-column prop="action" :label="$t('settings.action')" width="90">
              <template #default="{ row }">
                <el-tag :type="actionTagType(row.action)" size="small">{{ row.action }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="resource_type" :label="$t('settings.resourceType')" width="110" />
            <el-table-column prop="resource_id" :label="$t('settings.resourceId')" width="80" />
            <el-table-column prop="detail" :label="$t('settings.detail')" min-width="220" show-overflow-tooltip />
            <el-table-column prop="ip_address" :label="$t('settings.ip')" width="130" />
            <el-table-column prop="created_at" :label="$t('common.time')" width="170" />
          </el-table>
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="logsPagination.page"
              v-model:page-size="logsPagination.pageSize"
              :total="logsPagination.total"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadLogs"
              @current-change="loadLogs"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- ==================== 备份恢复 ==================== -->
      <el-tab-pane :label="$t('settings.backupRestore')" name="backup">
        <el-card>
          <el-empty :description="$t('settings.backupInDevelopment')" />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { systemApi, userApi } from '@/api'

const { t } = useI18n()
const activeTab = ref('info')
const systemInfo = ref({ app_name: '', version: '' })

// ==================== User Management ====================
const usersLoading = ref(false)
const userSubmitting = ref(false)
const showUserDialog = ref(false)
const editingUserId = ref(null)
const userFormRef = ref(null)
const users = ref([])
const usersPagination = reactive({ page: 1, pageSize: 20, total: 0 })
const userForm = reactive({ username: '', password: '', display_name: '', email: '', role: 'operator' })
const userRules = computed(() => ({
  username: [{ required: true, message: t('settings.pleaseInputUsername'), trigger: 'blur' }],
  password: [{ required: true, message: t('settings.pleaseInputPassword'), trigger: 'blur' }],
  role: [{ required: true, message: t('settings.pleaseSelectRole'), trigger: 'change' }],
}))

async function loadUsers() {
  usersLoading.value = true
  try {
    const res = await userApi.list({ page: usersPagination.page, page_size: usersPagination.pageSize })
    const d = res.data || res
    users.value = d.items || []
    usersPagination.total = d.total || 0
  } catch (e) { console.error(e) }
  finally { usersLoading.value = false }
}

function handleEditUser(row) {
  editingUserId.value = row.id
  Object.assign(userForm, {
    username: row.username,
    password: '',
    display_name: row.display_name || '',
    email: row.email || '',
    role: row.role,
  })
  showUserDialog.value = true
}

async function handleUserSubmit() {
  if (!editingUserId.value) {
    await userFormRef.value.validate()
  }
  userSubmitting.value = true
  try {
    if (editingUserId.value) {
      await userApi.update(editingUserId.value, {
        display_name: userForm.display_name,
        email: userForm.email,
        role: userForm.role,
      })
      ElMessage.success(t('common.success.update'))
    } else {
      await userApi.create(userForm)
      ElMessage.success(t('common.success.create'))
    }
    showUserDialog.value = false
    loadUsers()
  } catch (e) { console.error(e) }
  finally { userSubmitting.value = false }
}

async function handleToggleUser(row) {
  try {
    await userApi.update(row.id, { is_active: !row.is_active })
    ElMessage.success(row.is_active ? t('settings.disabledMsg') : t('settings.enabledMsg'))
    loadUsers()
  } catch (e) { console.error(e) }
}

async function handleDeleteUser(row) {
  await ElMessageBox.confirm(t('settings.confirmDeleteUser', { name: row.username }), t('common.tip'), { type: 'warning' })
  try {
    await userApi.delete(row.id)
    ElMessage.success(t('common.success.delete'))
    loadUsers()
  } catch (e) { console.error(e) }
}

function resetUserForm() {
  editingUserId.value = null
  Object.assign(userForm, { username: '', password: '', display_name: '', email: '', role: 'operator' })
  userFormRef.value?.resetFields()
}

// ==================== Audit Logs ====================
const logsLoading = ref(false)
const logs = ref([])
const logsPagination = reactive({ page: 1, pageSize: 20, total: 0 })
const logFilter = reactive({ action: '', username: '', resource_type: '' })

async function loadLogs() {
  logsLoading.value = true
  try {
    const res = await systemApi.getAuditLogs({
      page: logsPagination.page,
      page_size: logsPagination.pageSize,
      ...logFilter,
    })
    logs.value = res.data || []
    logsPagination.total = res.total || 0
  } catch (e) { console.error(e) }
  finally { logsLoading.value = false }
}

function resetLogFilter() {
  logFilter.action = ''
  logFilter.username = ''
  logFilter.resource_type = ''
  logsPagination.page = 1
  loadLogs()
}

function actionTagType(action) {
  const map = { CREATE: 'success', UPDATE: 'warning', DELETE: 'danger', LOGIN: 'info' }
  return map[action] || 'info'
}

// ==================== Tab Change ====================
function onTabChange(tab) {
  if (tab === 'users' && users.value.length === 0) loadUsers()
  if (tab === 'logs' && logs.value.length === 0) loadLogs()
}

onMounted(async () => {
  try {
    const res = await systemApi.getInfo()
    systemInfo.value = res.data || {}
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.page-header h2 { margin: 0; color: #303133; }
.tab-toolbar { margin-bottom: 12px; }
.filter-form { margin-bottom: 12px; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
