<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="系统信息" name="info">
        <el-card>
          <el-descriptions title="系统信息" :column="2" border>
            <el-descriptions-item label="应用名称">{{ systemInfo.app_name }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ systemInfo.version }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="用户管理" name="users">
        <el-card>
          <el-empty description="用户管理功能开发中" />
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="操作日志" name="logs">
        <el-card>
          <el-empty description="操作日志功能开发中" />
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="备份恢复" name="backup">
        <el-card>
          <el-empty description="备份恢复功能开发中" />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api'

const activeTab = ref('info')
const systemInfo = ref({ app_name: '', version: '' })

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
</style>
