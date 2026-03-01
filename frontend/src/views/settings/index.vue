<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <!-- ==================== 系统信息 ==================== -->
      <el-tab-pane label="系统信息" name="info">
        <el-card>
          <el-descriptions title="系统信息" :column="2" border>
            <el-descriptions-item label="应用名称">{{ systemInfo.app_name }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ systemInfo.version }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <!-- ==================== 用户管理 ==================== -->
      <el-tab-pane label="用户管理" name="users">
        <el-card>
          <div class="tab-toolbar">
            <el-button type="primary" size="small" @click="showUserDialog = true">
              <el-icon><Plus /></el-icon>新增用户
            </el-button>
          </div>
          <el-table :data="users" v-loading="usersLoading" stripe>
            <el-table-column prop="username" label="用户名" width="130" />
            <el-table-column prop="display_name" label="显示名" width="130" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">{{ row.role }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="170" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="handleEditUser(row)">编辑</el-button>
                <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="handleToggleUser(row)">
                  {{ row.is_active ? '禁用' : '启用' }}
                </el-button>
                <el-button size="small" type="danger" @click="handleDeleteUser(row)">删除</el-button>
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
          :title="editingUserId ? '编辑用户' : '新增用户'"
          width="480px"
          @close="resetUserForm"
        >
          <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="80px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="userForm.username" :disabled="!!editingUserId" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item v-if="!editingUserId" label="密码" prop="password">
              <el-input v-model="userForm.password" type="password" show-password placeholder="请输入密码" />
            </el-form-item>
            <el-form-item label="显示名" prop="display_name">
              <el-input v-model="userForm.display_name" placeholder="可选" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="userForm.email" placeholder="可选" />
            </el-form-item>
            <el-form-item label="角色" prop="role">
              <el-select v-model="userForm.role">
                <el-option label="管理员 (admin)" value="admin" />
                <el-option label="操作员 (operator)" value="operator" />
                <el-option label="只读 (viewer)" value="viewer" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showUserDialog = false">取消</el-button>
            <el-button type="primary" @click="handleUserSubmit" :loading="userSubmitting">确定</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <!-- ==================== 操作日志 ==================== -->
      <el-tab-pane label="操作日志" name="logs">
        <el-card>
          <el-form :inline="true" :model="logFilter" class="filter-form">
            <el-form-item label="操作">
              <el-select v-model="logFilter.action" placeholder="全部" clearable style="width: 120px">
                <el-option label="CREATE" value="CREATE" />
                <el-option label="UPDATE" value="UPDATE" />
                <el-option label="DELETE" value="DELETE" />
                <el-option label="LOGIN" value="LOGIN" />
              </el-select>
            </el-form-item>
            <el-form-item label="用户">
              <el-input v-model="logFilter.username" placeholder="用户名" clearable style="width: 120px" />
            </el-form-item>
            <el-form-item label="资源类型">
              <el-input v-model="logFilter.resource_type" placeholder="如 agent" clearable style="width: 120px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadLogs">查询</el-button>
              <el-button @click="resetLogFilter">重置</el-button>
            </el-form-item>
          </el-form>
          <el-table :data="logs" v-loading="logsLoading" stripe>
            <el-table-column prop="username" label="用户" width="110" />
            <el-table-column prop="action" label="操作" width="90">
              <template #default="{ row }">
                <el-tag :type="actionTagType(row.action)" size="small">{{ row.action }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="resource_type" label="资源类型" width="110" />
            <el-table-column prop="resource_id" label="资源ID" width="80" />
            <el-table-column prop="detail" label="详情" min-width="220" show-overflow-tooltip />
            <el-table-column prop="ip_address" label="IP" width="130" />
            <el-table-column prop="created_at" label="时间" width="170" />
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
      <el-tab-pane label="备份恢复" name="backup">
        <el-card>
          <el-empty description="备份恢复功能开发中" />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { systemApi, userApi } from '@/api'

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
const userRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

async function loadUsers() {
  usersLoading.value = true
  try {
    const res = await userApi.list({ page: usersPagination.page, page_size: usersPagination.pageSize })
    // Backend returns success({ items, total, page, page_size })
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
      ElMessage.success('更新成功')
    } else {
      await userApi.create(userForm)
      ElMessage.success('创建成功')
    }
    showUserDialog.value = false
    loadUsers()
  } catch (e) { console.error(e) }
  finally { userSubmitting.value = false }
}

async function handleToggleUser(row) {
  try {
    await userApi.update(row.id, { is_active: !row.is_active })
    ElMessage.success(row.is_active ? '已禁用' : '已启用')
    loadUsers()
  } catch (e) { console.error(e) }
}

async function handleDeleteUser(row) {
  await ElMessageBox.confirm(`确定删除用户 "${row.username}" 吗？`, '提示', { type: 'warning' })
  try {
    await userApi.delete(row.id)
    ElMessage.success('删除成功')
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
