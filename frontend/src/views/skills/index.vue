<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ $t('skills.title') }}</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>{{ $t('skills.addSkill') }}
      </el-button>
    </div>

    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item :label="$t('skills.skillName')">
          <el-input v-model="searchForm.name" :placeholder="$t('common.search')" clearable />
        </el-form-item>
        <el-form-item :label="$t('common.status')">
          <el-select v-model="searchForm.status" :placeholder="$t('common.all')" clearable>
            <el-option :label="$t('skills.installed')" value="installed" />
            <el-option :label="$t('skills.notInstalled')" value="available" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">{{ $t('common.query') }}</el-button>
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
              {{ skill.status === 'installed' ? $t('skills.installed') : $t('skills.available') }}
            </el-tag>
          </div>
          <div class="skill-version">v{{ skill.version }}</div>
          <p class="skill-desc">{{ skill.description || $t('skills.noDescription') }}</p>
          <div class="skill-actions">
            <el-button v-if="skill.status !== 'installed'" type="primary" size="small" @click="handleInstall(skill)">{{ $t('skills.install') }}</el-button>
            <el-button v-else type="warning" size="small" @click="handleUninstall(skill)">{{ $t('skills.uninstall') }}</el-button>
            <el-button size="small" @click="handleEdit(skill)">{{ $t('skills.configure') }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(skill)">{{ $t('common.delete') }}</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="!loading && tableData.length === 0" :description="$t('skills.noSkills')" />

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showDialog" :title="editingId ? $t('skills.editSkill') : $t('skills.addSkill')" width="550px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item :label="$t('skills.skillName')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="$t('skills.version')" prop="version">
          <el-input v-model="form.version" placeholder="1.0.0" />
        </el-form-item>
        <el-form-item :label="$t('common.description')">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="$t('skills.configParams')">
          <el-input v-model="form.config_json" type="textarea" :rows="4" placeholder='{"key": "value"}' />
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
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { skillApi } from '@/api'

const { t } = useI18n()
const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const tableData = ref([])
const searchForm = reactive({ name: '', status: '' })

const form = reactive({ name: '', version: '1.0.0', description: '', config_json: '' })
const rules = computed(() => ({
  name: [{ required: true, message: t('skills.pleaseInputName'), trigger: 'blur' }],
}))

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
      ElMessage.success(t('common.success.update'))
    } else {
      await skillApi.create(form)
      ElMessage.success(t('common.success.create'))
    }
    showDialog.value = false
    loadData()
  } catch (e) { console.error(e) }
  finally { submitting.value = false }
}

async function handleInstall(skill) { await skillApi.install(skill.id); ElMessage.success(t('skills.installSuccess')); loadData() }
async function handleUninstall(skill) { await skillApi.uninstall(skill.id); ElMessage.success(t('skills.uninstallSuccess')); loadData() }
async function handleDelete(skill) {
  await ElMessageBox.confirm(t('skills.confirmDelete', { name: skill.name }), t('common.tip'), { type: 'warning' })
  await skillApi.delete(skill.id); ElMessage.success(t('common.success.delete')); loadData()
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
