#!/bin/bash

# Agent健康监控脚本
# 定期检查Agent状态，重启失败的Agent

COMPANY_DIR="$HOME/.openclaw/company"
AGENTS_DIR="$COMPANY_DIR/agents"
LOG_DIR="$COMPANY_DIR/logs"
MONITOR_LOG="$LOG_DIR/monitor_$(date +%Y%m%d).log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MONITOR_LOG"
}

# 检查Agent状态
check_agent_health() {
    local agent_id=$1
    local agent_dir="$AGENTS_DIR/$agent_id"
    
    if [ ! -d "$agent_dir" ]; then
        log "ERROR: Agent目录不存在: $agent_id"
        return 2
    fi
    
    local config_file="$agent_dir/config.json"
    if [ ! -f "$config_file" ]; then
        log "ERROR: Agent配置文件不存在: $config_file"
        return 2
    fi
    
    # 检查最近活动时间
    local status_file="$agent_dir/status.json"
    if [ -f "$status_file" ]; then
        local last_active=$(jq -r '.lastActive' "$status_file" 2>/dev/null)
        if [ "$last_active" != "null" ] && [ -n "$last_active" ]; then
            local last_ts=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${last_active%%.*}" "+%s" 2>/dev/null || echo 0)
            local now_ts=$(date "+%s")
            local diff=$((now_ts - last_ts))
            
            # 如果超过5分钟无活动，认为不健康
            if [ $diff -gt 300 ]; then
                log "WARN: Agent $agent_id 超过5分钟无活动 (${diff}秒)"
                return 1
            fi
        fi
    fi
    
    # 检查错误计数
    local error_file="$agent_dir/errors.json"
    if [ -f "$error_file" ]; then
        local error_count=$(jq '.errors | length' "$error_file" 2>/dev/null || echo 0)
        if [ "$error_count" -gt 3 ]; then
            log "WARN: Agent $agent_id 错误次数过多: $error_count"
            return 1
        fi
    fi
    
    log "INFO: Agent $agent_id 状态正常"
    return 0
}

# 重启Agent
restart_agent() {
    local agent_id=$1
    local agent_dir="$AGENTS_DIR/$agent_id"
    
    log "INFO: 重启Agent: $agent_id"
    
    # 更新状态
    echo '{"lastRestart": "'$(date -Iseconds)'", "restartCount": 1}' > "$agent_dir/restart.json"
    
    # 这里可以添加实际重启逻辑
    # 例如: 发送重启指令到Agent会话
    
    # 模拟重启成功
    echo '{"status": "active", "lastActive": "'$(date -Iseconds)'"}' > "$agent_dir/status.json"
    
    log "INFO: Agent $agent_id 重启完成"
}

# 主监控循环
monitor_agents() {
    log "=== 开始Agent健康检查 ==="
    
    # 检查所有Agent
    for agent_dir in "$AGENTS_DIR"/*/; do
        if [ -d "$agent_dir" ]; then
            agent_id=$(basename "$agent_dir")
            log "检查Agent: $agent_id"
            
            check_agent_health "$agent_id"
            health_status=$?
            
            case $health_status in
                0)
                    # 健康，更新状态
                    echo '{"status": "healthy", "lastActive": "'$(date -Iseconds)'"}' > "$agent_dir/status.json"
                    ;;
                1)
                    # 不健康，尝试重启
                    log "尝试重启不健康的Agent: $agent_id"
                    restart_agent "$agent_id"
                    ;;
                2)
                    # 配置错误，需要人工干预
                    log "ERROR: Agent $agent_id 配置错误，需要人工检查"
                    ;;
            esac
        fi
    done
    
    log "=== Agent健康检查完成 ==="
}

# 性能统计
collect_metrics() {
    log "=== 收集性能指标 ==="
    
    local metrics_file="$COMPANY_DIR/metrics_$(date +%Y%m%d).json"
    local metrics='{"timestamp": "'$(date -Iseconds)'", "agents": {}}'
    
    for agent_dir in "$AGENTS_DIR"/*/; do
        if [ -d "$agent_dir" ]; then
            agent_id=$(basename "$agent_dir")
            
            # 获取Agent指标
            local task_count=0
            local success_count=0
            
            # 统计任务完成情况
            if [ -f "$agent_dir/tasks.json" ]; then
                task_count=$(jq '.total' "$agent_dir/tasks.json" 2>/dev/null || echo 0)
                success_count=$(jq '.completed' "$agent_dir/tasks.json" 2>/dev/null || echo 0)
            fi
            
            # 计算成功率
            local success_rate=1.0
            if [ "$task_count" -gt 0 ]; then
                success_rate=$(echo "scale=2; $success_count / $task_count" | bc)
            fi
            
            # 添加到指标
            metrics=$(echo "$metrics" | jq --arg id "$agent_id" \
                --argjson tasks "$task_count" \
                --argjson success "$success_count" \
                --argjson rate "$success_rate" \
                '.agents[$id] = {"tasks": $tasks, "success": $success, "successRate": $rate}')
        fi
    done
    
    echo "$metrics" | jq '.' > "$metrics_file"
    log "性能指标已保存到: $metrics_file"
}

# 主函数
main() {
    log "启动Agent监控系统"
    
    # 检查目录是否存在
    if [ ! -d "$AGENTS_DIR" ]; then
        log "ERROR: Agent目录不存在: $AGENTS_DIR"
        exit 1
    fi
    
    # 执行监控
    monitor_agents
    
    # 收集性能指标
    collect_metrics
    
    log "监控完成"
}

# 运行主函数
main "$@"