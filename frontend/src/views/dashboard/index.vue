<template>
  <div class="dashboard">
    <h2>{{ $t('dashboard.title') }}</h2>

    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="4" v-for="stat in stats" :key="stat.key">
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
          <template #header><span>{{ $t('dashboard.outputTrend') }}</span></template>
          <v-chart class="chart" :option="trendOption" autoresize />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>{{ $t('dashboard.agentStatus') }}</span></template>
          <v-chart class="chart" :option="agentPieOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts Row 2: Output Types + Instance Health -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card>
          <template #header><span>{{ $t('dashboard.outputTypeDistribution') }}</span></template>
          <v-chart class="chart" :option="outputBarOption" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>{{ $t('dashboard.instanceHealth') }}</span></template>
          <v-chart class="chart" :option="instancePieOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- Bottom Row: Recent Outputs + Alerts -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="14">
        <el-card>
          <template #header><span>{{ $t('dashboard.recentOutputs') }}</span></template>
          <el-table :data="recentOutputs" stripe size="small" v-if="recentOutputs.length">
            <el-table-column prop="title" :label="$t('dashboard.tableHeaders.title')" min-width="160" show-overflow-tooltip />
            <el-table-column prop="output_type" :label="$t('dashboard.tableHeaders.type')" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ row.output_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="agent_name" :label="$t('dashboard.tableHeaders.agent')" width="120" />
            <el-table-column prop="created_at" :label="$t('dashboard.tableHeaders.time')" width="170" />
          </el-table>
          <el-empty v-else :description="$t('dashboard.noOutputData')" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header><span>{{ $t('dashboard.systemAlerts') }}</span></template>
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
          <el-empty v-else :description="$t('dashboard.noAlerts')" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { dashboardApi, instanceApi } from '@/api'
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

const { t } = useI18n()

const stats = computed(() => [
  { key: 'instances', label: t('dashboard.stats.instances'), value: statsData.value[0], icon: 'Monitor', color: '#409EFF' },
  { key: 'agents', label: t('dashboard.stats.agents'), value: statsData.value[1], icon: 'UserFilled', color: '#67C23A' },
  { key: 'activeAgents', label: t('dashboard.stats.activeAgents'), value: statsData.value[2], icon: 'Cpu', color: '#E6A23C' },
  { key: 'outputs', label: t('dashboard.stats.outputs'), value: statsData.value[3], icon: 'Document', color: '#F56C6C' },
  { key: 'collaborations', label: t('dashboard.stats.collaborations'), value: statsData.value[4], icon: 'Connection', color: '#909399' },
  { key: 'skills', label: t('dashboard.stats.skills'), value: statsData.value[5], icon: 'MagicStick', color: '#9B59B6' },
])

const statsData = ref([0, 0, 0, 0, 0, 0])
const recentOutputs = ref([])
const alerts = ref([])

// Chart options
const trendOption = ref({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: [], boundaryGap: false },
  yAxis: { type: 'value', minInterval: 1 },
  series: [{
    name: t('dashboard.outputCount'), type: 'line', smooth: true, areaStyle: { opacity: 0.3 },
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
  // Auto-sync all instances first, then load dashboard data
  try { await instanceApi.syncAll() } catch (_) {}

  const [overviewRes, trendsRes, agentRes, outputTypeRes, instanceRes, recentRes, alertsRes] = await Promise.allSettled([
    dashboardApi.getOverview(),
    dashboardApi.getOutputTrends({ days: 7 }),
    dashboardApi.getAgentStats(),
    dashboardApi.getOutputTypeStats(),
    dashboardApi.getInstanceHealth(),
    dashboardApi.getRecentOutputs({ limit: 8 }),
    dashboardApi.getAlerts(),
  ])

  if (overviewRes.status === 'fulfilled' && overviewRes.value?.data) {
    const d = overviewRes.value.data
    statsData.value = [d.instance_count, d.agent_count, d.active_agent_count, d.output_count, d.collab_count, d.skill_count]
  }

  if (trendsRes.status === 'fulfilled' && trendsRes.value?.data) {
    const tData = trendsRes.value.data
    trendOption.value = {
      ...trendOption.value,
      xAxis: { ...trendOption.value.xAxis, data: tData.map(d => d.date.slice(5)) },
      series: [{ ...trendOption.value.series[0], data: tData.map(d => d.count) }],
    }
  }

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

  if (recentRes.status === 'fulfilled' && recentRes.value?.data) {
    recentOutputs.value = recentRes.value.data
  }

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
