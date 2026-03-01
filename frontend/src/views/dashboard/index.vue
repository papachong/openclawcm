<template>
  <div class="dashboard">
    <h2>仪表盘</h2>

    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="4" v-for="stat in stats" :key="stat.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts Row 1: Output Trends + Agent Status -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card>
          <template #header><span>输出趋势 (近7天)</span></template>
          <v-chart class="chart" :option="trendOption" autoresize />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>Agent 状态分布</span></template>
          <v-chart class="chart" :option="agentPieOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts Row 2: Output Types + Instance Health -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card>
          <template #header><span>输出类型分布</span></template>
          <v-chart class="chart" :option="outputBarOption" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>实例健康状态</span></template>
          <v-chart class="chart" :option="instancePieOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- Bottom Row: Recent Outputs + Alerts -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="14">
        <el-card>
          <template #header><span>最近输出动态</span></template>
          <el-table :data="recentOutputs" stripe size="small" v-if="recentOutputs.length">
            <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
            <el-table-column prop="output_type" label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ row.output_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="agent_name" label="Agent" width="120" />
            <el-table-column prop="created_at" label="时间" width="170" />
          </el-table>
          <el-empty v-else description="暂无输出数据" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header><span>系统告警</span></template>
          <div v-if="alerts.length">
            <el-alert
              v-for="(alert, idx) in alerts"
              :key="idx"
              :title="alert.message"
              :type="alert.type === 'error' ? 'error' : 'warning'"
              :closable="false"
              show-icon
              style="margin-bottom: 8px"
            />
          </div>
          <el-empty v-else description="无告警，一切正常 ✓" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { dashboardApi } from '@/api'
import { Monitor, Cpu, UserFilled, Document, Connection, MagicStick } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, DatasetComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer, LineChart, PieChart, BarChart,
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, DatasetComponent,
])

const stats = ref([
  { label: '实例', value: 0, icon: 'Monitor', color: '#409EFF' },
  { label: 'Agent', value: 0, icon: 'UserFilled', color: '#67C23A' },
  { label: '活跃Agent', value: 0, icon: 'Cpu', color: '#E6A23C' },
  { label: '输出', value: 0, icon: 'Document', color: '#F56C6C' },
  { label: '协作流程', value: 0, icon: 'Connection', color: '#909399' },
  { label: '技能', value: 0, icon: 'MagicStick', color: '#9B59B6' },
])

const recentOutputs = ref([])
const alerts = ref([])

// Chart options
const trendOption = ref({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: [], boundaryGap: false },
  yAxis: { type: 'value', minInterval: 1 },
  series: [{
    name: '输出数量', type: 'line', smooth: true, areaStyle: { opacity: 0.3 },
    data: [], itemStyle: { color: '#409EFF' },
  }],
})

const agentPieOption = ref({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: '5%', left: 'center' },
  series: [{
    type: 'pie', radius: ['40%', '65%'], avoidLabelOverlap: false,
    itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
    label: { show: false }, emphasis: { label: { show: true, fontWeight: 'bold' } },
    data: [],
  }],
})

const outputBarOption = ref({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', minInterval: 1 },
  series: [{ type: 'bar', data: [], barWidth: '50%', itemStyle: { borderRadius: [4, 4, 0, 0] } }],
})

const instancePieOption = ref({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: '5%', left: 'center' },
  series: [{
    type: 'pie', radius: ['40%', '65%'],
    itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
    label: { show: false }, emphasis: { label: { show: true, fontWeight: 'bold' } },
    data: [],
  }],
})

const statusColors = { running: '#67C23A', stopped: '#909399', error: '#F56C6C', idle: '#E6A23C' }
const instanceColors = { online: '#67C23A', offline: '#F56C6C', unknown: '#909399' }

onMounted(async () => {
  // Load all data in parallel
  const [overviewRes, trendsRes, agentRes, outputTypeRes, instanceRes, recentRes, alertsRes] = await Promise.allSettled([
    dashboardApi.getOverview(),
    dashboardApi.getOutputTrends({ days: 7 }),
    dashboardApi.getAgentStats(),
    dashboardApi.getOutputTypeStats(),
    dashboardApi.getInstanceHealth(),
    dashboardApi.getRecentOutputs({ limit: 8 }),
    dashboardApi.getAlerts(),
  ])

  // Overview stats
  if (overviewRes.status === 'fulfilled' && overviewRes.value?.data) {
    const d = overviewRes.value.data
    stats.value[0].value = d.instance_count
    stats.value[1].value = d.agent_count
    stats.value[2].value = d.active_agent_count
    stats.value[3].value = d.output_count
    stats.value[4].value = d.collab_count
    stats.value[5].value = d.skill_count
  }

  // Output trends
  if (trendsRes.status === 'fulfilled' && trendsRes.value?.data) {
    const tData = trendsRes.value.data
    trendOption.value = {
      ...trendOption.value,
      xAxis: { ...trendOption.value.xAxis, data: tData.map(d => d.date.slice(5)) },
      series: [{ ...trendOption.value.series[0], data: tData.map(d => d.count) }],
    }
  }

  // Agent stats pie
  if (agentRes.status === 'fulfilled' && agentRes.value?.data) {
    const a = agentRes.value.data
    const pieData = Object.entries(a)
      .filter(([, v]) => v > 0)
      .map(([k, v]) => ({ name: k, value: v, itemStyle: { color: statusColors[k] } }))
    if (pieData.length) {
      agentPieOption.value = {
        ...agentPieOption.value,
        series: [{ ...agentPieOption.value.series[0], data: pieData }],
      }
    }
  }

  // Output type bar
  if (outputTypeRes.status === 'fulfilled' && outputTypeRes.value?.data) {
    const oData = outputTypeRes.value.data
    const barColors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#9B59B6', '#1ABC9C']
    outputBarOption.value = {
      ...outputBarOption.value,
      xAxis: { ...outputBarOption.value.xAxis, data: oData.map(d => d.type) },
      series: [{
        ...outputBarOption.value.series[0],
        data: oData.map((d, i) => ({ value: d.count, itemStyle: { color: barColors[i % barColors.length] } })),
      }],
    }
  }

  // Instance health pie
  if (instanceRes.status === 'fulfilled' && instanceRes.value?.data) {
    const ih = instanceRes.value.data
    const ihData = Object.entries(ih)
      .filter(([, v]) => v > 0)
      .map(([k, v]) => ({ name: k, value: v, itemStyle: { color: instanceColors[k] } }))
    if (ihData.length) {
      instancePieOption.value = {
        ...instancePieOption.value,
        series: [{ ...instancePieOption.value.series[0], data: ihData }],
      }
    }
  }

  // Recent outputs
  if (recentRes.status === 'fulfilled' && recentRes.value?.data) {
    recentOutputs.value = recentRes.value.data
  }

  // Alerts
  if (alertsRes.status === 'fulfilled' && alertsRes.value?.data) {
    alerts.value = alertsRes.value.data
  }
})
</script>

<style scoped>
.dashboard h2 { margin-bottom: 20px; color: #303133; }
.stats-row { margin-bottom: 20px; }
.stat-card { cursor: pointer; }
.stat-content { display: flex; align-items: center; gap: 12px; }
.stat-icon {
  width: 48px; height: 48px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; color: #fff;
}
.stat-value { font-size: 24px; font-weight: bold; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 2px; }
.chart-row { margin-bottom: 20px; }
.chart { height: 280px; }
</style>
