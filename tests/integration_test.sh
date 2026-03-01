#!/usr/bin/env bash
# OpenClawCM Integration Test Script
# Tests all API endpoints

set +e
BASE="http://localhost:8000/api/v1"
PASS=0
FAIL=0

check() {
    local desc="$1"
    local expected="$2"
    local actual="$3"
    if echo "$actual" | grep -q "$expected"; then
        echo "  ✅ $desc"
        ((PASS++))
    else
        echo "  ❌ $desc (expected: $expected)"
        echo "     got: $actual"
        ((FAIL++))
    fi
}

echo "=========================================="
echo "  OpenClawCM Integration Tests"
echo "=========================================="

# Health check
echo ""
echo "--- Health Check ---"
R=$(curl -s "http://localhost:8000/health")
check "Health endpoint" '"status":"ok"' "$R"

# Auth
echo ""
echo "--- Authentication ---"
R=$(curl -s -X POST "$BASE/auth/login" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}')
check "Login success" '"code":200' "$R"
TOKEN=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")
AUTH="-H Authorization:\ Bearer\ $TOKEN"
H="Authorization: Bearer $TOKEN"

R=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE/auth/me")
check "Get current user" '"username":"admin"' "$R"

R=$(curl -s -X POST "$BASE/auth/login" -H "Content-Type: application/json" -d '{"username":"admin","password":"wrong"}')
check "Login with wrong password" '"code":401' "$R"

# Instances
echo ""
echo "--- Instance Management ---"
R=$(curl -s -H "$H" -X POST "$BASE/instances" -H "Content-Type: application/json" -d '{"name":"test-01","url":"http://10.0.1.10:8080","api_key":"key1","group_name":"dev"}')
check "Create instance" '"code":200' "$R"
INSTANCE_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" "$BASE/instances")
check "List instances" '"total":' "$R"

R=$(curl -s -H "$H" "$BASE/instances/$INSTANCE_ID")
check "Get instance" '"name":"test-01"' "$R"

R=$(curl -s -H "$H" -X PUT "$BASE/instances/$INSTANCE_ID" -H "Content-Type: application/json" -d '{"name":"test-01-updated"}')
check "Update instance" '"name":"test-01-updated"' "$R"

# Auth required test
echo ""
echo "--- Auth Required ---"
R=$(curl -s "$BASE/instances")
check "Unauthenticated access rejected" '"detail"' "$R"

# Model Providers
echo ""
echo "--- Model Provider Management ---"
R=$(curl -s -H "$H" -X POST "$BASE/models/providers" -H "Content-Type: application/json" -d '{"name":"OpenAI","api_type":"openai","base_url":"https://api.openai.com/v1","api_key":"sk-test"}')
check "Create provider" '"code":200' "$R"
PROVIDER_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" "$BASE/models/providers")
check "List providers" '"name":"OpenAI"' "$R"

# Model Configs
echo ""
echo "--- Model Config Management ---"
R=$(curl -s -H "$H" -X POST "$BASE/models" -H "Content-Type: application/json" -d "{\"name\":\"GPT-4o\",\"provider_id\":$PROVIDER_ID,\"model_name\":\"gpt-4o\",\"scope\":\"global\",\"temperature\":0.7,\"max_tokens\":4096}")
check "Create model config" '"code":200' "$R"
MODEL_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" "$BASE/models")
check "List model configs" '"total":' "$R"

# Agents
echo ""
echo "--- Agent Management ---"
R=$(curl -s -H "$H" -X POST "$BASE/agents" -H "Content-Type: application/json" -d "{\"name\":\"Coder\",\"instance_id\":$INSTANCE_ID,\"role\":\"developer\",\"model_config_id\":$MODEL_ID,\"system_prompt\":\"You are a coding assistant\"}")
check "Create agent" '"code":200' "$R"
AGENT_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" "$BASE/agents")
check "List agents" '"total":' "$R"

R=$(curl -s -H "$H" "$BASE/agents/$AGENT_ID")
check "Get agent" '"name":"Coder"' "$R"

R=$(curl -s -H "$H" -X POST "$BASE/agents/$AGENT_ID/start")
check "Start agent" '"status":"running"' "$R"

R=$(curl -s -H "$H" -X POST "$BASE/agents/$AGENT_ID/stop")
check "Stop agent" '"status":"stopped"' "$R"

# Agent Memory Config
echo ""
echo "--- Agent Memory Config ---"
R=$(curl -s -H "$H" -X PUT "$BASE/agents/$AGENT_ID" -H "Content-Type: application/json" -d '{"memory_type":"summary","max_history_messages":50,"max_token_limit":8000,"memory_persistence":true,"auto_cleanup_days":7}')
check "Update agent memory config" '"memory_type":"summary"' "$R"

R=$(curl -s -H "$H" "$BASE/agents/$AGENT_ID")
check "Get agent memory fields" '"max_history_messages":50' "$R"

# Skills
echo ""
echo "--- Skills Management ---"
R=$(curl -s -H "$H" -X POST "$BASE/skills" -H "Content-Type: application/json" -d '{"name":"web_search","version":"1.0.0","description":"Web search skill"}')
check "Create skill" '"code":200' "$R"
SKILL_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" "$BASE/skills")
check "List skills" '"total":' "$R"

# Agent Skills Binding
echo ""
echo "--- Agent Skills Binding ---"
R=$(curl -s -H "$H" -X POST "$BASE/agents/$AGENT_ID/skills" -H "Content-Type: application/json" -d "{\"skill_id\":$SKILL_ID}")
check "Bind skill to agent" '"code":200' "$R"

R=$(curl -s -H "$H" "$BASE/agents/$AGENT_ID/skills")
check "List agent skills" '"skill_name":"web_search"' "$R"

R=$(curl -s -H "$H" -X POST "$BASE/agents/$AGENT_ID/skills" -H "Content-Type: application/json" -d "{\"skill_id\":$SKILL_ID}")
check "Duplicate skill binding rejected" '"code":400' "$R"

R=$(curl -s -H "$H" -X DELETE "$BASE/agents/$AGENT_ID/skills/$SKILL_ID")
check "Unbind skill from agent" '"code":200' "$R"

# Outputs
echo ""
echo "--- Output Management ---"
R=$(curl -s -H "$H" -X POST "$BASE/outputs" -H "Content-Type: application/json" -d "{\"instance_id\":$INSTANCE_ID,\"agent_id\":$AGENT_ID,\"output_type\":\"CODE\",\"title\":\"Hello World\",\"content\":\"print('hello')\",\"content_type\":\"python\",\"status\":\"success\"}")
check "Create output" '"code":200' "$R"
OUTPUT_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" "$BASE/outputs")
check "List outputs" '"total":' "$R"

R=$(curl -s -H "$H" "$BASE/outputs/$OUTPUT_ID")
check "Get output" '"title":"Hello World"' "$R"

R=$(curl -s -H "$H" -X POST "$BASE/outputs/$OUTPUT_ID/favorite")
check "Toggle favorite" '"is_favorite":' "$R"

R=$(curl -s -H "$H" -X POST "$BASE/outputs/$OUTPUT_ID/tags" -H "Content-Type: application/json" -d '{"tag_name":"python"}')
check "Add tag" '"code":200' "$R"

# FTS Search
R=$(curl -s -H "$H" "$BASE/outputs/search?q=Hello")
check "FTS search" '"total":' "$R"

# Output Batch Operations
echo ""
echo "--- Output Batch Operations ---"
# Create a second output for batch testing
R=$(curl -s -H "$H" -X POST "$BASE/outputs" -H "Content-Type: application/json" -d "{\"instance_id\":$INSTANCE_ID,\"agent_id\":$AGENT_ID,\"output_type\":\"DOCUMENT\",\"title\":\"Batch Test Doc\",\"content\":\"# Markdown content\",\"content_type\":\"markdown\",\"status\":\"success\"}")
check "Create second output" '"code":200' "$R"
OUTPUT_ID2=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" -X POST "$BASE/outputs/batch-export" -H "Content-Type: application/json" -d "{\"ids\":[$OUTPUT_ID,$OUTPUT_ID2]}")
check "Batch export" '"code":200' "$R"
check "Batch export count" '"title":"Hello World"' "$R"

R=$(curl -s -H "$H" -X POST "$BASE/outputs/batch-delete" -H "Content-Type: application/json" -d "{\"ids\":[$OUTPUT_ID2]}")
check "Batch delete" '"deleted":1' "$R"

R=$(curl -s -H "$H" -X POST "$BASE/outputs/batch-delete" -H "Content-Type: application/json" -d '{"ids":[]}')
check "Batch delete empty rejected" '"code":400' "$R"

# Collaborations
echo ""
echo "--- Collaboration Management ---"
R=$(curl -s -H "$H" -X POST "$BASE/collaborations" -H "Content-Type: application/json" -d '{"name":"code-review","type":"chain","agent_ids":"[1]","routing_rules":"{}"}')
check "Create collaboration" '"code":200' "$R"
COLLAB_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" "$BASE/collaborations")
check "List collaborations" '"total":' "$R"

# Collaboration Nodes CRUD
echo ""
echo "--- Collaboration Nodes CRUD ---"
R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/nodes" -H "Content-Type: application/json" -d '{"node_type":"start","label":"开始","position_x":100,"position_y":50}')
check "Create start node" '"node_type":"start"' "$R"
START_NODE_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/nodes" -H "Content-Type: application/json" -d "{\"node_type\":\"agent\",\"label\":\"Coder Agent\",\"agent_id\":$AGENT_ID,\"position_x\":100,\"position_y\":200}")
check "Create agent node" '"node_type":"agent"' "$R"
AGENT_NODE_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/nodes" -H "Content-Type: application/json" -d '{"node_type":"end","label":"结束","position_x":100,"position_y":350}')
check "Create end node" '"node_type":"end"' "$R"
END_NODE_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" "$BASE/collaborations/$COLLAB_ID/nodes")
check "List nodes" '"node_type":"start"' "$R"

R=$(curl -s -H "$H" -X PUT "$BASE/collaborations/$COLLAB_ID/nodes/$AGENT_NODE_ID" -H "Content-Type: application/json" -d '{"label":"Updated Coder"}')
check "Update node" '"label":"Updated Coder"' "$R"

# Collaboration Edges CRUD
echo ""
echo "--- Collaboration Edges CRUD ---"
R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/edges" -H "Content-Type: application/json" -d "{\"source_node_id\":$START_NODE_ID,\"target_node_id\":$AGENT_NODE_ID}")
check "Create edge start->agent" '"source_node_id":' "$R"
EDGE1_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/edges" -H "Content-Type: application/json" -d "{\"source_node_id\":$AGENT_NODE_ID,\"target_node_id\":$END_NODE_ID,\"label\":\"complete\",\"edge_type\":\"success\"}")
check "Create edge agent->end" '"edge_type":"success"' "$R"
EDGE2_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" "$BASE/collaborations/$COLLAB_ID/edges")
check "List edges" '"source_node_id":' "$R"

R=$(curl -s -H "$H" -X PUT "$BASE/collaborations/$COLLAB_ID/edges/$EDGE1_ID" -H "Content-Type: application/json" -d '{"label":"go"}')
check "Update edge" '"label":"go"' "$R"

# Edge validation: non-existent node
R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/edges" -H "Content-Type: application/json" -d '{"source_node_id":99999,"target_node_id":99998}')
check "Edge with bad node rejected" '"code":400' "$R"

# Collaboration Flow Detail
echo ""
echo "--- Collaboration Flow Detail ---"
R=$(curl -s -H "$H" "$BASE/collaborations/$COLLAB_ID/flow")
check "Get flow detail" '"nodes":' "$R"
check "Flow has edges" '"edges":' "$R"
check "Flow has 3 nodes" '"node_type":"agent"' "$R"

# Collaboration Layout Save
echo ""
echo "--- Collaboration Layout Save ---"
R=$(curl -s -H "$H" -X PUT "$BASE/collaborations/$COLLAB_ID/layout" -H "Content-Type: application/json" -d "{\"nodes\":[{\"id\":$START_NODE_ID,\"position_x\":150,\"position_y\":80},{\"id\":$AGENT_NODE_ID,\"position_x\":150,\"position_y\":250}],\"viewport_zoom\":1.5,\"viewport_x\":10,\"viewport_y\":20}")
check "Save layout" '"code":200' "$R"

# Verify layout was saved
R=$(curl -s -H "$H" "$BASE/collaborations/$COLLAB_ID")
check "Viewport zoom saved" '"viewport_zoom":1.5' "$R"

# Collaboration Start/Stop
echo ""
echo "--- Collaboration Flow Control ---"
R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/start")
check "Start collaboration" '"status":"running"' "$R"

R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/start")
check "Start already running rejected" '"code":400' "$R"

R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/stop")
check "Stop collaboration" '"status":"inactive"' "$R"

# Start without agent node - create a new empty collab
R=$(curl -s -H "$H" -X POST "$BASE/collaborations" -H "Content-Type: application/json" -d '{"name":"empty-collab","type":"chain"}')
EMPTY_COLLAB_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")
R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$EMPTY_COLLAB_ID/start")
check "Start without agent nodes rejected" '"code":400' "$R"

# Delete edge and node
R=$(curl -s -H "$H" -X DELETE "$BASE/collaborations/$COLLAB_ID/edges/$EDGE2_ID")
check "Delete edge" '"code":200' "$R"

# Delete node (should also clean connected edges)
R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/nodes" -H "Content-Type: application/json" -d '{"node_type":"condition","position_x":300,"position_y":200}')
TEMP_NODE_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")
R=$(curl -s -H "$H" -X DELETE "$BASE/collaborations/$COLLAB_ID/nodes/$TEMP_NODE_ID")
check "Delete node" '"code":200' "$R"

# Save as template
R=$(curl -s -H "$H" -X POST "$BASE/collaborations/$COLLAB_ID/save-template")
check "Save as template" '"is_template":1' "$R"

R=$(curl -s -H "$H" "$BASE/collaborations/templates")
check "List templates" '"code":200' "$R"

# Shared Memory Pools
echo ""
echo "--- Shared Memory Pool Management ---"
R=$(curl -s -H "$H" -X POST "$BASE/memory-pools" -H "Content-Type: application/json" -d "{\"name\":\"code-review-memory\",\"memory_type\":\"buffer\",\"max_history_messages\":100,\"max_token_limit\":16000,\"collaboration_id\":$COLLAB_ID,\"description\":\"Shared memory for code review\"}")
check "Create memory pool" '"code":200' "$R"
POOL_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s -H "$H" "$BASE/memory-pools")
check "List memory pools" '"total":' "$R"

R=$(curl -s -H "$H" "$BASE/memory-pools/$POOL_ID")
check "Get memory pool" '"name":"code-review-memory"' "$R"

R=$(curl -s -H "$H" -X PUT "$BASE/memory-pools/$POOL_ID" -H "Content-Type: application/json" -d '{"max_history_messages":200}')
check "Update memory pool" '"max_history_messages":200' "$R"

# Memory Pool Agent Binding
echo ""
echo "--- Memory Pool Agent Binding ---"
R=$(curl -s -H "$H" -X POST "$BASE/memory-pools/$POOL_ID/agents" -H "Content-Type: application/json" -d "{\"agent_id\":$AGENT_ID,\"permission\":\"readwrite\"}")
check "Bind agent to pool" '"code":200' "$R"

R=$(curl -s -H "$H" "$BASE/memory-pools/$POOL_ID/agents")
check "List pool agents" '"agent_id":' "$R"

R=$(curl -s -H "$H" -X POST "$BASE/memory-pools/$POOL_ID/agents" -H "Content-Type: application/json" -d "{\"agent_id\":$AGENT_ID,\"permission\":\"read\"}")
check "Duplicate pool binding rejected" '"code":400' "$R"

R=$(curl -s -H "$H" -X DELETE "$BASE/memory-pools/$POOL_ID/agents/$AGENT_ID")
check "Unbind agent from pool" '"code":200' "$R"

R=$(curl -s -H "$H" -X DELETE "$BASE/memory-pools/$POOL_ID")
check "Delete memory pool" '"code":200' "$R"

# Dashboard
echo ""
echo "--- Dashboard ---"
R=$(curl -s -H "$H" "$BASE/dashboard/overview")
check "Dashboard overview" '"instance_count":' "$R"

R=$(curl -s -H "$H" "$BASE/dashboard/recent-outputs")
check "Recent outputs" '"code":200' "$R"

R=$(curl -s -H "$H" "$BASE/dashboard/alerts")
check "Alerts" '"code":200' "$R"

# Dashboard new APIs
echo ""
echo "--- Dashboard New APIs ---"
R=$(curl -s -H "$H" "$BASE/dashboard/output-trends?days=7")
check "Output trends" '"code":200' "$R"

R=$(curl -s -H "$H" "$BASE/dashboard/agent-stats")
check "Agent stats" '"code":200' "$R"

R=$(curl -s -H "$H" "$BASE/dashboard/output-type-stats")
check "Output type stats" '"code":200' "$R"

R=$(curl -s -H "$H" "$BASE/dashboard/instance-health")
check "Instance health" '"code":200' "$R"

# Provider update
echo ""
echo "--- Provider Update ---"
R=$(curl -s -H "$H" -X PUT "$BASE/models/providers/$PROVIDER_ID" -H "Content-Type: application/json" -d '{"name":"OpenAI Updated"}')
check "Update provider" '"name":"OpenAI Updated"' "$R"

# System
echo ""
echo "--- System ---"
R=$(curl -s -H "$H" "$BASE/system/info")
check "System info" '"app_name":"OpenClawCM"' "$R"

# Audit logs (admin only)
R=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE/system/audit-logs")
check "Audit logs" '"total":' "$R"

# User management (admin only)
R=$(curl -s -H "Authorization: Bearer $TOKEN" -X POST "$BASE/auth/users" -H "Content-Type: application/json" -d '{"username":"testuser","password":"test123","role":"operator"}')
check "Create user" '"code":200' "$R"

R=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE/auth/users")
check "List users" '"total":' "$R"

# Cleanup - Delete test instance
R=$(curl -s -H "$H" -X DELETE "$BASE/instances/$INSTANCE_ID")
check "Delete instance" '"code":200' "$R"

R=$(curl -s -H "$H" "$BASE/instances/99999")
check "Get non-existent (404)" '"code":404' "$R"

# Summary
echo ""
echo "=========================================="
echo "  Results: $PASS passed, $FAIL failed"
echo "=========================================="

if [ $FAIL -gt 0 ]; then
    exit 1
fi
