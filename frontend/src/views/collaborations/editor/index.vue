<template>
  <div class="flow-editor-page">
    <!-- Top Bar -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <el-button @click="goBack" :icon="ArrowLeft" circle />
        <span class="flow-name">{{ flowData.name || '加载中...' }}</span>
        <el-tag :type="statusTagType" size="small">{{ statusLabel }}</el-tag>
      </div>
      <div class="toolbar-right">
        <el-button @click="handleSaveLayout" :loading="saving" type="primary" :icon="FolderChecked">保存布局</el-button>
        <el-button v-if="flowData.status !== 'running'" @click="handleStart" type="success" :icon="VideoPlay">启动</el-button>
        <el-button v-else @click="handleStop" type="danger" :icon="VideoPause">停止</el-button>
      </div>
    </div>

    <div class="editor-body">
      <!-- Left Panel: node palette -->
      <div class="node-palette">
        <div class="palette-title">节点面板</div>
        <div
          v-for="nt in nodeTypes"
          :key="nt.type"
          class="palette-item"
          draggable="true"
          @dragstart="onDragStart($event, nt)"
        >
          <el-icon :color="nt.color"><component :is="nt.icon" /></el-icon>
          <span>{{ nt.label }}</span>
        </div>

        <el-divider>可用Agent</el-divider>
        <div
          v-for="agent in allAgents"
          :key="agent.id"
          class="palette-item palette-agent"
          draggable="true"
          @dragstart="onDragStartAgent($event, agent)"
        >
          <el-icon color="#409EFF"><UserFilled /></el-icon>
          <span>{{ agent.name }}</span>
        </div>
      </div>

      <!-- Vue Flow Canvas -->
      <div class="flow-canvas" ref="canvasRef" @drop="onDrop" @dragover.prevent>
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :node-types="customNodeTypes"
          :default-viewport="{ zoom: flowData.viewport_zoom || 1, x: flowData.viewport_x || 0, y: flowData.viewport_y || 0 }"
          :connection-mode="ConnectionMode.Loose"
          :snap-to-grid="true"
          :snap-grid="[15, 15]"
          fit-view-on-init
          @connect="onConnect"
          @node-click="onNodeClick"
          @edge-click="onEdgeClick"
        >
          <Background />
          <Controls />
          <MiniMap />
        </VueFlow>
      </div>

      <!-- Right Panel: selected node/edge properties -->
      <div class="props-panel" v-if="selectedNode || selectedEdge">
        <!-- Node Properties -->
        <template v-if="selectedNode">
          <div class="panel-title">节点属性</div>
          <el-form label-width="80px" size="small">
            <el-form-item label="类型">
              <el-tag size="small">{{ nodeTypeLabel(selectedNode.data.node_type) }}</el-tag>
            </el-form-item>
            <el-form-item label="标签">
              <el-input v-model="selectedNode.data.label" @change="onNodePropChange" />
            </el-form-item>
            <el-form-item label="Agent" v-if="selectedNode.data.node_type === 'agent'">
              <el-select v-model="selectedNode.data.agent_id" @change="onAgentChange" clearable placeholder="选择Agent">
                <el-option v-for="a in allAgents" :key="a.id" :label="a.name" :value="a.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="配置JSON" v-if="selectedNode.data.node_type === 'condition'">
              <el-input v-model="selectedNode.data.config_json" type="textarea" :rows="4" @change="onNodePropChange" placeholder='{"expr": "output.score > 0.8"}' />
            </el-form-item>
            <el-form-item>
              <el-button type="danger" size="small" @click="deleteSelectedNode">删除节点</el-button>
            </el-form-item>
          </el-form>
        </template>

        <!-- Edge Properties -->
        <template v-if="selectedEdge && !selectedNode">
          <div class="panel-title">连线属性</div>
          <el-form label-width="80px" size="small">
            <el-form-item label="标签">
              <el-input v-model="selectedEdge.data.label" @change="onEdgePropChange" />
            </el-form-item>
            <el-form-item label="类型">
              <el-select v-model="selectedEdge.data.edge_type" @change="onEdgePropChange">
                <el-option label="默认" value="default" />
                <el-option label="成功" value="success" />
                <el-option label="失败" value="failure" />
                <el-option label="条件" value="conditional" />
              </el-select>
            </el-form-item>
            <el-form-item label="条件JSON" v-if="selectedEdge.data.edge_type === 'conditional'">
              <el-input v-model="selectedEdge.data.condition_json" type="textarea" :rows="3" @change="onEdgePropChange" />
            </el-form-item>
            <el-form-item>
              <el-button type="danger" size="small" @click="deleteSelectedEdge">删除连线</el-button>
            </el-form-item>
          </el-form>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, markRaw, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, VideoPlay, VideoPause, FolderChecked,
  UserFilled, CircleClose, Switch, Connection,
} from '@element-plus/icons-vue'
import { VueFlow, useVueFlow, ConnectionMode } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

import AgentNode from './AgentNode.vue'
import { collaborationApi, agentApi } from '@/api'

const route = useRoute()
const router = useRouter()
const collabId = computed(() => Number(route.params.id))
const canvasRef = ref(null)
const saving = ref(false)

const flowData = ref({ name: '', status: 'inactive', viewport_zoom: 1, viewport_x: 0, viewport_y: 0 })
const nodes = ref([])
const edges = ref([])
const allAgents = ref([])

const selectedNode = ref(null)
const selectedEdge = ref(null)

const customNodeTypes = { agent: markRaw(AgentNode) }

const { addNodes, addEdges, removeNodes, removeEdges, project } = useVueFlow()

const nodeTypes = [
  { type: 'start', label: '开始节点', icon: 'VideoPlay', color: '#67C23A' },
  { type: 'end', label: '结束节点', icon: 'CircleClose', color: '#F56C6C' },
  { type: 'condition', label: '条件分支', icon: 'Switch', color: '#E6A23C' },
  { type: 'parallel_gateway', label: '并行网关', icon: 'Connection', color: '#409EFF' },
]

const statusTagType = computed(() => {
  const m = { running: 'success', inactive: 'info', error: 'danger', active: 'success' }
  return m[flowData.value.status] || 'info'
})
const statusLabel = computed(() => {
  const m = { running: '运行中', inactive: '已停止', error: '错误', active: '运行中' }
  return m[flowData.value.status] || flowData.value.status
})

function nodeTypeLabel(t) {
  return { agent: 'Agent', start: '开始', end: '结束', condition: '条件', parallel_gateway: '并行网关' }[t] || t
}

function goBack() { router.push('/collaborations') }

// ==================== Load flow data ====================

async function loadFlow() {
  try {
    const res = await collaborationApi.getFlow(collabId.value)
    const flow = res
    flowData.value = flow

    nodes.value = (flow.nodes || []).map(n => ({
      id: String(n.id),
      type: 'agent',
      position: { x: n.position_x, y: n.position_y },
      data: { ...n },
    }))

    edges.value = (flow.edges || []).map(e => ({
      id: String(e.id),
      source: String(e.source_node_id),
      target: String(e.target_node_id),
      label: e.label || '',
      type: 'default',
      animated: e.edge_type === 'conditional',
      data: { ...e },
    }))
  } catch (e) {
    console.error(e)
    ElMessage.error('加载流程失败')
  }
}

async function loadAgents() {
  try {
    const res = await agentApi.list()
    allAgents.value = res.data || []
  } catch (e) { console.error(e) }
}

// ==================== Drag & Drop ====================

let dragType = null
let dragAgent = null

function onDragStart(evt, nt) {
  dragType = nt.type
  dragAgent = null
  evt.dataTransfer.effectAllowed = 'move'
}

function onDragStartAgent(evt, agent) {
  dragType = 'agent'
  dragAgent = agent
  evt.dataTransfer.effectAllowed = 'move'
}

async function onDrop(evt) {
  const bounds = canvasRef.value.getBoundingClientRect()
  const position = project({ x: evt.clientX - bounds.left, y: evt.clientY - bounds.top })

  const nodeData = {
    node_type: dragType || 'agent',
    position_x: position.x,
    position_y: position.y,
  }

  if (dragAgent) {
    nodeData.agent_id = dragAgent.id
    nodeData.label = dragAgent.name
  }

  try {
    const res = await collaborationApi.createNode(collabId.value, nodeData)
    const n = res
    const newNode = {
      id: String(n.id),
      type: 'agent',
      position: { x: n.position_x, y: n.position_y },
      data: { ...n },
    }
    addNodes([newNode])
    ElMessage.success('节点已添加')
  } catch (e) {
    console.error(e)
    ElMessage.error('添加节点失败')
  }

  dragType = null
  dragAgent = null
}

// ==================== Connections ====================

async function onConnect(params) {
  try {
    const res = await collaborationApi.createEdge(collabId.value, {
      source_node_id: Number(params.source),
      target_node_id: Number(params.target),
    })
    const e = res
    addEdges([{
      id: String(e.id),
      source: String(e.source_node_id),
      target: String(e.target_node_id),
      label: e.label || '',
      data: { ...e },
    }])
  } catch (e) {
    console.error(e)
    ElMessage.error('创建连线失败')
  }
}

// ==================== Selection ====================

function onNodeClick({ node }) {
  selectedNode.value = node
  selectedEdge.value = null
}

function onEdgeClick({ edge }) {
  selectedEdge.value = edge
  selectedNode.value = null
}

// ==================== Property changes ====================

async function onNodePropChange() {
  if (!selectedNode.value) return
  const n = selectedNode.value
  try {
    await collaborationApi.updateNode(collabId.value, Number(n.id), {
      label: n.data.label,
      config_json: n.data.config_json,
    })
  } catch (e) { console.error(e) }
}

async function onAgentChange(agentId) {
  if (!selectedNode.value) return
  const n = selectedNode.value
  const agent = allAgents.value.find(a => a.id === agentId)
  n.data.agent_id = agentId
  n.data.agent_name = agent?.name || null
  if (!n.data.label || n.data.label === 'Agent') {
    n.data.label = agent?.name || 'Agent'
  }
  try {
    await collaborationApi.updateNode(collabId.value, Number(n.id), {
      agent_id: agentId,
      label: n.data.label,
    })
  } catch (e) { console.error(e) }
}

async function onEdgePropChange() {
  if (!selectedEdge.value) return
  const e = selectedEdge.value
  try {
    await collaborationApi.updateEdge(collabId.value, Number(e.id), {
      label: e.data.label,
      edge_type: e.data.edge_type,
      condition_json: e.data.condition_json,
    })
    e.label = e.data.label
    e.animated = e.data.edge_type === 'conditional'
  } catch (e2) { console.error(e2) }
}

// ==================== Delete ====================

async function deleteSelectedNode() {
  if (!selectedNode.value) return
  const nodeId = selectedNode.value.id
  try {
    await collaborationApi.deleteNode(collabId.value, Number(nodeId))
    removeNodes([nodeId])
    // Also remove connected edges from UI
    const connEdges = edges.value.filter(e => e.source === nodeId || e.target === nodeId)
    if (connEdges.length) removeEdges(connEdges.map(e => e.id))
    selectedNode.value = null
    ElMessage.success('节点已删除')
  } catch (e) { console.error(e) }
}

async function deleteSelectedEdge() {
  if (!selectedEdge.value) return
  const edgeId = selectedEdge.value.id
  try {
    await collaborationApi.deleteEdge(collabId.value, Number(edgeId))
    removeEdges([edgeId])
    selectedEdge.value = null
    ElMessage.success('连线已删除')
  } catch (e) { console.error(e) }
}

// ==================== Save Layout ====================

async function handleSaveLayout() {
  saving.value = true
  try {
    const nodePositions = nodes.value.map(n => ({
      id: Number(n.id),
      position_x: n.position.x,
      position_y: n.position.y,
    }))
    await collaborationApi.saveLayout(collabId.value, { nodes: nodePositions })
    ElMessage.success('布局已保存')
  } catch (e) {
    console.error(e)
    ElMessage.error('保存布局失败')
  } finally { saving.value = false }
}

// ==================== Flow Control ====================

async function handleStart() {
  try {
    await collaborationApi.start(collabId.value)
    flowData.value.status = 'running'
    ElMessage.success('协作流程已启动')
  } catch (e) { console.error(e) }
}

async function handleStop() {
  try {
    await collaborationApi.stop(collabId.value)
    flowData.value.status = 'inactive'
    ElMessage.success('协作流程已停止')
  } catch (e) { console.error(e) }
}

onMounted(() => {
  loadFlow()
  loadAgents()
})
</script>

<style scoped>
.flow-editor-page { display: flex; flex-direction: column; height: calc(100vh - 100px); }

.editor-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 16px; background: #fff; border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}
.toolbar-left { display: flex; align-items: center; gap: 12px; }
.flow-name { font-size: 16px; font-weight: 600; color: #303133; }
.toolbar-right { display: flex; gap: 8px; }

.editor-body { display: flex; flex: 1; overflow: hidden; }

.node-palette {
  width: 200px; background: #fafbfc; border-right: 1px solid #ebeef5;
  padding: 12px; overflow-y: auto; flex-shrink: 0;
}
.palette-title { font-weight: 600; color: #606266; margin-bottom: 12px; font-size: 14px; }
.palette-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  background: #fff; border: 1px solid #e4e7ed; border-radius: 6px;
  margin-bottom: 8px; cursor: grab; font-size: 13px; transition: all 0.2s;
}
.palette-item:hover { border-color: #409EFF; box-shadow: 0 2px 6px rgba(64,158,255,0.15); }
.palette-agent { border-left: 3px solid #409EFF; }

.flow-canvas { flex: 1; position: relative; }

.props-panel {
  width: 260px; background: #fff; border-left: 1px solid #ebeef5;
  padding: 16px; overflow-y: auto; flex-shrink: 0;
}
.panel-title { font-weight: 600; color: #303133; margin-bottom: 16px; font-size: 14px; }
</style>
