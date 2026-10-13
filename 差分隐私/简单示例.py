#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超简单的差分隐私体验示例
让你3分钟理解差分隐私是怎么工作的
"""

import numpy as np
import matplotlib.pyplot as plt

print("=== 欢迎来到差分隐私体验课堂！===")
print("我们用一个小学校的例子来理解差分隐私\n")

# 场景设置
print("📚 场景：小明小学有5个班级，每个班的学生数量如下：")
real_class_sizes = [25, 30, 28, 32, 27]
print(f"真实班级人数：{real_class_sizes}")
print(f"总学生数：{sum(real_class_sizes)}")
print(f"平均每班人数：{np.mean(real_class_sizes):.1f}")
print("\n" + "="*50)

# 问题提出
print("\n❓ 问题：")
print("学校想发布班级统计信息用于教育研究，")
print("但是担心泄露具体班级信息（比如某个班特别少人）")
print("怎么既能提供有用信息，又保护隐私呢？")

input("\n按Enter键继续...")

# 差分隐私解决方案
print("\n🛡️ 差分隐私的解决方案：")
print("给每个班级的人数添加一些'随机噪音'！")

def add_differential_privacy(data, noise_level=2):
    """添加差分隐私噪音"""
    # 生成随机噪音
    noise = np.random.normal(0, noise_level, len(data))
    # 添加噪音到原始数据
    private_data = np.array(data) + noise
    # 确保人数不能是负数
    private_data = np.maximum(private_data, 0)
    return private_data, noise

# 体验不同的隐私保护级别
print("\n🔧 让我们试试不同的隐私保护强度：")

for level, noise_strength in [("轻度保护", 1), ("中度保护", 3), ("强度保护", 6)]:
    print(f"\n--- {level} (噪音强度: {noise_strength}) ---")
    
    private_sizes, noise = add_differential_privacy(real_class_sizes, noise_strength)
    
    print(f"原始人数: {real_class_sizes}")
    print(f"添加噪音: {[f'{n:+.1f}' for n in noise]}")
    print(f"隐私保护后: {[int(x) for x in private_sizes]}")
    print(f"真实总数: {sum(real_class_sizes)}, 保护后总数: {int(sum(private_sizes))}")
    print(f"误差: {abs(sum(real_class_sizes) - sum(private_sizes)):.1f}人")

input("\n按Enter键看可视化效果...")

# 可视化对比
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

# 原始数据
ax1.bar(range(1, 6), real_class_sizes, color='blue', alpha=0.7)
ax1.set_title('原始数据\n（真实班级人数）')
ax1.set_xlabel('班级')
ax1.set_ylabel('学生人数')
ax1.set_ylim(0, 40)

# 中度隐私保护
private_medium, _ = add_differential_privacy(real_class_sizes, 3)
ax2.bar(range(1, 6), private_medium, color='orange', alpha=0.7)
ax2.set_title('中度隐私保护\n（加了噪音）')
ax2.set_xlabel('班级')
ax2.set_ylabel('学生人数')
ax2.set_ylim(0, 40)

# 强度隐私保护
private_strong, _ = add_differential_privacy(real_class_sizes, 6)
ax3.bar(range(1, 6), private_strong, color='red', alpha=0.7)
ax3.set_title('强度隐私保护\n（噪音更大）')
ax3.set_xlabel('班级')
ax3.set_ylabel('学生人数')
ax3.set_ylim(0, 40)

plt.tight_layout()
plt.savefig('/home/zp/twf/安全大模型/差分隐私示例图.png', dpi=150, bbox_inches='tight')
print("📊 图表已保存为 '差分隐私示例图.png'")

print("\n" + "="*60)
print("🎯 关键观察：")
print("1. 原始数据：精确但可能泄露隐私")
print("2. 中度保护：数据略有变化，但总体趋势保持")
print("3. 强度保护：个体数据变化较大，但统计特性大致保持")

# 实际应用演示
print("\n" + "="*60)
print("🏥 实际应用示例：医院患者数据")

# 模拟医院数据
diseases = ["糖尿病", "高血压", "心脏病", "癌症", "其他"]
real_patient_counts = [45, 78, 23, 12, 89]

print(f"\n真实患者统计：")
for disease, count in zip(diseases, real_patient_counts):
    print(f"  {disease}: {count}人")

print(f"\n应用差分隐私保护后：")
private_counts, _ = add_differential_privacy(real_patient_counts, 3)
for disease, count in zip(diseases, private_counts):
    print(f"  {disease}: {int(count)}人")

print(f"\n隐私保护效果：")
print(f"- 总患者数误差: {abs(sum(real_patient_counts) - sum(private_counts)):.0f}人")
print(f"- 个别疾病可能差几个人，但整体分布相似")
print("- 可以安全发布用于医学研究，不担心泄露具体患者信息")

# 互动环节
print("\n" + "="*60)
print("🎮 互动环节：你来设计隐私保护方案！")

try:
    user_epsilon = float(input("请输入你想要的隐私保护强度(1-10，数字越大噪音越小): "))
    if user_epsilon < 1:
        user_epsilon = 1
    elif user_epsilon > 10:
        user_epsilon = 10
    
    # 用户自定义的隐私保护
    noise_level = 10 / user_epsilon  # epsilon越大，噪音越小
    user_private_data, user_noise = add_differential_privacy(real_class_sizes, noise_level)
    
    print(f"\n你选择的保护强度: {user_epsilon}")
    print(f"对应噪音级别: {noise_level:.1f}")
    print(f"原始班级人数: {real_class_sizes}")
    print(f"你的隐私保护结果: {[int(x) for x in user_private_data]}")
    
    # 评估用户的选择
    total_error = abs(sum(real_class_sizes) - sum(user_private_data))
    if total_error < 5:
        print("✅ 很好！你在隐私和效用之间找到了不错的平衡")
    elif total_error < 15:
        print("⚠️ 不错，但可能需要微调参数")
    else:
        print("❌ 噪音有点大，数据可用性降低了")
        
except:
    print("没关系，继续体验吧！")

# 总结
print("\n" + "="*60)
print("🎓 恭喜！你已经理解了差分隐私的基本概念：")
print("\n核心思想：")
print("✓ 给数据添加随机噪音")
print("✓ 保护个体隐私")
print("✓ 保持统计特性")
print("✓ 可调节保护强度")

print("\n实际应用：")
print("✓ 医疗数据共享")
print("✓ 人口普查发布")
print("✓ 企业数据分析")
print("✓ AI模型训练")

print("\n我们的完整框架就是把这个简单概念：")
print("🔄 自动化 + 工程化 + 标准化")
print("让你可以安全处理任何敏感数据！")

print("\n下一步可以尝试运行完整的框架：")
print("python 差分隐私.py") 