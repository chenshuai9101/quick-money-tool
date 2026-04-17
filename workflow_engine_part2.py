#!/usr/bin/env python3
"""
工作流引擎 - 续
"""

import json
import os
import time
import yaml
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Dict, List, Any, Optional

# 导入第一部分
from workflow_engine import Workflow, WorkflowInstance, WorkflowStatus, WorkflowEngine

class EnhancedWorkflowEngine(WorkflowEngine):
    def __init__(self, workflows_dir: str = "~/.openclaw/company/workflows"):
        super().__init__(workflows_dir)
        self.agent_skills_db = self.load_agent_skills()
    
    def load_agent_skills(self) -> Dict[str, List[str]]:
        """加载Agent技能数据库"""
        skills_file = Path("~/.openclaw/company/agents/skills_db.json").expanduser()
        if skills_file.exists():
            with open(skills_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def find_best_agent_for_step(self, workflow_step, available_agents: List[Dict[str, Any]]) -> Optional[str]:
        """为工作流步骤找到最合适的Agent"""
        if not available_agents:
            return None
        
        required_skills = set(workflow_step.required_skills)
        scored_agents = []
        
        for agent in available_agents:
            agent_id = agent.get("agent_id")
            agent_skills = set(self.agent_skills_db.get(agent_id, []))
            
            # 计算技能匹配度
            matched_skills = required_skills.intersection(agent_skills)
            match_score = len(matched_skills) / len(required_skills) if required_skills else 0
            
            # 考虑Agent负载
            current_load = agent.get("current_tasks", 0)
            load_penalty = current_load * 0.1  # 每个任务减0.1分
            
            # 考虑历史成功率
            success_rate = agent.get("success_rate", 1.0)
            
            # 综合得分
            total_score = (match_score * 0.6 + success_rate * 0.4) - load_penalty
            
            scored_agents.append({
                "agent_id": agent_id,
                "score": total_score,
                "match_score": match_score,
                "load": current_load
            })
        
        if scored_agents:
            scored_agents.sort(key=lambda x: x["score"], reverse=True)
            return scored_agents[0]["agent_id"]
        
        return None
    
    def execute_workflow(self, instance_id: str, available_agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行工作流实例"""
        if instance_id not in self.instances:
            instance = self.load_instance(instance_id)
            if not instance:
                return {"status": "error", "message": f"工作流实例不存在: {instance_id}"}
        
        instance = self.instances[instance_id]
        
        if instance.status != WorkflowStatus.RUNNING:
            instance.start()
        
        result = {
            "instance_id": instance_id,
            "workflow_id": instance.workflow.workflow_id,
            "current_step": instance.current_step,
            "total_steps": len(instance.workflow.steps),
            "steps": []
        }
        
        # 执行当前及后续步骤
        while instance.current_step < len(instance.workflow.steps):
            step = instance.workflow.get_step(instance.current_step)
            if not step:
                instance.fail(f"步骤 {instance.current_step} 不存在")
                break
            
            step_result = self.execute_workflow_step(instance, step, available_agents)
            result["steps"].append(step_result)
            
            if step_result["status"] == "completed":
                instance.complete_step(step_result)
            else:
                instance.fail(step_result.get("error", "未知错误"))
                break
            
            # 保存进度
            self.save_instance(instance)
        
        # 更新最终状态
        result["status"] = instance.status.value
        result["completed_at"] = instance.end_time.isoformat() if instance.end_time else None
        
        return result
    
    def execute_workflow_step(self, instance: WorkflowInstance, step: Any, available_agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行单个工作流步骤"""
        step_start = datetime.now()
        
        try:
            # 找到合适的Agent
            best_agent_id = self.find_best_agent_for_step(step, available_agents)
            
            if not best_agent_id:
                return {
                    "step_name": step.name,
                    "status": "failed",
                    "error": "没有找到合适的Agent执行此步骤",
                    "start_time": step_start.isoformat(),
                    "end_time": datetime.now().isoformat()
                }
            
            # 准备步骤输入
            step_input = {
                "task_data": instance.task_data,
                "step_config": {
                    "name": step.name,
                    "description": step.description,
                    "timeout_minutes": step.timeout_minutes,
                    "required_skills": step.required_skills
                },
                "previous_results": instance.step_results[-3:] if instance.step_results else []
            }
            
            # 这里应该调用Agent执行任务
            # 暂时模拟执行
            time.sleep(2)  # 模拟执行时间
            
            step_output = {
                "agent_id": best_agent_id,
                "execution_time": 2.0,
                "output": f"步骤 '{step.name}' 执行完成",
                "artifacts": ["output_file.txt"]
            }
            
            return {
                "step_name": step.name,
                "status": "completed",
                "agent_id": best_agent_id,
                "input": step_input,
                "output": step_output,
                "start_time": step_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "execution_time": (datetime.now() - step_start).total_seconds()
            }
            
        except Exception as e:
            return {
                "step_name": step.name,
                "status": "failed",
                "error": str(e),
                "start_time": step_start.isoformat(),
                "end_time": datetime.now().isoformat()
            }

# 创建工作流定义文件
def create_workflow_definitions():
    """创建标准工作流定义文件"""
    workflows_dir = Path("~/.openclaw/company/workflows").expanduser()
    workflows_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 技术研发工作流
    tech_workflow = {
        "name": "技术研发标准工作流",
        "description": "用于代码开发、API集成、系统维护等技术任务",
        "agent_type": "tech",
        "trigger_conditions": ["开发", "代码", "API", "集成", "修复", "部署", "编程", "脚本"],
        "steps": [
            {
                "name": "需求分析",
                "description": "分析任务需求，澄清模糊点",
                "timeout_minutes": 10,
                "required_skills": ["coding-agent-analysis"],
                "inputs": ["任务描述", "需求文档"],
                "outputs": ["技术方案文档"],
                "actions": ["需求分析", "技术评估"]
            },
            {
                "name": "架构设计",
                "description": "设计系统架构，选择技术栈",
                "timeout_minutes": 15,
                "required_skills": ["coding-agent-design", "architecture"],
                "inputs": ["技术方案"],
                "outputs": ["架构设计图", "技术选型"],
                "actions": ["架构设计", "技术选型"]
            },
            {
                "name": "代码开发",
                "description": "编写代码，实现功能",
                "timeout_minutes": 60,
                "required_skills": ["coding-agent-development", "github"],
                "inputs": ["设计文档"],
                "outputs": ["代码文件", "测试用例"],
                "actions": ["编写代码", "单元测试"]
            },
            {
                "name": "测试验证",
                "description": "运行测试，修复bug",
                "timeout_minutes": 20,
                "required_skills": ["coding-agent-testing"],
                "inputs": ["代码文件"],
                "outputs": ["测试报告", "修复记录"],
                "actions": ["运行测试", "bug修复"]
            },
            {
                "name": "文档编写",
                "description": "编写使用文档和API文档",
                "timeout_minutes": 15,
                "required_skills": ["coding-agent-documentation"],
                "inputs": ["完成的功能"],
                "outputs": ["README.md", "API文档"],
                "actions": ["文档编写"]
            },
            {
                "name": "交付部署",
                "description": "打包交付，部署到目标环境",
                "timeout_minutes": 10,
                "required_skills": ["github", "deployment"],
                "inputs": ["所有产出物"],
                "outputs": ["交付包", "部署指南"],
                "actions": ["打包", "部署"]
            }
        ]
    }
    
    # 2. 运营推广工作流
    ops_workflow = {
        "name": "运营推广标准工作流",
        "description": "用于内容创作、社交媒体管理、用户运营等任务",
        "agent_type": "ops",
        "trigger_conditions": ["内容", "文章", "视频", "社交", "推广", "宣传", "营销", "运营"],
        "steps": [
            {
                "name": "内容策划",
                "description": "制定内容策略，确定形式",
                "timeout_minutes": 15,
                "required_skills": ["summarize-analysis"],
                "inputs": ["主题", "目标受众"],
                "outputs": ["内容策划方案"],
                "actions": ["策略制定", "形式确定"]
            },
            {
                "name": "素材收集",
                "description": "收集图片、数据、参考资料",
                "timeout_minutes": 20,
                "required_skills": ["web_fetch", "image_generate"],
                "inputs": ["策划方案"],
                "outputs": ["素材库", "参考资料"],
                "actions": ["素材搜索", "资料收集"]
            },
            {
                "name": "内容制作",
                "description": "撰写文章或制作视频",
                "timeout_minutes": 45,
                "required_skills": ["summarize-creation", "video-frames"],
                "inputs": ["素材库"],
                "outputs": ["内容草稿"],
                "actions": ["内容创作", "编辑制作"]
            },
            {
                "name": "优化润色",
                "description": "优化语言，添加视觉元素",
                "timeout_minutes": 15,
                "required_skills": ["sag", "image-optimization"],
                "inputs": ["内容草稿"],
                "outputs": ["优化后内容"],
                "actions": ["语言优化", "视觉优化"]
            },
            {
                "name": "格式转换",
                "description": "转换为目标平台格式",
                "timeout_minutes": 10,
                "required_skills": ["format-conversion"],
                "inputs": ["优化内容"],
                "outputs": ["多种格式内容"],
                "actions": ["格式转换"]
            },
            {
                "name": "发布分发",
                "description": "发布到各平台，安排时间",
                "timeout_minutes": 15,
                "required_skills": ["discord", "slack", "cron"],
                "inputs": ["最终内容"],
                "outputs": ["发布链接", "时间表"],
                "actions": ["平台发布", "时间安排"]
            }
        ]
    }
    
    # 保存工作流定义
    with open(workflows_dir / "tech_workflow.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(tech_workflow, f, allow_unicode=True, default_flow_style=False)
    
    with open(workflows_dir / "ops_workflow.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(ops_workflow, f, allow_unicode=True, default_flow_style=False)
    
    print("工作流定义文件已创建")

# 使用示例
if __name__ == "__main__":
    # 创建工作流定义
    create_workflow_definitions()
    
    # 初始化工作流引擎
    engine = EnhancedWorkflowEngine()
    
    # 模拟可用Agent
    available_agents = [
        {"agent_id": "tech-agent-001", "current_tasks": 2, "success_rate": 0.95},
        {"agent_id": "tech-agent-002", "current_tasks": 1, "success_rate": 0.92},
        {"agent_id": "ops-agent-001", "current_tasks": 0, "success_rate": 0.98},
    ]
    
    # 模拟Agent技能
    engine.agent_skills_db = {
        "tech-agent-001": ["coding-agent-analysis", "coding-agent-design", "coding-agent-development", "github"],
        "tech-agent-002": ["coding-agent-testing", "coding-agent-documentation", "deployment"],
        "ops-agent-001": ["summarize-analysis", "summarize-creation", "web_fetch", "discord"]
    }
    
    # 测试任务匹配
    test_task = "开发一个天气查询API，需要集成Open-Meteo服务"
    matched_workflow = engine.find_matching_workflow(test_task)
    
    if matched_workflow:
        print(f"匹配到工作流: {matched_workflow.name}")
        
        # 创建工作流实例
        task_data = {
            "title": "天气查询API开发",
            "description": test_task,
            "priority": "high",
            "estimated_hours": 4
        }
        
        instance = engine.create_instance(matched_workflow.workflow_id, task_data)
        
        if instance:
            # 执行工作流
            result = engine.execute_workflow(instance.instance_id, available_agents)
            print(f"工作流执行结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print("没有匹配的工作流")