<template>
  <div class="page-container">
    <div class="page-header">
      <h2>输出管理</h2>
      <div class="header-actions" v-if="selectedIds.length > 0">
        <el-tag type="info">已选 {{ selectedIds.length }} 项</el-tag>
        <el-button size="small" type="primary" @click="handleBatchExport">批量导出</el-button>
        <el-button size="small" type="danger" @click="handleBatchDelete">批量删除</el-button>
      </div>
    </div>

    <!-- Search & Filter -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="实例">
          <el-select v-model="searchForm.instance_id" placeholder="全部实例" clearable>
            <el-option v-for="inst in instances" :key="inst.id" :label="inst.name" :value="inst.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Agent">
          <el-select v-model="searchForm.agent_id" placeholder="全部Agent" clearable>
            <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="输出类型">
          <el-select v-model="searchForm.output_type" placeholder="全部类型" clearable>
            <el-option v-for="t in outputTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="搜索内容..." clearable style="width: 250px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Output Type Tabs -->
    <el-card>
      <el-tabs v-model="currentType" @tab-change="loadData">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane v-for="t in outputTypes" :key="t.value" :label="t.label" :name="t.value" />
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
              <span>实例: {{ item.instance_name }}</span>
              <span>Agent: {{ item.agent_name }}</span>
              <span v-if="item.token_usage">Token: {{ item.token_usage }}</span>
              <span v-if="item.tags?.length">
                <el-tag v-for="tag in item.tags" :key="tag" size="small" class="output-tag">{{ tag }}</el-tag>
              </span>
            </div>
          </div>
        </div>
        <el-empty v-if="!loading && tableData.length === 0" description="暂无输出数据" />
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
            <el-descriptions-item label="类型">
              <el-tag :type="typeTagColor(detailItem.output_type)">{{ typeLabel(detailItem.output_type) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">{{ detailItem.status }}</el-descriptions-item>
            <el-descriptions-item label="实例">{{ detailItem.instance_name }}</el-descriptions-item>
            <el-descriptions-item label="Agent">{{ detailItem.agent_name }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ detailItem.created_at }}</el-descriptions-item>
            <el-descriptions-item label="Token用量">{{ detailItem.token_usage || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="detail-content">
          <h4>内容</h4>
          <!-- Code type with syntax highlighting -->
          <div v-if="detailItem.output_type === 'CODE'" class="code-block" v-html="highlightedCode" />
          <!-- Document / Markdown rendering -->
          <div v-else-if="detailItem.output_type === 'DOCUMENT'" class="markdown-body" v-html="renderedMarkdown" />
          <!-- Other types -->
          <pre v-else class="content-block">{{ detailItem.content || detailItem.raw_content }}</pre>
        </div>

        <div class="detail-actions">
          <el-button @click="handleToggleFavorite(detailItem)">
            {{ detailItem.is_favorite ? '取消收藏' : '收藏' }}
          </el-button>
          <el-button type="primary" @click="handleExport(detailItem, 'markdown')">导出Markdown</el-button>
          <el-button @click="handleExport(detailItem, 'json')">导出JSON</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { StarFilled } from '@element-plus/icons-vue'
import { outputApi, instanceApi, agentApi } from '@/api'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import { marked } from 'marked'

const loading = ref(false)
const tableData = ref([])
const detailVisible = ref(false)
const detailItem = ref(null)
const currentType = ref('all')
const instances = ref([])
const agents = ref([])

const searchForm = reactive({ instance_id: '', agent_id: '', output_type: '', keyword: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const outputTypes = [
  { value: 'CODE', label: '代码', color: 'primary' },
  { value: 'DOCUMENT', label: '文档', color: 'success' },
  { value: 'DATA', label: '数据', color: 'warning' },
  { value: 'CONVERSATION', label: '对话', color: 'info' },
  { value: 'FILE', label: '文件', color: '' },
  { value: 'COMMAND', label: '命令', color: 'danger' },
  { value: 'STRUCTURED', label: '结构化', color: 'primary' },
]

const typeLabel = (t) => outputTypes.find(o => o.value === t)?.label || t
const typeTagColor = (t) => outputTypes.find(o => o.value === t)?.color || 'info'

const selectedIds = computed(() => tableData.value.filter(i => i._selected).map(i => i.id))

// Syntax highlighting for code
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

// Markdown rendering
const renderedMarkdown = computed(() => {
  if (!detailItem.value) return ''
  const content = detailItem.value.content || detailItem.value.raw_content || ''
  try {
    return marked(content)
  } catch (e) {
    return `<p>${content}</p>`
  }
})

function onSelectionChange() {
  // Trigger reactivity on selectedIds
}

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm,
      output_type: currentType.value === 'all' ? searchForm.output_type : currentType.value,
    }
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
    ElMessage.success(item.is_favorite ? '已收藏' : '已取消收藏')
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
    ElMessage.success('导出成功')
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
  await ElMessageBox.confirm(`确定删除选中的 ${ids.length} 条输出吗？`, '批量删除', { type: 'warning' })
  try {
    const res = await outputApi.batchDelete(ids)
    ElMessage.success(`成功删除 ${res?.deleted || ids.length} 条`)
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
    ElMessage.success(`导出 ${items.length} 条`)
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
