#!/usr/bin/env python3
"""
快速赚钱工具 - 帮助用户通过多种方式在线赚取小额收入
作者：牧云野
目标：24小时内赚取5元人民币
"""

import sys
import os
import json
import time
from datetime import datetime
import webbrowser
import subprocess

class QuickMoneyTool:
    def __init__(self):
        self.methods = {
            "1": {
                "name": "在线调查平台",
                "description": "完成简单调查问卷获取报酬",
                "estimated_earnings": "1-10元/调查",
                "time_required": "5-15分钟/调查",
                "platforms": ["问卷星", "第一调查网", "收奖网"]
            },
            "2": {
                "name": "微任务平台",
                "description": "完成简单任务如数据标注、内容审核",
                "estimated_earnings": "0.1-2元/任务",
                "time_required": "1-5分钟/任务",
                "platforms": ["阿里众包", "百度众测", "腾讯搜活帮"]
            },
            "3": {
                "name": "内容创作",
                "description": "撰写短文、制作表情包等",
                "estimated_earnings": "5-50元/作品",
                "time_required": "30-60分钟/作品",
                "platforms": ["知乎", "简书", "微信公众号"]
            },
            "4": {
                "name": "技能服务",
                "description": "提供编程、设计、翻译等服务",
                "estimated_earnings": "10-100元/小时",
                "time_required": "灵活",
                "platforms": ["猪八戒网", "程序员客栈", "Upwork"]
            }
        }
        
        self.target_amount = 5  # 目标：5元人民币
        self.start_time = datetime.now()
        
    def show_banner(self):
        """显示工具横幅"""
        banner = """
        ╔══════════════════════════════════════╗
        ║      快速赚钱工具 v1.0              ║
        ║      目标：24小时内赚取5元          ║
        ║      作者：牧云野                   ║
        ╚══════════════════════════════════════╝
        """
        print(banner)
        
    def show_methods(self):
        """显示所有赚钱方法"""
        print("\n📊 可用的赚钱方法：")
        print("═" * 50)
        for key, method in self.methods.items():
            print(f"{key}. {method['name']}")
            print(f"   📝 {method['description']}")
            print(f"   💰 预计收益：{method['estimated_earnings']}")
            print(f"   ⏱️  时间需求：{method['time_required']}")
            print(f"   🌐 推荐平台：{', '.join(method['platforms'])}")
            print()
            
    def calculate_progress(self, earnings=0):
        """计算进度"""
        progress = (earnings / self.target_amount) * 100
        elapsed = (datetime.now() - self.start_time).total_seconds() / 3600  # 小时
        
        print(f"\n📈 进度报告：")
        print(f"   目标金额：{self.target_amount} 元")
        print(f"   已赚金额：{earnings} 元")
        print(f"   完成进度：{progress:.1f}%")
        print(f"   已用时间：{elapsed:.1f} 小时")
        print(f"   剩余时间：{24 - elapsed:.1f} 小时")
        
        if earnings >= self.target_amount:
            print("\n🎉 恭喜！你已达成目标！")
            return True
        else:
            remaining = self.target_amount - earnings
            print(f"\n🎯 还需赚取：{remaining} 元")
            return False
            
    def generate_action_plan(self, selected_methods):
        """生成行动计划"""
        print("\n📋 你的行动计划：")
        print("═" * 50)
        
        total_estimated_time = 0
        for method_key in selected_methods:
            method = self.methods[method_key]
            print(f"✅ {method['name']}:")
            print(f"   行动：访问 {method['platforms'][0]}")
            print(f"   任务：完成1-2个{method['description'].split('，')[0]}")
            print(f"   预计收益：{method['estimated_earnings']}")
            print()
            
        print("💡 提示：")
        print("   1. 从最简单的方法开始")
        print("   2. 同时尝试多个平台")
        print("   3. 记录你的收入")
        print("   4. 每完成一个任务就更新进度")
        
    def save_progress(self, earnings, notes=""):
        """保存进度到文件"""
        progress_data = {
            "target_amount": self.target_amount,
            "current_earnings": earnings,
            "start_time": self.start_time.isoformat(),
            "current_time": datetime.now().isoformat(),
            "notes": notes
        }
        
        with open("money_progress.json", "w", encoding="utf-8") as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 进度已保存到 money_progress.json")
        
    def open_platform_links(self):
        """尝试打开平台链接（如果环境允许）"""
        print("\n🔗 尝试打开推荐平台...")
        
        # 这些是中国可访问的平台
        platforms = {
            "问卷星": "https://www.wjx.cn",
            "阿里众包": "https://newjob.taobao.com",
            "猪八戒网": "https://www.zbj.com",
            "知乎": "https://www.zhihu.com"
        }
        
        for name, url in platforms.items():
            print(f"   正在打开 {name} ({url})...")
            try:
                # 尝试用默认浏览器打开
                webbrowser.open(url)
                time.sleep(1)
            except:
                print(f"   无法打开 {name}，请手动访问")
                
    def run(self):
        """运行主程序"""
        self.show_banner()
        
        # 显示方法
        self.show_methods()
        
        # 获取用户选择
        print("请选择你想尝试的方法（输入数字，多个用逗号分隔，如：1,2）：")
        selection = input("> ").strip()
        
        selected_methods = [s.strip() for s in selection.split(",") if s.strip() in self.methods]
        
        if not selected_methods:
            print("⚠️  未选择有效方法，将使用默认方法1和2")
            selected_methods = ["1", "2"]
            
        # 生成行动计划
        self.generate_action_plan(selected_methods)
        
        # 尝试打开平台链接
        self.open_platform_links()
        
        # 获取当前收入
        print("\n💰 请输入你目前已赚取的金额（元）：")
        try:
            current_earnings = float(input("> ").strip())
        except:
            current_earnings = 0
            
        # 计算进度
        self.calculate_progress(current_earnings)
        
        # 保存进度
        self.save_progress(current_earnings, f"选择了方法：{', '.join(selected_methods)}")
        
        print("\n✨ 工具运行完成！")
        print("   请按照行动计划开始赚钱吧！")
        print("   记得定期运行此工具更新进度。")
        
if __name__ == "__main__":
    tool = QuickMoneyTool()
    tool.run()