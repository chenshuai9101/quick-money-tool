#!/usr/bin/env python3
"""
工作流管理器
整合工作流引擎、任务分派、Agent匹配
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 导入工作流引擎
sys.path.append(str(Path(__file__).parent))
from workflow_engine_part2 import EnhancedWorkflowEngine, create_workflow_definitions

class WorkflowManager:
    def __init__(self):
        self.base_dir = Path("~/.openclaw/company").expanduser()
        self.workflows_dir = self.base_dir / "workflows"
        self.agents_dir = self.base_dir / "agents"
        self.tasks_dir = self.base_dir / "tasks"
        self.logs_dir = self.base_dir / "logs"
        
        # 创建目录
        for dir_path in [self.workflows_dir, self.agents_dir, self.tasks_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化工作流引擎
        self.engine = EnhancedWorkflowEngine(str(self.workflows_dir))
        
        # 加载Agent状态
        self.agent_status = self.load_agent_status()
    
    def load_agent_status(self):
        """加载Agent状态"""
        status_file = self.agents_dir / "status.json"
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_agent_status(self):
        """保存Agent状态"""
        status_file = self.agents_dir / "status.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(self.agent_status, f, indent=2, ensure_ascii=False)
    
    def get_available_agents(self, agent_type: str = "") -> list:
        """获取可用Agent列表"""
        available = []
        
        for agent_id, status in self.agent_status.items():
            # 检查Agent类型
            if agent_type and status.get("agent_type") != agent_type:
                continue
            
            # 检查是否可用
            if status.get("status") == "active" and status.get("current_tasks", 0) < status.get("max_tasks", 5):
                available.append({
                    "agent_id": agent_id,
                    "agent_type": status.get("agent_type", ""),
                    "current_tasks": status.get("current_tasks", 0),
                    "success_rate": status.get("success_rate", 1.0),
                    "skills": status.get("skills", [])
                })
        
        return available
    
    def register_agent(self, agent_id: str, agent_config: dict):
        """注册新Agent"""
        self.agent_status[agent_id] = {
            "agent_id": agent_id,
            "agent_type": agent_config.get("agent_type", "general"),
            "status": "active",
            "skills": agent_config.get("skills", []),
            "current_tasks": 0,
            "max_tasks": agent_config.get("max_tasks", 5),
            "success_rate": 1.0,
            "registered_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now().isoformat()
        }
        
        self.save_agent_status()
        print(f"Agent已注册: {agent_id}")
    
    def submit_task(self, task_description: str, task_metadata: dict = None) -> dict:
        """提交新任务"""
        if task_metadata is None:
            task_metadata = {}
        
        # 记录任务
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        task_data = {
            "task_id": task_id,
            "description": task_description,
            "metadata": task_metadata,
            "submitted_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        # 保存任务
        task_file = self.tasks_dir / f"{task_id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)
        
        # 查找匹配的工作流
        matched_workflow = self.engine.find_matching_workflow(task_description)
        
        if not matched_workflow:
            return {
                "status": "error",
                "message": "没有找到匹配的工作流",
                "task_id": task_id
            }
        
        # 创建工作流实例
        workflow_input = {
            "task_id": task_id,
            "description": task_description,
            "metadata": task_metadata
        }
        
        instance = self.engine.create_instance(matched_workflow.workflow_id, workflow_input)
        
        if not instance:
            return {
                "status": "error",
                "message": "创建工作流实例失败",
                "task_id": task_id
            }
        
        # 获取可用Agent
        available_agents = self.get_available_agents(matched_workflow.agent_type)
        
        if not available_agents:
            return {
                "status": "error",
                "message": "没有可用的Agent",
                "task_id": task_id,
                "workflow_id": matched_workflow.workflow_id,
                "instance_id": instance.instance_id
            }
        
        # 执行工作流
        result = self.engine.execute_workflow(instance.instance_id, available_agents)
        
        # 更新任务状态
        task_data["status"] = result["status"]
        task_data["workflow_instance_id"] = instance.instance_id
        task_data["completed_at"] = result.get("completed_at")
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "success",
            "task_id": task_id,
            "workflow_id": matched_workflow.workflow_id,
            "instance_id": instance.instance_id,
            "execution_result": result
        }
    
    def monitor_workflows(self):
        """监控所有进行中的工作流"""
        active_instances = []
        
        for instance_file in (self.workflows_dir / "instances").glob("*.json"):
            with open(instance_file, 'r', encoding='utf-8') as f:
                instance_data = json.load(f)
            
            if instance_data.get("status") in ["running", "pending"]:
                active_instances.append(instance_data)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_instances": len(active_instances),
            "instances": active_instances[:10]  # 只返回前10个
        }
    
    def get_workflow_stats(self):
        """获取工作流统计信息"""
        stats = {
            "total_workflows": len(self.engine.workflows),
            "workflow_types": {},
            "agent_types": {},
            "performance": {}
        }
        
        # 统计工作流类型
        for workflow_id, workflow in self.engine.workflows.items():
            agent_type = workflow.agent_type
            stats["workflow_types"][agent_type] = stats["workflow_types"].get(agent_type, 0) + 1
        
        # 统计Agent类型
        for agent_id, status in self.agent_status.items():
            agent_type = status.get("agent_type", "unknown")
            stats["agent_types"][agent_type] = stats["agent_types"].get(agent_type, 0) + 1
        
        return stats

# 命令行界面
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="工作流管理器")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 初始化命令
    init_parser = subparsers.add_parser("init", help="初始化工作流系统")
    
    # 注册Agent命令
    register_parser = subparsers.add_parser("register", help="注册新Agent")
    register_parser.add_argument("--id", required=True, help="Agent ID")
    register_parser.add_argument("--type", required=True, help="Agent类型 (tech/ops/support/pm)")
    register_parser.add_argument("--skills", help="技能列表，逗号分隔")
    
    # 提交任务命令
    submit_parser = subparsers.add_parser("submit", help="提交新任务")
    submit_parser.add_argument("--description", required=True, help="任务描述")
    submit_parser.add_argument("--priority", default="normal", help="优先级")
    
    # 监控命令
    monitor_parser = subparsers.add_parser("monitor", help="监控工作流状态")
    
    # 统计命令
    stats_parser = subparsers.add_parser("stats", help="查看统计信息")
    
    args = parser.parse_args()
    
    manager = WorkflowManager()
    
    if args.command == "init":
        # 创建工作流定义
        create_workflow_definitions()
        print("工作流系统初始化完成")
        
        # 注册示例Agent
        example_agents = [
            {"id": "tech-001", "type": "tech", "skills": ["coding-agent-analysis", "coding-agent-design", "github"]},
            {"id": "ops-001", "type": "ops", "skills": ["summarize-analysis", "summarize-creation", "discord"]},
            {"id": "support-001", "type": "support", "skills": ["taskflow-inbox-triage", "imsg"]},
            {"id": "pm-001", "type": "pm", "skills": ["taskflow", "trello"]}
        ]
        
        for agent in example_agents:
            manager.register_agent(agent["id"], {
                "agent_type": agent["type"],
                "skills": agent["skills"],
                "max_tasks": 3
            })
        
        print("示例Agent已注册")
    
    elif args.command == "register":
        skills = args.skills.split(",") if args.skills else []
        manager.register_agent(args.id, {
            "agent_type": args.type,
            "skills": skills,
            "max_tasks": 3
        })
    
    elif args.command == "submit":
        metadata = {
            "priority": args.priority,
            "submitted_by": "cli"
        }
        
        result = manager.submit_task(args.description, metadata)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "monitor":
        status = manager.monitor_workflows()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif args.command == "stats":
        stats = manager.get_workflow_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()