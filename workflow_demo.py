#!/usr/bin/env python3
"""
工作流系统演示
展示完整的多Agent工作流执行过程
"""

import json
import time
from datetime import datetime
from workflow_manager import WorkflowManager

def demo_tech_workflow():
    """演示技术研发工作流"""
    print("=" * 60)
    print("演示: 技术研发工作流")
    print("=" * 60)
    
    manager = WorkflowManager()
    
    # 1. 提交技术开发任务
    task_description = "开发一个天气查询API，需要集成Open-Meteo服务，支持城市查询和错误处理"
    
    print(f"提交任务: {task_description}")
    print("-" * 40)
    
    result = manager.submit_task(task_description, {
        "priority": "high",
        "estimated_hours": 4,
        "customer": "示例客户"
    })
    
    print(f"任务ID: {result.get('task_id')}")
    print(f"工作流ID: {result.get('workflow_id')}")
    print(f"实例ID: {result.get('instance_id')}")
    print(f"状态: {result.get('status')}")
    
    # 2. 显示工作流步骤
    if "execution_result" in result:
        execution = result["execution_result"]
        print(f"\n工作流执行步骤 ({execution.get('current_step')}/{execution.get('total_steps')}):")
        
        for i, step in enumerate(execution.get("steps", [])):
            print(f"  {i+1}. {step.get('step_name')}: {step.get('status')}")
            if step.get('agent_id'):
                print(f"     执行Agent: {step.get('agent_id')}")
            if step.get('error'):
                print(f"     错误: {step.get('error')}")
    
    return result

def demo_ops_workflow():
    """演示运营推广工作流"""
    print("\n" + "=" * 60)
    print("演示: 运营推广工作流")
    print("=" * 60)
    
    manager = WorkflowManager()
    
    # 提交内容创作任务
    task_description = "创作一篇关于AI助手的文章，需要包含功能介绍、使用案例和未来展望，制作成微信公众号格式"
    
    print(f"提交任务: {task_description}")
    print("-" * 40)
    
    result = manager.submit_task(task_description, {
        "priority": "medium",
        "target_platform": "微信公众号",
        "word_count": 1500
    })
    
    print(f"任务ID: {result.get('task_id')}")
    print(f"工作流ID: {result.get('workflow_id')}")
    print(f"实例ID: {result.get('instance_id')}")
    
    return result

def demo_support_workflow():
    """演示客户服务工作流"""
    print("\n" + "=" * 60)
    print("演示: 客户服务工作流")
    print("=" * 60)
    
    manager = WorkflowManager()
    
    # 提交客户支持任务
    task_description = "客户反馈天气查询API返回错误代码500，需要诊断问题并提供解决方案"
    
    print(f"提交任务: {task_description}")
    print("-" * 40)
    
    result = manager.submit_task(task_description, {
        "priority": "urgent",
        "customer_id": "CUST-001",
        "issue_type": "technical"
    })
    
    print(f"任务ID: {result.get('task_id')}")
    print(f"工作流ID: {result.get('workflow_id')}")
    
    return result

def demo_pm_workflow():
    """演示项目管理工作流"""
    print("\n" + "=" * 60)
    print("演示: 项目管理工作流")
    print("=" * 60)
    
    manager = WorkflowManager()
    
    # 提交项目管理任务
    task_description = "管理新功能开发项目，包括需求收集、任务分派、进度跟踪和风险控制"
    
    print(f"提交任务: {task_description}")
    print("-" * 40)
    
    result = manager.submit_task(task_description, {
        "priority": "high",
        "project_scope": "新功能开发",
        "team_size": 4,
        "timeline": "2周"
    })
    
    print(f"任务ID: {result.get('task_id')}")
    print(f"工作流ID: {result.get('workflow_id')}")
    
    return result

def demo_multi_workflow_coordination():
    """演示多工作流协调"""
    print("\n" + "=" * 60)
    print("演示: 多工作流协调 - 完整产品开发流程")
    print("=" * 60)
    
    manager = WorkflowManager()
    
    # 模拟一个完整的产品开发流程
    workflows = [
        {
            "name": "项目管理",
            "description": "制定产品开发计划，分配资源",
            "type": "pm"
        },
        {
            "name": "技术开发", 
            "description": "开发核心功能模块，包括用户认证和天气查询",
            "type": "tech"
        },
        {
            "name": "内容创作",
            "description": "制作产品介绍文档和宣传材料",
            "type": "ops"
        },
        {
            "name": "客户支持",
            "description": "准备FAQ和用户支持材料",
            "type": "support"
        }
    ]
    
    print("产品开发流程:")
    for i, wf in enumerate(workflows, 1):
        print(f"  {i}. {wf['name']}: {wf['description']}")
    
    print("\n提交所有工作流任务...")
    
    results = []
    for wf in workflows:
        result = manager.submit_task(
            f"{wf['name']}: {wf['description']}",
            {"workflow_type": wf['type'], "product": "智能天气助手"}
        )
        results.append(result)
        print(f"  ✓ {wf['name']} 任务已提交 (ID: {result.get('task_id')})")
        time.sleep(0.5)  # 避免任务ID冲突
    
    return results

def monitor_all_workflows():
    """监控所有工作流"""
    print("\n" + "=" * 60)
    print("监控: 所有工作流状态")
    print("=" * 60)
    
    manager = WorkflowManager()
    status = manager.monitor_workflows()
    
    print(f"时间: {status.get('timestamp')}")
    print(f"活跃实例数: {status.get('active_instances')}")
    
    if status.get('instances'):
        print("\n活跃工作流实例:")
        for instance in status['instances']:
            print(f"  - {instance.get('workflow_id')}: 步骤 {instance.get('current_step')}/{instance.get('total_steps')}")
            if instance.get('task_data', {}).get('description'):
                desc = instance['task_data']['description']
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                print(f"    任务: {desc}")

def show_system_stats():
    """显示系统统计"""
    print("\n" + "=" * 60)
    print("系统统计")
    print("=" * 60)
    
    manager = WorkflowManager()
    stats = manager.get_workflow_stats()
    
    print(f"总工作流类型: {stats.get('total_workflows')}")
    
    print("\n工作流类型分布:")
    for wf_type, count in stats.get('workflow_types', {}).items():
        print(f"  {wf_type}: {count}个")
    
    print("\nAgent类型分布:")
    for agent_type, count in stats.get('agent_types', {}).items():
        print(f"  {agent_type}: {count}个")

def main():
    """主演示函数"""
    print("🐾 牧云野多Agent工作流系统演示")
    print("=" * 60)
    
    # 初始化系统
    print("1. 初始化工作流系统...")
    # 这里应该调用初始化，但为了演示我们跳过
    
    # 运行各个演示
    demo_results = []
    
    # 演示单个工作流
    demo_results.append(demo_tech_workflow())
    demo_results.append(demo_ops_workflow())
    demo_results.append(demo_support_workflow())
    demo_results.append(demo_pm_workflow())
    
    # 演示多工作流协调
    multi_results = demo_multi_workflow_coordination()
    demo_results.extend(multi_results)
    
    # 监控状态
    monitor_all_workflows()
    
    # 显示统计
    show_system_stats()
    
    # 总结
    print("\n" + "=" * 60)
    print("演示总结")
    print("=" * 60)
    
    total_tasks = len(demo_results)
    successful = sum(1 for r in demo_results if r.get('status') == 'success')
    
    print(f"总演示任务: {total_tasks}")
    print(f"成功任务: {successful}")
    print(f"成功率: {successful/total_tasks*100:.1f}%")
    
    print("\n工作流系统特点:")
    print("  1. 自动任务分类和工作流匹配")
    print("  2. 智能Agent分配和负载均衡")
    print("  3. 完整的工作流步骤管理")
    print("  4. 实时监控和状态跟踪")
    print("  5. 多工作流协调执行")
    
    print("\n🐾 演示完成！系统已准备好处理真实任务。")

if __name__ == "__main__":
    main()