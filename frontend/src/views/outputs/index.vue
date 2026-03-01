<template>
  <div class="page-container">
    <div class="page-header">
      <h2>输出管理</h2>
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
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="searchForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
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

      <!-- Output List -->
      <div class="output-list" v-loading="loading">
        <div v-for="item in tableData" :key="item.id" class="output-item" @click="showDetail(item)">
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
            <span v-if="item.tags?.length">
              <el-tag v-for="tag in item.tags" :key="tag" size="small" class="output-tag">{{ tag }}</el-tag>
            </span>
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
          <!-- Code type -->
          <pre v-if="detailItem.output_type === 'CODE'" class="code-block"><code>{{ detailItem.content }}</code></pre>
          <!-- Document/Conversation -->
          <div v-else-if="detailItem.output_type === 'DOCUMENT'" class="markdown-content" v-html="detailItem.content" />
          <!-- Other types -->
          <pre v-else class="content-block">{{ detailItem.content }}</pre>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { StarFilled } from '@element-plus/icons-vue'
import { outputApi, instanceApi, agentApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const detailVisible = ref(false)
const detailItem = ref(null)
const currentType = ref('all')
const instances = ref([])
const agents = ref([])

const searchForm = reactive({ instance_id: '', agent_id: '', output_type: '', keyword: '', date_range: null })
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

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm,
      output_type: currentType.value === 'all' ? searchForm.output_type : currentType.value,
    }
    if (params.date_range) {
      params.start_date = params.date_range[0]
      params.end_date = params.date_range[1]
    }
    delete params.date_range
    const res = await outputApi.list(params)
    tableData.value = res.data || []
    pagination.total = res.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function resetSearch() {
  Object.assign(searchForm, { instance_id: '', agent_id: '', output_type: '', keyword: '', date_range: null })
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
    await outputApi.export(item.id, format)
    ElMessage.success('导出成功')
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
.search-card { margin-bottom: 0; }
.output-list { min-height: 200px; }
.output-item {
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background 0.2s;
}
.output-item:hover { background: #f5f7fa; }
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
.code-block { background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px; overflow-x: auto; }
.content-block { background: #f5f7fa; padding: 16px; border-radius: 8px; white-space: pre-wrap; }
.detail-actions { display: flex; gap: 8px; margin-top: 20px; }
</style>
