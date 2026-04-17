#!/usr/bin/env python3
"""
任务分派系统
负责将任务分派给合适的Agent，并监控执行状态
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

class TaskDispatcher:
    def __init__(self, base_dir="~/.openclaw/company"):
        self.base_dir = Path(base_dir).expanduser()
        self.queues_dir = self.base_dir / "queues"
        self.agents_dir = self.base_dir / "agents"
        self.tasks_dir = self.base_dir / "tasks"
        
        # 创建目录结构
        for dir_path in [self.queues_dir, self.agents_dir, self.tasks_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 队列子目录
        for queue in ["pending", "processing", "completed", "failed"]:
            (self.queues_dir / queue).mkdir(exist_ok=True)
    
    def create_task(self, task_data):
        """创建新任务"""
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.urandom(4).hex()}"
        
        task = {
            "id": task_id,
            "createdAt": datetime.now().isoformat(),
            "status": "pending",
            "data": task_data,
            "history": []
        }
        
        # 保存任务文件
        task_file = self.tasks_dir / f"{task_id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        
        # 添加到待处理队列
        queue_file = self.queues_dir / "pending" / f"{task_id}.json"
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump({"taskId": task_id, "addedAt": datetime.now().isoformat()}, f)
        
        print(f"任务创建成功: {task_id}")
        return task_id
    
    def assign_task(self, task_id, agent_id):
        """将任务分派给Agent"""
        task_file = self.tasks_dir / f"{task_id}.json"
        
        if not task_file.exists():
            print(f"任务不存在: {task_id}")
            return False
        
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)
        
        # 更新任务状态
        task["status"] = "processing"
        task["assignedTo"] = agent_id
        task["assignedAt"] = datetime.now().isoformat()
        task["history"].append({
            "action": "assigned",
            "to": agent_id,
            "at": datetime.now().isoformat()
        })
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        
        # 移动队列文件
        pending_file = self.queues_dir / "pending" / f"{task_id}.json"
        processing_file = self.queues_dir / "processing" / f"{task_id}.json"
        
        if pending_file.exists():
            pending_file.rename(processing_file)
        
        print(f"任务 {task_id} 已分派给 {agent_id}")
        return True
    
    def complete_task(self, task_id, result):
        """标记任务完成"""
        task_file = self.tasks_dir / f"{task_id}.json"
        
        if not task_file.exists():
            print(f"任务不存在: {task_id}")
            return False
        
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)
        
        # 更新任务状态
        task["status"] = "completed"
        task["completedAt"] = datetime.now().isoformat()
        task["result"] = result
        task["history"].append({
            "action": "completed",
            "at": datetime.now().isoformat(),
            "result": "success"
        })
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        
        # 移动队列文件
        processing_file = self.queues_dir / "processing" / f"{task_id}.json"
        completed_file = self.queues_dir / "completed" / f"{task_id}.json"
        
        if processing_file.exists():
            processing_file.rename(completed_file)
        
        print(f"任务 {task_id} 已完成")
        return True
    
    def fail_task(self, task_id, error):
        """标记任务失败"""
        task_file = self.tasks_dir / f"{task_id}.json"
        
        if not task_file.exists():
            print(f"任务不存在: {task_id}")
            return False
        
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)
        
        # 更新任务状态
        task["status"] = "failed"
        task["failedAt"] = datetime.now().isoformat()
        task["error"] = error
        task["history"].append({
            "action": "failed",
            "at": datetime.now().isoformat(),
            "error": error
        })
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        
        # 移动队列文件
        processing_file = self.queues_dir / "processing" / f"{task_id}.json"
        failed_file = self.queues_dir / "failed" / f"{task_id}.json"
        
        if processing_file.exists():
            processing_file.rename(failed_file)
        
        print(f"任务 {task_id} 已标记为失败: {error}")
        return True
    
    def get_pending_tasks(self):
        """获取待处理任务列表"""
        pending_dir = self.queues_dir / "pending"
        tasks = []
        
        for task_file in pending_dir.glob("*.json"):
            with open(task_file, 'r', encoding='utf-8') as f:
                task_ref = json.load(f)
                task_id = task_ref["taskId"]
                
                # 获取完整任务信息
                full_task_file = self.tasks_dir / f"{task_id}.json"
                if full_task_file.exists():
                    with open(full_task_file, 'r', encoding='utf-8') as tf:
                        tasks.append(json.load(tf))
        
        return tasks
    
    def get_agent_tasks(self, agent_id):
        """获取指定Agent的任务"""
        tasks = []
        
        for task_file in self.tasks_dir.glob("*.json"):
            with open(task_file, 'r', encoding='utf-8') as f:
                task = json.load(f)
                if task.get("assignedTo") == agent_id and task.get("status") == "processing":
                    tasks.append(task)
        
        return tasks

# 使用示例
if __name__ == "__main__":
    dispatcher = TaskDispatcher()
    
    # 创建测试任务
    test_task = {
        "title": "开发天气查询技能",
        "department": "tech",
        "priority": "high",
        "description": "使用Open-Meteo API开发天气查询技能",
        "requirements": [
            "支持城市查询",
            "返回温度、天气状况",
            "错误处理"
        ],
        "estimatedHours": 4
    }
    
    task_id = dispatcher.create_task(test_task)
    print(f"创建的任务ID: {task_id}")
    
    # 查看待处理任务
    pending = dispatcher.get_pending_tasks()
    print(f"待处理任务数: {len(pending)}")