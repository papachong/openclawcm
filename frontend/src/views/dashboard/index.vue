<template>
  <div class="dashboard">
    <h2>仪表盘</h2>
    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="28"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Outputs -->
    <el-card class="section-card">
      <template #header>
        <span>最近输出动态</span>
      </template>
      <el-empty description="暂无数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { dashboardApi } from '@/api'
import { Monitor, Cpu, UserFilled, Document } from '@element-plus/icons-vue'

const stats = ref([
  { label: '实例数量', value: 0, icon: 'Monitor', color: '#409EFF' },
  { label: 'Agent数量', value: 0, icon: 'UserFilled', color: '#67C23A' },
  { label: '活跃Agent', value: 0, icon: 'Cpu', color: '#E6A23C' },
  { label: '输出总数', value: 0, icon: 'Document', color: '#F56C6C' },
])

onMounted(async () => {
  try {
    const res = await dashboardApi.getOverview()
    if (res.data) {
      stats.value[0].value = res.data.instance_count
      stats.value[1].value = res.data.agent_count
      stats.value[2].value = res.data.active_agent_count
      stats.value[3].value = res.data.output_count
    }
  } catch (e) {
    console.error('Failed to load dashboard data', e)
  }
})
</script>

<style scoped>
.dashboard h2 {
  margin-bottom: 20px;
  color: #303133;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.section-card {
  margin-top: 20px;
}
</style>
