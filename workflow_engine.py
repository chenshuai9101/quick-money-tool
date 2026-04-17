#!/usr/bin/env python3
"""
工作流引擎
管理不同Agent类型的工作流执行
"""

import json
import os
import time
import yaml
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Dict, List, Any, Optional

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class WorkflowStep:
    def __init__(self, step_config: Dict[str, Any]):
        self.name = step_config.get("name", "")
        self.description = step_config.get("description", "")
        self.timeout_minutes = step_config.get("timeout_minutes", 30)
        self.required_skills = step_config.get("required_skills", [])
        self.inputs = step_config.get("inputs", [])
        self.outputs = step_config.get("outputs", [])
        self.actions = step_config.get("actions", [])
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "timeout_minutes": self.timeout_minutes,
            "required_skills": self.required_skills,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "actions": self.actions
        }

class Workflow:
    def __init__(self, workflow_id: str, workflow_config: Dict[str, Any]):
        self.workflow_id = workflow_id
        self.name = workflow_config.get("name", "")
        self.description = workflow_config.get("description", "")
        self.agent_type = workflow_config.get("agent_type", "")
        self.trigger_conditions = workflow_config.get("trigger_conditions", [])
        self.steps = []
        
        # 解析步骤
        for step_config in workflow_config.get("steps", []):
            self.steps.append(WorkflowStep(step_config))
    
    def get_step(self, step_index: int) -> Optional[WorkflowStep]:
        if 0 <= step_index < len(self.steps):
            return self.steps[step_index]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "trigger_conditions": self.trigger_conditions,
            "steps": [step.to_dict() for step in self.steps]
        }

class WorkflowInstance:
    def __init__(self, instance_id: str, workflow: Workflow, task_data: Dict[str, Any]):
        self.instance_id = instance_id
        self.workflow = workflow
        self.task_data = task_data
        self.status = WorkflowStatus.PENDING
        self.current_step = 0
        self.step_results = []
        self.start_time = None
        self.end_time = None
        self.created_at = datetime.now()
        
    def start(self):
        self.status = WorkflowStatus.RUNNING
        self.start_time = datetime.now()
        self.current_step = 0
    
    def complete_step(self, step_result: Dict[str, Any]):
        self.step_results.append({
            "step_index": self.current_step,
            "step_name": self.workflow.get_step(self.current_step).name if self.workflow.get_step(self.current_step) else "",
            "result": step_result,
            "completed_at": datetime.now().isoformat()
        })
        self.current_step += 1
        
        # 检查是否完成所有步骤
        if self.current_step >= len(self.workflow.steps):
            self.complete()
    
    def complete(self):
        self.status = WorkflowStatus.COMPLETED
        self.end_time = datetime.now()
    
    def fail(self, error: str):
        self.status = WorkflowStatus.FAILED
        self.end_time = datetime.now()
        self.step_results.append({
            "step_index": self.current_step,
            "error": error,
            "failed_at": datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "workflow_id": self.workflow.workflow_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "total_steps": len(self.workflow.steps),
            "task_data": self.task_data,
            "step_results": self.step_results,
            "created_at": self.created_at.isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }

class WorkflowEngine:
    def __init__(self, workflows_dir: str = "~/.openclaw/company/workflows"):
        self.workflows_dir = Path(workflows_dir).expanduser()
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        self.instances_dir = self.workflows_dir / "instances"
        self.instances_dir.mkdir(exist_ok=True)
        
        self.workflows: Dict[str, Workflow] = {}
        self.instances: Dict[str, WorkflowInstance] = {}
        
        # 加载工作流定义
        self.load_workflows()
    
    def load_workflows(self):
        """从YAML文件加载工作流定义"""
        workflow_files = list(self.workflows_dir.glob("*.yaml")) + list(self.workflows_dir.glob("*.yml"))
        
        for workflow_file in workflow_files:
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_config = yaml.safe_load(f)
                
                workflow_id = workflow_file.stem
                workflow = Workflow(workflow_id, workflow_config)
                self.workflows[workflow_id] = workflow
                print(f"加载工作流: {workflow.name} ({workflow_id})")
            except Exception as e:
                print(f"加载工作流失败 {workflow_file}: {e}")
    
    def find_matching_workflow(self, task_description: str, agent_type: str = "") -> Optional[Workflow]:
        """根据任务描述和Agent类型查找匹配的工作流"""
        matching_workflows = []
        
        for workflow_id, workflow in self.workflows.items():
            # 检查Agent类型匹配
            if agent_type and workflow.agent_type != agent_type:
                continue
            
            # 检查触发条件
            matches = 0
            for condition in workflow.trigger_conditions:
                if condition.lower() in task_description.lower():
                    matches += 1
            
            if matches > 0:
                matching_workflows.append((workflow, matches))
        
        if matching_workflows:
            # 选择匹配度最高的工作流
            matching_workflows.sort(key=lambda x: x[1], reverse=True)
            return matching_workflows[0][0]
        
        return None
    
    def create_instance(self, workflow_id: str, task_data: Dict[str, Any]) -> Optional[WorkflowInstance]:
        """创建工作流实例"""
        if workflow_id not in self.workflows:
            print(f"工作流不存在: {workflow_id}")
            return None
        
        workflow = self.workflows[workflow_id]
        instance_id = f"{workflow_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        
        instance = WorkflowInstance(instance_id, workflow, task_data)
        self.instances[instance_id] = instance
        
        # 保存实例到文件
        self.save_instance(instance)
        
        print(f"创建工作流实例: {instance_id}")
        return instance
    
    def save_instance(self, instance: WorkflowInstance):
        """保存工作流实例到文件"""
        instance_file = self.instances_dir / f"{instance.instance_id}.json"
        with open(instance_file, 'w', encoding='utf-8') as f:
            json.dump(instance.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """从文件加载工作流实例"""
        instance_file = self.instances_dir / f"{instance_id}.json"
        
        if not instance_file.exists():
            return None
        
        try:
            with open(instance_file, 'r', encoding='utf-8') as f:
                instance_data = json.load(f)
            
            # 重建实例
            workflow_id = instance_data.get("workflow_id")
            if workflow_id not in self.workflows:
                return None
            
            workflow = self.workflows[workflow_id]
            instance = WorkflowInstance(instance_id, workflow, instance_data.get("task_data", {}))
            
            # 恢复状态
            instance.status = WorkflowStatus(instance_data.get("status", "pending"))
            instance.current_step = instance_data.get("current_step", 0)
            instance.step_results = instance_data.get("step_results", [])
            
            # 时间字段
            if instance_data.get("created_at"):
                instance.created_at = datetime.fromisoformat(instance_data["created_at"])
            if instance_data.get("start_time"):
                instance.start_time = datetime.fromisoformat(instance_data["start_time"])
            if instance_data.get("end_time"):
                instance.end_time = datetime.fromisoformat(instance_data["end_time"])
            
            self.instances[instance_id] = instance
            return instance
            
        except Exception as e:
            print(f"加载工作流实例失败 {instance_id}: {e}")
            return None
    
    def execute_step(self, instance_id: str, step_input: Dict