<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ $t('outputs.title') }}</h2>
      <div class="header-actions" v-if="selectedIds.length > 0">
        <el-tag type="info">{{ $t('outputs.selectedCount', { count: selectedIds.length }) }}</el-tag>
        <el-button size="small" type="primary" @click="handleBatchExport">{{ $t('outputs.batchExport') }}</el-button>
        <el-button size="small" type="danger" @click="handleBatchDelete">{{ $t('outputs.batchDelete') }}</el-button>
      </div>
    </div>

    <!-- Search & Filter -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item :label="$t('outputs.instance')">
          <el-select v-model="searchForm.instance_id" :placeholder="$t('outputs.allInstances')" clearable>
            <el-option v-for="inst in instances" :key="inst.id" :label="inst.name" :value="inst.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('outputs.agent')">
          <el-select v-model="searchForm.agent_id" :placeholder="$t('outputs.allAgents')" clearable>
            <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('outputs.outputType')">
          <el-select v-model="searchForm.output_type" :placeholder="$t('outputs.allTypes')" clearable>
            <el-option v-for="ot in outputTypes" :key="ot.value" :label="ot.label" :value="ot.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('outputs.keyword')">
          <el-input v-model="searchForm.keyword" :placeholder="$t('outputs.searchPlaceholder')" clearable style="width: 250px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">{{ $t('common.search') }}</el-button>
          <el-button @click="resetSearch">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Output Type Tabs -->
    <el-card>
      <el-tabs v-model="currentType" @tab-change="loadData">
        <el-tab-pane :label="$t('common.all')" name="all" />
        <el-tab-pane v-for="ot in outputTypes" :key="ot.value" :label="ot.label" :name="ot.value" />
      </el-tabs>

      <!-- Output List with Checkbox -->
      <div class="output-list" v-loading="loading">
        <div v-for="item in tableData" :key="item.id" class="output-item">
          <el-checkbox v-model="item._selected" @change="onSelectionChange" class="output-checkbox" />
          <div class="output-content" @click="showDetail(item)">
            <div class="output-item-header">
              <div class="output-item-left">
                <el-tag :type="typeTagColor(item.output_type)" size="small">{{ typeLabel(item.output_type) }}</el-tag>
                <span class="output-title">{{ item.title }}</span>
              </div>
              <div class="output-item-right">
                <el-icon v-if="item.is_favorite" color="#E6A23C"><StarFilled /></el-icon>
                <span class="output-time">{{ item.created_at }}</span>
              </div>
            </div>
            <div class="output-summary">{{ item.summary }}</div>
            <div class="output-meta">
              <span>{{ $t('outputs.instanceLabel') }} {{ item.instance_name }}</span>
              <span>{{ $t('outputs.agentLabel') }} {{ item.agent_name }}</span>
              <span v-if="item.token_usage">{{ $t('outputs.tokenLabel') }} {{ item.token_usage }}</span>
              <span v-if="item.tags?.length">
                <el-tag v-for="tag in item.tags" :key="tag" size="small" class="output-tag">{{ tag }}</el-tag>
              </span>
            </div>
          </div>
        </div>
        <el-empty v-if="!loading && tableData.length === 0" :description="$t('outputs.noOutputData')" />
      </div>

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

    <!-- Output Detail Drawer -->
    <el-drawer v-model="detailVisible" :title="detailItem?.title" size="60%">
      <div v-if="detailItem" class="output-detail">
        <div class="detail-meta">
          <el-descriptions :column="2" border>
            <el-descriptions-item :label="$t('common.type')">
              <el-tag :type="typeTagColor(detailItem.output_type)">{{ typeLabel(detailItem.output_type) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('common.status')">{{ detailItem.status }}</el-descriptions-item>
            <el-descriptions-item :label="$t('outputs.instance')">{{ detailItem.instance_name }}</el-descriptions-item>
            <el-descriptions-item :label="$t('outputs.agent')">{{ detailItem.agent_name }}</el-descriptions-item>
            <el-descriptions-item :label="$t('common.createdAt')">{{ detailItem.created_at }}</el-descriptions-item>
            <el-descriptions-item :label="$t('outputs.tokenUsage')">{{ detailItem.token_usage || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="detail-content">
          <h4>{{ $t('outputs.content') }}</h4>
          <div v-if="detailItem.output_type === 'CODE'" class="code-block" v-html="highlightedCode" />
          <div v-else-if="detailItem.output_type === 'DOCUMENT'" class="markdown-body" v-html="renderedMarkdown" />
          <pre v-else class="content-block">{{ detailItem.content || detailItem.raw_content }}</pre>
        </div>

        <div class="detail-actions">
          <el-button @click="handleToggleFavorite(detailItem)">
            {{ detailItem.is_favorite ? $t('outputs.cancelFavorite') : $t('outputs.favorite') }}
          </el-button>
          <el-button type="primary" @click="handleExport(detailItem, 'markdown')">{{ $t('outputs.exportMarkdown') }}</el-button>
          <el-button @click="handleExport(detailItem, 'json')">{{ $t('outputs.exportJSON') }}</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { StarFilled } from '@element-plus/icons-vue'
import { outputApi, instanceApi, agentApi } from '@/api'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import { marked } from 'marked'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])
const detailVisible = ref(false)
const detailItem = ref(null)
const currentType = ref('all')
const instances = ref([])
const agents = ref([])

const searchForm = reactive({ instance_id: '', agent_id: '', output_type: '', keyword: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const outputTypes = computed(() => [
  { value: 'CODE', label: t('outputs.typeCode'), color: 'primary' },
  { value: 'DOCUMENT', label: t('outputs.typeDocument'), color: 'success' },
  { value: 'DATA', label: t('outputs.typeData'), color: 'warning' },
  { value: 'CONVERSATION', label: t('outputs.typeConversation'), color: 'info' },
  { value: 'FILE', label: t('outputs.typeFile'), color: '' },
  { value: 'COMMAND', label: t('outputs.typeCommand'), color: 'danger' },
  { value: 'STRUCTURED', label: t('outputs.typeStructured'), color: 'primary' },
])

const typeLabel = (ot) => outputTypes.value.find(o => o.value === ot)?.label || ot
const typeTagColor = (ot) => outputTypes.value.find(o => o.value === ot)?.color || 'info'

const selectedIds = computed(() => tableData.value.filter(i => i._selected).map(i => i.id))

const highlightedCode = computed(() => {
  if (!detailItem.value) return ''
  const code = detailItem.value.content || detailItem.value.raw_content || ''
  const lang = detailItem.value.content_type || 'text'
  try {
    if (hljs.getLanguage(lang)) {
      return `<pre class="hljs"><code>${hljs.highlight(code, { language: lang }).value}</code></pre>`
    }
    return `<pre class="hljs"><code>${hljs.highlightAuto(code).value}</code></pre>`
  } catch (e) {
    return `<pre><code>${code}</code></pre>`
  }
})

const renderedMarkdown = computed(() => {
  if (!detailItem.value) return ''
  const content = detailItem.value.content || detailItem.value.raw_content || ''
  try { return marked(content) } catch (e) { return `<p>${content}</p>` }
})

function onSelectionChange() {}

async function loadData() {
  loading.value = true
  try {
    // Build params, filtering out empty strings to avoid 422 errors
    const params = { page: pagination.page, page_size: pagination.pageSize }
    if (searchForm.instance_id) params.instance_id = searchForm.instance_id
    if (searchForm.agent_id) params.agent_id = searchForm.agent_id
    if (searchForm.keyword) params.keyword = searchForm.keyword
    params.output_type = currentType.value === 'all' ? (searchForm.output_type || undefined) : currentType.value
    const res = await outputApi.list(params)
    tableData.value = (res.data || []).map(i => ({ ...i, _selected: false }))
    pagination.total = res.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function resetSearch() {
  Object.assign(searchForm, { instance_id: '', agent_id: '', output_type: '', keyword: '' })
  currentType.value = 'all'
  pagination.page = 1
  loadData()
}

function showDetail(item) {
  detailItem.value = item
  detailVisible.value = true
}

async function handleToggleFavorite(item) {
  try {
    await outputApi.toggleFavorite(item.id)
    item.is_favorite = !item.is_favorite
    ElMessage.success(item.is_favorite ? t('outputs.favorited') : t('outputs.unfavorited'))
  } catch (e) { console.error(e) }
}

async function handleExport(item, format) {
  try {
    const res = await outputApi.export(item.id, format)
    if (format === 'json') {
      const blob = new Blob([JSON.stringify(res, null, 2)], { type: 'application/json' })
      downloadBlob(blob, `${item.title}.json`)
    } else if (format === 'markdown' && res?.content) {
      const blob = new Blob([res.content], { type: 'text/markdown' })
      downloadBlob(blob, res.filename || `${item.title}.md`)
    }
    ElMessage.success(t('outputs.exportSuccess'))
  } catch (e) { console.error(e) }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

async function handleBatchDelete() {
  const ids = selectedIds.value
  await ElMessageBox.confirm(t('outputs.confirmBatchDelete', { count: ids.length }), t('outputs.batchDeleteTitle'), { type: 'warning' })
  try {
    const res = await outputApi.batchDelete(ids)
    ElMessage.success(t('outputs.batchDeleteSuccess', { count: res?.deleted || ids.length }))
    loadData()
  } catch (e) { console.error(e) }
}

async function handleBatchExport() {
  const ids = selectedIds.value
  try {
    const res = await outputApi.batchExport(ids)
    const items = Array.isArray(res) ? res : (res?.data || [])
    const blob = new Blob([JSON.stringify(items, null, 2)], { type: 'application/json' })
    downloadBlob(blob, `outputs-export-${Date.now()}.json`)
    ElMessage.success(t('outputs.batchExportSuccess', { count: items.length }))
  } catch (e) { console.error(e) }
}

async function loadRefs() {
  try {
    const [instRes, agentRes] = await Promise.all([instanceApi.list(), agentApi.list()])
    instances.value = instRes.data || []
    agents.value = agentRes.data || []
  } catch (e) { console.error(e) }
}

onMounted(() => { loadData(); loadRefs() })
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h2 { margin: 0; color: #303133; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.search-card { margin-bottom: 0; }
.output-list { min-height: 200px; }
.output-item {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 16px; border-bottom: 1px solid #ebeef5; transition: background 0.2s;
}
.output-item:hover { background: #f5f7fa; }
.output-checkbox { margin-top: 4px; }
.output-content { flex: 1; cursor: pointer; }
.output-item-header { display: flex; justify-content: space-between; align-items: center; }
.output-item-left { display: flex; align-items: center; gap: 8px; }
.output-title { font-weight: bold; color: #303133; }
.output-time { color: #909399; font-size: 13px; }
.output-summary { color: #606266; font-size: 14px; margin: 8px 0; line-height: 1.5; }
.output-meta { display: flex; gap: 16px; color: #909399; font-size: 13px; }
.output-tag { margin-left: 4px; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
.detail-meta { margin-bottom: 20px; }
.detail-content { margin: 20px 0; }
.code-block :deep(pre.hljs) { background: #0d1117; color: #c9d1d9; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 13px; }
.markdown-body { padding: 16px; background: #fff; border: 1px solid #ebeef5; border-radius: 8px; line-height: 1.8; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin-top: 16px; border-bottom: 1px solid #ebeef5; padding-bottom: 4px; }
.markdown-body :deep(code) { background: #f5f7fa; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.markdown-body :deep(pre code) { background: #0d1117; color: #c9d1d9; display: block; padding: 16px; border-radius: 8px; overflow-x: auto; }
.content-block { background: #f5f7fa; padding: 16px; border-radius: 8px; white-space: pre-wrap; }
.detail-actions { display: flex; gap: 8px; margin-top: 20px; }
</style>
