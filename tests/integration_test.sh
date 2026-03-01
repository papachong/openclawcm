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

R=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE/auth/me")
check "Get current user" '"username":"admin"' "$R"

R=$(curl -s -X POST "$BASE/auth/login" -H "Content-Type: application/json" -d '{"username":"admin","password":"wrong"}')
check "Login with wrong password" '"code":401' "$R"

# Instances
echo ""
echo "--- Instance Management ---"
R=$(curl -s -X POST "$BASE/instances" -H "Content-Type: application/json" -d '{"name":"test-01","url":"http://10.0.1.10:8080","api_key":"key1","group_name":"dev"}')
check "Create instance" '"code":200' "$R"
INSTANCE_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s "$BASE/instances")
check "List instances" '"total":' "$R"

R=$(curl -s "$BASE/instances/$INSTANCE_ID")
check "Get instance" '"name":"test-01"' "$R"

R=$(curl -s -X PUT "$BASE/instances/$INSTANCE_ID" -H "Content-Type: application/json" -d '{"name":"test-01-updated"}')
check "Update instance" '"name":"test-01-updated"' "$R"

# Model Providers
echo ""
echo "--- Model Provider Management ---"
R=$(curl -s -X POST "$BASE/models/providers" -H "Content-Type: application/json" -d '{"name":"OpenAI","api_type":"openai","base_url":"https://api.openai.com/v1","api_key":"sk-test"}')
check "Create provider" '"code":200' "$R"
PROVIDER_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s "$BASE/models/providers")
check "List providers" '"name":"OpenAI"' "$R"

# Model Configs
echo ""
echo "--- Model Config Management ---"
R=$(curl -s -X POST "$BASE/models" -H "Content-Type: application/json" -d "{\"name\":\"GPT-4o\",\"provider_id\":$PROVIDER_ID,\"model_name\":\"gpt-4o\",\"scope\":\"global\",\"temperature\":0.7,\"max_tokens\":4096}")
check "Create model config" '"code":200' "$R"
MODEL_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s "$BASE/models")
check "List model configs" '"total":' "$R"

# Agents
echo ""
echo "--- Agent Management ---"
R=$(curl -s -X POST "$BASE/agents" -H "Content-Type: application/json" -d "{\"name\":\"Coder\",\"instance_id\":$INSTANCE_ID,\"role\":\"developer\",\"model_config_id\":$MODEL_ID,\"system_prompt\":\"You are a coding assistant\"}")
check "Create agent" '"code":200' "$R"
AGENT_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s "$BASE/agents")
check "List agents" '"total":' "$R"

R=$(curl -s "$BASE/agents/$AGENT_ID")
check "Get agent" '"name":"Coder"' "$R"

R=$(curl -s -X POST "$BASE/agents/$AGENT_ID/start")
check "Start agent" '"status":"running"' "$R"

R=$(curl -s -X POST "$BASE/agents/$AGENT_ID/stop")
check "Stop agent" '"status":"stopped"' "$R"

# Skills
echo ""
echo "--- Skills Management ---"
R=$(curl -s -X POST "$BASE/skills" -H "Content-Type: application/json" -d '{"name":"web_search","version":"1.0.0","description":"Web search skill"}')
check "Create skill" '"code":200' "$R"
SKILL_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s "$BASE/skills")
check "List skills" '"total":' "$R"

# Outputs
echo ""
echo "--- Output Management ---"
R=$(curl -s -X POST "$BASE/outputs" -H "Content-Type: application/json" -d "{\"instance_id\":$INSTANCE_ID,\"agent_id\":$AGENT_ID,\"output_type\":\"CODE\",\"title\":\"Hello World\",\"content\":\"print('hello')\",\"content_type\":\"python\",\"status\":\"success\"}")
check "Create output" '"code":200' "$R"
OUTPUT_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s "$BASE/outputs")
check "List outputs" '"total":' "$R"

R=$(curl -s "$BASE/outputs/$OUTPUT_ID")
check "Get output" '"title":"Hello World"' "$R"

R=$(curl -s -X POST "$BASE/outputs/$OUTPUT_ID/favorite")
check "Toggle favorite" '"is_favorite":' "$R"

R=$(curl -s -X POST "$BASE/outputs/$OUTPUT_ID/tags" -H "Content-Type: application/json" -d '{"tag_name":"python"}')
check "Add tag" '"code":200' "$R"

# FTS Search
R=$(curl -s "$BASE/outputs/search?q=Hello")
check "FTS search" '"total":' "$R"

# Collaborations
echo ""
echo "--- Collaboration Management ---"
R=$(curl -s -X POST "$BASE/collaborations" -H "Content-Type: application/json" -d '{"name":"code-review","type":"chain","agent_ids":"[1]","routing_rules":"{}"}')
check "Create collaboration" '"code":200' "$R"
COLLAB_ID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")

R=$(curl -s "$BASE/collaborations")
check "List collaborations" '"total":' "$R"

# Dashboard
echo ""
echo "--- Dashboard ---"
R=$(curl -s "$BASE/dashboard/overview")
check "Dashboard overview" '"instance_count":' "$R"

R=$(curl -s "$BASE/dashboard/recent-outputs")
check "Recent outputs" '"code":200' "$R"

R=$(curl -s "$BASE/dashboard/alerts")
check "Alerts" '"code":200' "$R"

# System
echo ""
echo "--- System ---"
R=$(curl -s "$BASE/system/info")
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
R=$(curl -s -X DELETE "$BASE/instances/$INSTANCE_ID")
check "Delete instance" '"code":200' "$R"

R=$(curl -s "$BASE/instances/99999")
check "Get non-existent (404)" '"code":404' "$R"

# Summary
echo ""
echo "=========================================="
echo "  Results: $PASS passed, $FAIL failed"
echo "=========================================="

if [ $FAIL -gt 0 ]; then
    exit 1
fi
