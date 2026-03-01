<template>
  <div class="page-container">
    <div class="page-header">
      <h2>Skills管理</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>新增Skill
      </el-button>
    </div>

    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="Skill名称">
          <el-input v-model="searchForm.name" placeholder="搜索" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="已安装" value="installed" />
            <el-option label="未安装" value="available" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Skills Grid -->
    <el-row :gutter="16">
      <el-col :span="8" v-for="skill in tableData" :key="skill.id">
        <el-card shadow="hover" class="skill-card">
          <div class="skill-header">
            <span class="skill-name">{{ skill.name }}</span>
            <el-tag :type="skill.status === 'installed' ? 'success' : 'info'" size="small">
              {{ skill.status === 'installed' ? '已安装' : '可用' }}
            </el-tag>
          </div>
          <div class="skill-version">v{{ skill.version }}</div>
          <p class="skill-desc">{{ skill.description || '暂无描述' }}</p>
          <div class="skill-actions">
            <el-button v-if="skill.status !== 'installed'" type="primary" size="small" @click="handleInstall(skill)">安装</el-button>
            <el-button v-else type="warning" size="small" @click="handleUninstall(skill)">卸载</el-button>
            <el-button size="small" @click="handleEdit(skill)">配置</el-button>
            <el-button size="small" type="danger" @click="handleDelete(skill)">删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="!loading && tableData.length === 0" description="暂无Skills" />

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showDialog" :title="editingId ? '编辑Skill' : '新增Skill'" width="550px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="Skill名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="版本" prop="version">
          <el-input v-model="form.version" placeholder="1.0.0" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="配置参数">
          <el-input v-model="form.config_json" type="textarea" :rows="4" placeholder='{"key": "value"}' />
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
import { skillApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const tableData = ref([])
const searchForm = reactive({ name: '', status: '' })

const form = reactive({ name: '', version: '1.0.0', description: '', config_json: '' })
const rules = { name: [{ required: true, message: '请输入Skill名称', trigger: 'blur' }] }

async function loadData() {
  loading.value = true
  try {
    const res = await skillApi.list(searchForm)
    tableData.value = res.data || []
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function handleEdit(row) {
  editingId.value = row.id
  Object.assign(form, { name: row.name, version: row.version, description: row.description, config_json: row.config_json || '' })
  showDialog.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editingId.value) {
      await skillApi.update(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await skillApi.create(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadData()
  } catch (e) { console.error(e) }
  finally { submitting.value = false }
}

async function handleInstall(skill) { await skillApi.install(skill.id); ElMessage.success('安装成功'); loadData() }
async function handleUninstall(skill) { await skillApi.uninstall(skill.id); ElMessage.success('卸载成功'); loadData() }
async function handleDelete(skill) {
  await ElMessageBox.confirm(`确定删除 "${skill.name}" 吗？`, '提示', { type: 'warning' })
  await skillApi.delete(skill.id); ElMessage.success('删除成功'); loadData()
}
function resetForm() { editingId.value = null; Object.assign(form, { name: '', version: '1.0.0', description: '', config_json: '' }) }

onMounted(() => loadData())
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h2 { margin: 0; color: #303133; }
.search-card { margin-bottom: 0; }
.skill-card { margin-bottom: 16px; }
.skill-header { display: flex; justify-content: space-between; align-items: center; }
.skill-name { font-size: 16px; font-weight: bold; color: #303133; }
.skill-version { color: #909399; font-size: 12px; margin-top: 4px; }
.skill-desc { color: #606266; font-size: 14px; margin: 10px 0; min-height: 40px; }
.skill-actions { display: flex; gap: 8px; }
</style>
