#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型差分隐私使用示例
展示如何在自然语言处理中应用差分隐私
"""

import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from 大模型DP训练 import DPLMConfig, TextPrivacyProtector
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_text_privatization():
    """演示文本隐私保护功能"""
    
    print("=== 🔒 文本隐私保护演示 ===")
    
    # 配置差分隐私参数
    config = DPLMConfig(
        epsilon=1.0,
        delta=1e-5,
        text_privacy_level="medium"  # 可选: low, medium, high
    )
    
    # 创建文本隐私保护器
    protector = TextPrivacyProtector(config)
    
    # 示例敏感文本
    sensitive_texts = [
        "患者张三，身份证号123456789012345678，住址北京市朝阳区某某街道123号，电话13812345678",
        "李医生诊断，患者王五患有糖尿病，需要进行胰岛素治疗",
        "用户邮箱 user@example.com，注册时间2023-05-15，账户余额1000元",
        "客户刘某某，年龄35岁，职业软件工程师，月收入15000元"
    ]
    
    print("\n🔍 不同隐私保护级别的效果对比：")
    
    for level in ["low", "medium", "high"]:
        print(f"\n--- {level.upper()}级别隐私保护 ---")
        config.text_privacy_level = level
        protector = TextPrivacyProtector(config)
        
        for i, text in enumerate(sensitive_texts[:2], 1):  # 只展示前两个
            protected_text = protector.privatize_text(text)
            print(f"{i}. 原文: {text}")
            print(f"   保护后: {protected_text}")
            print()


def demo_privacy_budget_analysis():
    """演示隐私预算分析"""
    
    print("=== 📊 隐私预算分析演示 ===")
    
    epsilons = [0.1, 0.5, 1.0, 2.0, 5.0]
    
    sample_text = "患者张三，男，35岁，诊断为高血压，医生建议药物治疗"
    
    print(f"\n原始文本: {sample_text}")
    print("\n不同epsilon值的隐私保护效果：")
    
    for epsilon in epsilons:
        config = DPLMConfig(epsilon=epsilon, text_privacy_level="medium")
        protector = TextPrivacyProtector(config)
        
        protected_text = protector.privatize_text(sample_text)
        
        print(f"\nε = {epsilon:3.1f}: {protected_text}")
        
        # 分析隐私强度
        if epsilon < 0.5:
            privacy_level = "🔒 极强隐私保护"
        elif epsilon < 1.5:
            privacy_level = "🛡️ 中等隐私保护"
        else:
            privacy_level = "🔓 较弱隐私保护"
        
        print(f"        隐私强度: {privacy_level}")


def demo_text_generation_privacy():
    """演示文本生成中的隐私保护"""
    
    print("=== 🤖 文本生成隐私保护演示 ===")
    
    # 模拟文本生成的隐私保护过程
    prompts = [
        "医生建议",
        "患者症状",
        "治疗方案",
        "诊断结果"
    ]
    
    # 模拟不同epsilon值下的生成效果
    epsilons = [0.1, 1.0, 10.0]
    
    print("\n模拟文本生成中的差分隐私应用：")
    
    for prompt in prompts[:2]:  # 只展示前两个
        print(f"\n提示词: '{prompt}'")
        
        for epsilon in epsilons:
            # 模拟生成过程（实际应用中会调用真实的生成模型）
            if epsilon == 0.1:
                generated = f"{prompt}相关的一般性描述"
            elif epsilon == 1.0:
                generated = f"{prompt}包含适当细节的描述"
            else:
                generated = f"{prompt}包含详细信息的完整描述"
            
            privacy_note = ""
            if epsilon < 0.5:
                privacy_note = "（高度模糊化，隐私最强）"
            elif epsilon < 2.0:
                privacy_note = "（适度细节，平衡隐私和效用）"
            else:
                privacy_note = "（较多细节，隐私较弱）"
            
            print(f"  ε={epsilon:4.1f}: {generated} {privacy_note}")


def demo_real_world_applications():
    """演示实际应用场景"""
    
    print("=== 🌍 实际应用场景演示 ===")
    
    scenarios = {
        "医疗数据共享": {
            "原始数据": "患者赵某某，45岁女性，确诊乳腺癌，已进行手术治疗",
            "应用场景": "医院间共享病例数据用于医学研究",
            "隐私需求": "保护患者身份，但保留医学特征"
        },
        "企业数据分析": {
            "原始数据": "员工李某某，软件工程师，工作5年，绩效优秀，月薪20000元",
            "应用场景": "HR分析员工数据优化管理",
            "隐私需求": "保护员工个人信息，保留统计特征"
        },
        "AI模型训练": {
            "原始数据": "用户张某某发表评论：这家餐厅的服务态度很好，推荐！",
            "应用场景": "训练情感分析模型",
            "隐私需求": "保护用户身份，保留情感信息"
        }
    }
    
    config = DPLMConfig(epsilon=1.0, text_privacy_level="medium")
    protector = TextPrivacyProtector(config)
    
    for scenario_name, scenario_info in scenarios.items():
        print(f"\n--- {scenario_name} ---")
        print(f"应用场景: {scenario_info['应用场景']}")
        print(f"隐私需求: {scenario_info['隐私需求']}")
        print(f"原始数据: {scenario_info['原始数据']}")
        
        protected_data = protector.privatize_text(scenario_info['原始数据'])
        print(f"保护后的数据: {protected_data}")
        
        # 评估效果
        if "某某" in protected_data or "[REDACTED]" in protected_data:
            print("✅ 隐私保护: 成功保护敏感身份信息")
        else:
            print("⚠️ 隐私保护: 可能仍有隐私泄露风险")


def demo_privacy_utility_tradeoff():
    """演示隐私-效用权衡"""
    
    print("=== ⚖️ 隐私-效用权衡分析 ===")
    
    sample_text = "糖尿病患者需要定期监测血糖水平，建议每日测量2-3次"
    
    analysis_configs = [
        {"epsilon": 0.1, "level": "high", "name": "极强隐私保护"},
        {"epsilon": 1.0, "level": "medium", "name": "平衡隐私保护"},
        {"epsilon": 10.0, "level": "low", "name": "较弱隐私保护"},
    ]
    
    print(f"\n原始医疗文本: {sample_text}")
    print("\n隐私-效用权衡分析:")
    
    for config_info in analysis_configs:
        config = DPLMConfig(
            epsilon=config_info["epsilon"], 
            text_privacy_level=config_info["level"]
        )
        protector = TextPrivacyProtector(config)
        
        protected_text = protector.privatize_text(sample_text)
        
        # 计算文本相似度（简化版本）
        original_words = set(sample_text.split())
        protected_words = set(protected_text.split())
        similarity = len(original_words & protected_words) / len(original_words)
        
        print(f"\n{config_info['name']} (ε={config_info['epsilon']}):")
        print(f"  保护后文本: {protected_text}")
        print(f"  文本相似度: {similarity:.2f}")
        print(f"  隐私强度: {'🔒' * (3 if config_info['epsilon'] < 1 else 2 if config_info['epsilon'] < 5 else 1)}")
        print(f"  效用保持: {'⭐' * int(similarity * 5)}")


def main():
    """主演示函数"""
    
    print("🎉 欢迎来到大模型差分隐私演示！")
    print("我们将展示差分隐私在自然语言处理中的各种应用\n")
    
    try:
        # 1. 文本隐私保护
        demo_text_privatization()
        
        input("\n按Enter键继续下一个演示...")
        
        # 2. 隐私预算分析
        demo_privacy_budget_analysis()
        
        input("\n按Enter键继续下一个演示...")
        
        # 3. 文本生成隐私保护
        demo_text_generation_privacy()
        
        input("\n按Enter键继续下一个演示...")
        
        # 4. 实际应用场景
        demo_real_world_applications()
        
        input("\n按Enter键继续下一个演示...")
        
        # 5. 隐私-效用权衡
        demo_privacy_utility_tradeoff()
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
    
    print("\n" + "="*60)
    print("🎓 演示完成！你现在应该理解了：")
    print("✓ 如何在自然语言中应用差分隐私")
    print("✓ 不同隐私强度的效果对比")
    print("✓ 隐私保护与数据效用的权衡")
    print("✓ 实际应用场景中的隐私保护策略")
    print("\n核心要点：")
    print("• 文本数据需要特殊的隐私保护方法")
    print("• epsilon值越小，隐私保护越强，但数据效用可能降低")
    print("• 不同应用场景需要不同的隐私保护策略")
    print("• 差分隐私提供了数学可证明的隐私保证")


if __name__ == "__main__":
    main() 