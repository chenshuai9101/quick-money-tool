#!/bin/bash

# Agent工厂脚本
# 用法: ./agent_factory.sh <部门> <编号> <专精领域>

DEPARTMENT=$1
AGENT_NUM=$2
SPECIALIZATION=$3
AGENT_ID="${DEPARTMENT}-Agent-${AGENT_NUM}"

# 部门配置映射
declare -A DEPT_CONFIGS=(
    ["tech"]="coding-agent,github,gh-issues|deepseek/deepseek-chat|high|300"
    ["ops"]="summarize,sag,video-frames,discord|deepseek/deepseek-chat|medium|180"
    ["support"]="imsg,discord,taskflow-inbox-triage|deepseek/deepseek-chat|low|120"
    ["pm"]="taskflow,trello,apple-reminders|deepseek/deepseek-chat|medium|180"
)

# 解析配置
IFS='|' read -r SKILLS MODEL THINKING TIMEOUT <<< "${DEPT_CONFIGS[$DEPARTMENT]}"

# 创建Agent目录
AGENT_DIR="$HOME/.openclaw/company/agents/$AGENT_ID"
mkdir -p "$AGENT_DIR"

# 生成Agent配置文件
cat > "$AGENT_DIR/config.json" << EOF
{
  "agentId": "$AGENT_ID",
  "department": "$DEPARTMENT",
  "specialization": "$SPECIALIZATION",
  "model": "$MODEL",
  "thinking": "$THINKING",
  "timeoutSeconds": $TIMEOUT,
  "skills": "$SKILLS",
  "createdAt": "$(date -Iseconds)",
  "status": "active",
  "performance": {
    "tasksCompleted": 0,
    "successRate": 1.0,
    "avgResponseTime": 0
  }
}
EOF

# 生成初始化任务
INIT_TASK="你是一名${DEPARTMENT}部门的专家，专精于${SPECIALIZATION}。你的技能包括：${SKILLS}。请等待具体任务分配。"

echo "Agent配置已创建: $AGENT_ID"
echo "配置位置: $AGENT_DIR/config.json"
echo "初始化任务: $INIT_TASK"

# 这里可以添加实际创建会话的代码
# sessions_spawn(...)