<template>
  <div :class="['agent-node', `node-${data.node_type}`]">
    <div class="node-header">
      <el-icon v-if="data.node_type === 'start'" color="#67C23A"><VideoPlay /></el-icon>
      <el-icon v-else-if="data.node_type === 'end'" color="#F56C6C"><CircleClose /></el-icon>
      <el-icon v-else-if="data.node_type === 'condition'" color="#E6A23C"><Switch /></el-icon>
      <el-icon v-else-if="data.node_type === 'parallel_gateway'" color="#409EFF"><Connection /></el-icon>
      <el-icon v-else color="#409EFF"><UserFilled /></el-icon>
      <span class="node-label">{{ data.label || 'Agent' }}</span>
    </div>
    <div class="node-sub" v-if="data.agent_name">{{ data.agent_name }}</div>
    <Handle type="target" :position="Position.Top" />
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup>
import { Handle, Position } from '@vue-flow/core'
import { UserFilled, VideoPlay, CircleClose, Switch, Connection } from '@element-plus/icons-vue'

const props = defineProps({ data: { type: Object, required: true } })
</script>

<style scoped>
.agent-node {
  background: #fff;
  border: 2px solid #409EFF;
  border-radius: 8px;
  padding: 8px 16px;
  min-width: 140px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  cursor: grab;
}
.node-start { border-color: #67C23A; }
.node-end { border-color: #F56C6C; }
.node-condition { border-color: #E6A23C; border-style: dashed; }
.node-parallel_gateway { border-color: #409EFF; border-style: dotted; }
.node-header { display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 13px; }
.node-sub { font-size: 11px; color: #909399; margin-top: 2px; }
</style>
