#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型差分隐私训练框架
Differential Privacy Training Framework for Large Language Models

专门处理自然语言数据的差分隐私保护
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
import numpy as np
import math
import random
import logging
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from transformers import AutoTokenizer, AutoModel
import re
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DPLMConfig:
    """大模型差分隐私配置"""
    epsilon: float = 1.0                    # 隐私预算
    delta: float = 1e-5                     # 失败概率
    max_grad_norm: float = 1.0               # 梯度裁剪阈值
    noise_multiplier: float = 1.1            # 噪声乘数
    batch_size: int = 32                     # 批处理大小
    max_sequence_length: int = 512           # 最大序列长度
    vocab_size: int = 50000                  # 词汇表大小
    learning_rate: float = 2e-5              # 学习率
    epochs: int = 3                          # 训练轮数
    text_privacy_level: str = "medium"       # 文本隐私级别: low/medium/high
    
    def __post_init__(self):
        """自动计算噪声乘数"""
        if self.noise_multiplier is None:
            self.noise_multiplier = math.sqrt(2 * math.log(1.25 / self.delta)) / self.epsilon


class TextPrivacyProtector:
    """文本隐私保护器"""
    
    def __init__(self, config: DPLMConfig):
        self.config = config
        self.synonym_dict = self._load_synonyms()
        self.sensitive_patterns = self._load_sensitive_patterns()
        
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """加载同义词词典（简化版本）"""
        # 实际应用中应该加载完整的同义词词典
        return {
            "医生": ["医师", "大夫", "医务人员", "临床医生"],
            "患者": ["病人", "就诊者", "医疗对象", "病患"],
            "诊断": ["判断", "评估", "检查结果", "医学评价"],
            "治疗": ["医治", "诊疗", "康复", "医疗"],
            "姓名": ["名字", "称呼", "代号", "标识"],
            "地址": ["住址", "位置", "居住地", "所在地"],
            # 可以扩展更多同义词对
        }
    
    def _load_sensitive_patterns(self) -> List[str]:
        """加载敏感信息模式"""
        return [
            r'\b1[3-9]\d{9}\b',         # 手机号
            r'\b\d{15}|\d{18}\b',       # 身份证号（15位或18位）
            r'\b\d{4}-\d{2}-\d{2}\b',   # 日期
            r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',  # 邮箱
            r'[张王李赵刘陈杨黄周吴徐孙朱马胡郭林何高梁郑罗宋谢唐韩曹许邓萧冯曾程蔡彭潘袁于董余苏叶吕魏蒋田杜丁沈姜范江傅钟卢汪戴崔任陆廖姚方金邱夏谭韦贾邹石熊孟秦阎薛侯雷白龙段郝孔邵史毛常万顾赖武康贺严尹钱施牛洪龚][一-龥]{1,2}',  # 中文姓名
            r'某某',                     # 匿名化标识
        ]
    
    def privatize_text(self, text: str, epsilon_portion: float = 0.1) -> str:
        """对文本进行隐私保护"""
        if self.config.text_privacy_level == "low":
            return self._light_privatization(text, epsilon_portion)
        elif self.config.text_privacy_level == "medium":
            return self._medium_privatization(text, epsilon_portion)
        else:  # high
            return self._strong_privatization(text, epsilon_portion)
    
    def _light_privatization(self, text: str, epsilon: float) -> str:
        """轻度隐私保护：主要替换敏感实体"""
        # 替换明显的敏感信息
        for pattern in self.sensitive_patterns:
            text = re.sub(pattern, '[REDACTED]', text)
        
        return text
    
    def _medium_privatization(self, text: str, epsilon: float) -> str:
        """中度隐私保护：同义词替换 + 敏感信息替换"""
        # 首先进行轻度保护
        text = self._light_privatization(text, epsilon)
        
        # 同义词替换
        words = text.split()
        privatized_words = []
        
        for word in words:
            if word in self.synonym_dict and random.random() < self._get_replacement_prob(epsilon):
                # 使用指数机制选择同义词
                synonyms = self.synonym_dict[word]
                replacement = self._exponential_mechanism_select(synonyms, word, epsilon)
                privatized_words.append(replacement)
            else:
                privatized_words.append(word)
        
        return ' '.join(privatized_words)
    
    def _strong_privatization(self, text: str, epsilon: float) -> str:
        """强度隐私保护：词汇扰动 + 句式重构"""
        # 中度保护
        text = self._medium_privatization(text, epsilon)
        
        # 词汇级别扰动
        text = self._lexical_perturbation(text, epsilon * 0.3)
        
        # 句法重构
        text = self._syntactic_restructuring(text, epsilon * 0.2)
        
        return text
    
    def _get_replacement_prob(self, epsilon: float) -> float:
        """计算替换概率"""
        return min(0.3, epsilon / self.config.epsilon)
    
    def _exponential_mechanism_select(self, candidates: List[str], original: str, epsilon: float) -> str:
        """使用指数机制选择替换词"""
        if not candidates:
            return original
        
        # 简化的相似度计算（实际应用中应使用语义相似度）
        scores = [1.0 / (1 + abs(len(candidate) - len(original))) for candidate in candidates]
        
        # 指数机制权重
        weights = [math.exp(epsilon * score / 2) for score in scores]
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        
        # 随机选择
        return np.random.choice(candidates, p=probabilities)
    
    def _lexical_perturbation(self, text: str, epsilon: float) -> str:
        """词汇级别扰动"""
        words = text.split()
        perturbed_words = []
        
        for word in words:
            if random.random() < epsilon and len(word) > 3:
                # 字符级别的轻微扰动
                chars = list(word)
                if len(chars) > 4:
                    # 随机交换相邻字符
                    idx = random.randint(1, len(chars) - 2)
                    chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
                perturbed_words.append(''.join(chars))
            else:
                perturbed_words.append(word)
        
        return ' '.join(perturbed_words)
    
    def _syntactic_restructuring(self, text: str, epsilon: float) -> str:
        """句法重构（简化版本）"""
        sentences = text.split('。')
        restructured = []
        
        for sentence in sentences:
            if random.random() < epsilon and '，' in sentence:
                # 简单的语序调整
                parts = sentence.split('，')
                if len(parts) >= 2:
                    random.shuffle(parts)
                    sentence = '，'.join(parts)
            restructured.append(sentence)
        
        return '。'.join(restructured)


class DPLanguageModelTrainer:
    """差分隐私语言模型训练器"""
    
    def __init__(self, model: nn.Module, config: DPLMConfig):
        self.model = model
        self.config = config
        self.text_protector = TextPrivacyProtector(config)
        self.privacy_accountant = PrivacyAccountant(config)
        
    def compute_per_sample_gradients(self, batch: Dict[str, torch.Tensor]) -> List[List[torch.Tensor]]:
        """计算每个样本的梯度"""
        per_sample_grads = []
        
        # 获取输入
        input_ids = batch['input_ids']
        attention_mask = batch['attention_mask']
        labels = batch['labels']
        
        batch_size = input_ids.size(0)
        
        for i in range(batch_size):
            # 单样本输入
            sample_input = {
                'input_ids': input_ids[i:i+1],
                'attention_mask': attention_mask[i:i+1],
                'labels': labels[i:i+1]
            }
            
            # 前向传播
            outputs = self.model(**sample_input)
            loss = outputs.loss
            
            # 计算梯度
            self.model.zero_grad()
            loss.backward()
            
            # 收集梯度
            sample_grads = []
            for param in self.model.parameters():
                if param.grad is not None:
                    sample_grads.append(param.grad.clone())
                else:
                    sample_grads.append(torch.zeros_like(param))
            
            per_sample_grads.append(sample_grads)
        
        return per_sample_grads
    
    def clip_gradients(self, per_sample_grads: List[List[torch.Tensor]]) -> List[List[torch.Tensor]]:
        """按L2范数裁剪梯度"""
        clipped_grads = []
        
        for sample_grads in per_sample_grads:
            # 计算L2范数
            grad_norm = torch.norm(torch.cat([g.flatten() for g in sample_grads]))
            
            # 裁剪
            if grad_norm > self.config.max_grad_norm:
                clip_factor = self.config.max_grad_norm / grad_norm
                clipped_sample_grads = [g * clip_factor for g in sample_grads]
            else:
                clipped_sample_grads = sample_grads
            
            clipped_grads.append(clipped_sample_grads)
        
        return clipped_grads
    
    def add_dp_noise(self, clipped_grads: List[List[torch.Tensor]]) -> List[torch.Tensor]:
        """添加差分隐私噪声"""
        # 计算平均梯度
        num_samples = len(clipped_grads)
        num_params = len(clipped_grads[0])
        
        avg_grads = []
        for param_idx in range(num_params):
            param_grads = [sample_grads[param_idx] for sample_grads in clipped_grads]
            avg_grad = torch.mean(torch.stack(param_grads), dim=0)
            avg_grads.append(avg_grad)
        
        # 添加高斯噪声
        noisy_grads = []
        noise_std = self.config.noise_multiplier * self.config.max_grad_norm / num_samples
        
        for grad in avg_grads:
            noise = torch.normal(0, noise_std, grad.shape, device=grad.device)
            noisy_grad = grad + noise
            noisy_grads.append(noisy_grad)
        
        return noisy_grads
    
    def train_step(self, batch: Dict[str, torch.Tensor]) -> float:
        """执行一个训练步骤"""
        # 1. 计算每样本梯度
        per_sample_grads = self.compute_per_sample_gradients(batch)
        
        # 2. 裁剪梯度
        clipped_grads = self.clip_gradients(per_sample_grads)
        
        # 3. 添加差分隐私噪声
        noisy_grads = self.add_dp_noise(clipped_grads)
        
        # 4. 更新模型参数
        with torch.no_grad():
            for param, noisy_grad in zip(self.model.parameters(), noisy_grads):
                param -= self.config.learning_rate * noisy_grad
        
        # 5. 更新隐私会计
        self.privacy_accountant.update(batch_size=len(batch['input_ids']))
        
        # 计算损失用于监控
        with torch.no_grad():
            outputs = self.model(**batch)
            loss = outputs.loss.item()
        
        return loss
    
    def train(self, dataloader: DataLoader) -> Dict:
        """训练模型"""
        self.model.train()
        total_loss = 0
        num_batches = 0
        
        logger.info(f"开始差分隐私训练，epsilon={self.config.epsilon}")
        
        for epoch in range(self.config.epochs):
            epoch_loss = 0
            epoch_batches = 0
            
            for batch_idx, batch in enumerate(dataloader):
                # 移动数据到设备
                batch = {k: v.to(self.model.device) if hasattr(v, 'to') else v 
                        for k, v in batch.items()}
                
                # 训练步骤
                loss = self.train_step(batch)
                
                epoch_loss += loss
                epoch_batches += 1
                total_loss += loss
                num_batches += 1
                
                # 检查隐私预算
                if self.privacy_accountant.is_budget_exhausted():
                    logger.warning("隐私预算已耗尽，停止训练")
                    break
                
                if batch_idx % 100 == 0:
                    current_epsilon, current_delta = self.privacy_accountant.get_current_privacy_cost()
                    logger.info(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss:.4f}, "
                              f"Privacy: ε={current_epsilon:.4f}, δ={current_delta:.6f}")
            
            avg_epoch_loss = epoch_loss / epoch_batches if epoch_batches > 0 else 0
            logger.info(f"Epoch {epoch} completed, Average Loss: {avg_epoch_loss:.4f}")
            
            if self.privacy_accountant.is_budget_exhausted():
                break
        
        final_epsilon, final_delta = self.privacy_accountant.get_current_privacy_cost()
        
        return {
            'average_loss': total_loss / num_batches if num_batches > 0 else 0,
            'final_privacy_cost': (final_epsilon, final_delta),
            'total_batches': num_batches
        }


class PrivacyAccountant:
    """隐私会计管理器"""
    
    def __init__(self, config: DPLMConfig):
        self.config = config
        self.steps = 0
        self.total_samples_processed = 0
        
    def update(self, batch_size: int):
        """更新隐私消耗"""
        self.steps += 1
        self.total_samples_processed += batch_size
    
    def get_current_privacy_cost(self) -> Tuple[float, float]:
        """计算当前隐私消耗"""
        # 使用简化的moments accountant方法
        q = self.config.batch_size / 10000  # 假设数据集大小为10000
        sigma = self.config.noise_multiplier
        
        # 简化的隐私损失计算
        epsilon = (q * self.steps * math.log(1 + q * (math.exp(1/sigma**2) - 1))) / sigma**2
        delta = self.config.delta
        
        return epsilon, delta
    
    def is_budget_exhausted(self) -> bool:
        """检查隐私预算是否已耗尽"""
        current_epsilon, current_delta = self.get_current_privacy_cost()
        return (current_epsilon >= self.config.epsilon or 
                current_delta >= self.config.delta)


class TextDataset(Dataset):
    """文本数据集"""
    
    def __init__(self, texts: List[str], tokenizer, max_length: int = 512, 
                 text_protector: Optional[TextPrivacyProtector] = None):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.text_protector = text_protector
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        
        # 应用文本隐私保护
        if self.text_protector:
            text = self.text_protector.privatize_text(text)
        
        # 分词和编码
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': encoding['input_ids'].squeeze()  # 对于语言模型，标签就是输入
        }


class DPTextGenerator:
    """差分隐私文本生成器"""
    
    def __init__(self, model: nn.Module, tokenizer, epsilon: float = 1.0):
        self.model = model
        self.tokenizer = tokenizer
        self.epsilon = epsilon
    
    def generate_with_dp(self, prompt: str, max_length: int = 100, 
                        temperature: float = 1.0) -> str:
        """使用差分隐私生成文本"""
        self.model.eval()
        
        # 编码输入
        input_ids = self.tokenizer.encode(prompt, return_tensors='pt')
        
        generated_tokens = []
        current_input = input_ids
        
        with torch.no_grad():
            for _ in range(max_length):
                # 模型前向传播
                outputs = self.model(current_input)
                logits = outputs.logits[0, -1, :]  # 获取最后一个位置的logits
                
                # 温度缩放
                logits = logits / temperature
                
                # 使用指数机制进行私有采样
                next_token_id = self._exponential_mechanism_sampling(logits)
                
                # 停止条件
                if next_token_id == self.tokenizer.eos_token_id:
                    break
                
                generated_tokens.append(next_token_id)
                
                # 更新输入
                next_token = torch.tensor([[next_token_id]])
                current_input = torch.cat([current_input, next_token], dim=1)
        
        # 解码生成的文本
        generated_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        return generated_text
    
    def _exponential_mechanism_sampling(self, logits: torch.Tensor) -> int:
        """使用指数机制进行采样"""
        # 转换为概率
        probabilities = F.softmax(logits, dim=-1)
        
        # 指数机制权重
        exp_weights = torch.exp(self.epsilon * probabilities / 2)
        
        # 归一化
        exp_weights = exp_weights / torch.sum(exp_weights)
        
        # 采样
        token_id = torch.multinomial(exp_weights, 1).item()
        return token_id


def main():
    """主函数示例"""
    # 配置
    config = DPLMConfig(
        epsilon=1.0,
        delta=1e-5,
        max_grad_norm=1.0,
        noise_multiplier=1.1,
        batch_size=16,
        epochs=2,
        text_privacy_level="medium"
    )
    
    # 模拟数据
    sample_texts = [
        "患者张三，男，35岁，因胸痛入院。",
        "李医生建议进行心电图检查。",
        "诊断结果显示心肌梗塞的可能性较大。",
        "建议立即进行介入治疗。",
        # 更多文本...
    ]
    
    logger.info("开始差分隐私大模型训练示例")
    
    # 初始化tokenizer（这里使用伪代码，实际需要真实的tokenizer）
    class MockTokenizer:
        def __init__(self):
            self.eos_token_id = 0
            
        def encode(self, text, return_tensors=None):
            # 简化的编码
            return torch.randint(1, 1000, (1, 10))
        
        def __call__(self, text, **kwargs):
            return {
                'input_ids': torch.randint(1, 1000, (1, config.max_sequence_length)),
                'attention_mask': torch.ones(1, config.max_sequence_length)
            }
        
        def decode(self, tokens, skip_special_tokens=False):
            return "生成的文本示例"
    
    tokenizer = MockTokenizer()
    
    # 创建数据集
    text_protector = TextPrivacyProtector(config)
    dataset = TextDataset(sample_texts, tokenizer, config.max_sequence_length, text_protector)
    dataloader = DataLoader(dataset, batch_size=config.batch_size, shuffle=True)
    
    # 创建模型（简化版本）
    class SimpleLanguageModel(nn.Module):
        def __init__(self, vocab_size=1000, hidden_size=256):
            super().__init__()
            self.embedding = nn.Embedding(vocab_size, hidden_size)
            self.transformer = nn.TransformerEncoder(
                nn.TransformerEncoderLayer(hidden_size, nhead=8, batch_first=True),
                num_layers=2
            )
            self.lm_head = nn.Linear(hidden_size, vocab_size)
            self.device = torch.device('cpu')
            
        def forward(self, input_ids, attention_mask=None, labels=None):
            x = self.embedding(input_ids)
            x = self.transformer(x)
            logits = self.lm_head(x)
            
            loss = None
            if labels is not None:
                loss_fn = nn.CrossEntropyLoss()
                loss = loss_fn(logits.view(-1, logits.size(-1)), labels.view(-1))
            
            return type('ModelOutput', (), {'logits': logits, 'loss': loss})()
    
    model = SimpleLanguageModel()
    
    # 训练
    trainer = DPLanguageModelTrainer(model, config)
    results = trainer.train(dataloader)
    
    logger.info(f"训练完成！")
    logger.info(f"平均损失: {results['average_loss']:.4f}")
    logger.info(f"最终隐私消耗: ε={results['final_privacy_cost'][0]:.4f}, "
               f"δ={results['final_privacy_cost'][1]:.6f}")
    
    # 文本生成示例
    generator = DPTextGenerator(model, tokenizer, epsilon=0.5)
    generated_text = generator.generate_with_dp("医生建议", max_length=50)
    logger.info(f"生成的文本: {generated_text}")


if __name__ == "__main__":
    main() 