<template>
  <div class="page-container">
    <div class="page-header">
      <h2>多Agent协作配置</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>新建协作流程
      </el-button>
    </div>

    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="流程名称" min-width="150" />
        <el-table-column prop="type" label="协作类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ flowTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="agent_count" label="参与Agent数" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="success" @click="handleSaveTemplate(row)">存为模板</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && tableData.length === 0" description="暂无协作配置" />
    </el-card>

    <!-- Create Dialog -->
    <el-dialog v-model="showDialog" :title="editingId ? '编辑协作流程' : '新建协作流程'" width="700px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="流程名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="协作类型" prop="type">
          <el-select v-model="form.type">
            <el-option label="链式协作" value="chain" />
            <el-option label="并行协作" value="parallel" />
            <el-option label="条件分支" value="conditional" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="参与Agent" prop="agent_ids">
          <el-select v-model="form.agent_ids" multiple placeholder="选择参与的Agent">
            <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="消息路由规则">
          <el-input v-model="form.routing_rules" type="textarea" :rows="4" placeholder='JSON格式的路由规则' />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { collaborationApi, agentApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const tableData = ref([])
const agents = ref([])

const form = reactive({ name: '', type: 'chain', agent_ids: [], routing_rules: '', description: '' })
const rules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }

const flowTypeLabel = (t) => ({ chain: '链式', parallel: '并行', conditional: '条件分支', custom: '自定义' }[t] || t)

async function loadData() {
  loading.value = true
  try {
    const res = await collaborationApi.list()
    tableData.value = res.data || []
  } catch (e) { console.error(e) }
  finally { loading.value = false }
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
      await collaborationApi.update(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await collaborationApi.create(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadData()
  } catch (e) { console.error(e) }
  finally { submitting.value = false }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除 "${row.name}" 吗？`, '提示', { type: 'warning' })
  await collaborationApi.delete(row.id)
  ElMessage.success('删除成功')
  loadData()
}

async function handleSaveTemplate(row) {
  await collaborationApi.saveAsTemplate(row.id)
  ElMessage.success('已保存为模板')
}

function resetForm() {
  editingId.value = null
  Object.assign(form, { name: '', type: 'chain', agent_ids: [], routing_rules: '', description: '' })
}

onMounted(async () => {
  loadData()
  try { const res = await agentApi.list(); agents.value = res.data || [] } catch (e) {}
})
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h2 { margin: 0; color: #303133; }
</style>
