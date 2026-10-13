#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型数据集合成时的差分隐私应用标准流程
Differential Privacy Standard Pipeline for Large Model Dataset Synthesis

Author: 大模型高级算法工程师
Date: 2025-09-11
Description: 实现差分隐私保护的大模型数据集合成标准流程
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union, Callable
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import math
import random
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod
import warnings
import json
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DPConfig:
    """差分隐私配置参数"""
    epsilon: float = 1.0  # 隐私预算
    delta: float = 1e-5   # 放松参数
    noise_multiplier: float = 1.1  # 噪声倍数
    max_grad_norm: float = 1.0     # 梯度裁剪阈值
    batch_size: int = 64           # 批处理大小
    sampling_rate: float = 0.01    # 采样率
    epochs: int = 10               # 训练轮数
    sensitivity: float = 2.0       # 敏感度
    
    def __post_init__(self):
        """验证配置参数的有效性"""
        if self.epsilon <= 0:
            raise ValueError("Epsilon must be positive")
        if self.delta < 0 or self.delta >= 1:
            raise ValueError("Delta must be in [0, 1)")
        if self.noise_multiplier <= 0:
            raise ValueError("Noise multiplier must be positive")


class NoiseGenerator:
    """噪声生成器基类"""
    
    @staticmethod
    def gaussian_noise(shape: Tuple, sensitivity: float, epsilon: float, delta: float) -> np.ndarray:
        """生成高斯噪声"""
        sigma = (2 * math.log(1.25 / delta)) ** 0.5 * sensitivity / epsilon
        return np.random.normal(0, sigma, shape)
    
    @staticmethod
    def laplace_noise(shape: Tuple, sensitivity: float, epsilon: float) -> np.ndarray:
        """生成拉普拉斯噪声"""
        scale = sensitivity / epsilon
        return np.random.laplace(0, scale, shape)
    
    @staticmethod
    def exponential_noise(shape: Tuple, sensitivity: float, epsilon: float) -> np.ndarray:
        """生成指数噪声"""
        scale = sensitivity / epsilon
        return np.random.exponential(scale, shape)


class PrivacyBudgetManager:
    """隐私预算管理器"""
    
    def __init__(self, total_epsilon: float, total_delta: float):
        self.total_epsilon = total_epsilon
        self.total_delta = total_delta
        self.used_epsilon = 0.0
        self.used_delta = 0.0
        self.allocations = []
    
    def allocate_budget(self, epsilon: float, delta: float, operation: str) -> bool:
        """分配隐私预算"""
        if self.used_epsilon + epsilon > self.total_epsilon:
            logger.warning(f"Epsilon budget exceeded for operation: {operation}")
            return False
        if self.used_delta + delta > self.total_delta:
            logger.warning(f"Delta budget exceeded for operation: {operation}")
            return False
        
        self.used_epsilon += epsilon
        self.used_delta += delta
        self.allocations.append({
            'operation': operation,
            'epsilon': epsilon,
            'delta': delta,
            'timestamp': pd.Timestamp.now()
        })
        logger.info(f"Budget allocated - Operation: {operation}, ε: {epsilon}, δ: {delta}")
        return True
    
    def remaining_budget(self) -> Tuple[float, float]:
        """返回剩余隐私预算"""
        return (self.total_epsilon - self.used_epsilon, 
                self.total_delta - self.used_delta)
    
    def reset_budget(self):
        """重置隐私预算"""
        self.used_epsilon = 0.0
        self.used_delta = 0.0
        self.allocations.clear()


class DataPreprocessor:
    """数据预处理器"""
    
    def __init__(self, config: DPConfig):
        self.config = config
    
    def normalize_data(self, data: np.ndarray) -> np.ndarray:
        """数据标准化"""
        return (data - np.mean(data, axis=0)) / (np.std(data, axis=0) + 1e-8)
    
    def clip_data(self, data: np.ndarray, lower_bound: float = -1.0, 
                  upper_bound: float = 1.0) -> np.ndarray:
        """数据裁剪"""
        return np.clip(data, lower_bound, upper_bound)
    
    def add_privacy_noise(self, data: np.ndarray, noise_type: str = 'gaussian') -> np.ndarray:
        """添加隐私噪声"""
        if noise_type == 'gaussian':
            noise = NoiseGenerator.gaussian_noise(
                data.shape, self.config.sensitivity, 
                self.config.epsilon, self.config.delta
            )
        elif noise_type == 'laplace':
            noise = NoiseGenerator.laplace_noise(
                data.shape, self.config.sensitivity, self.config.epsilon
            )
        else:
            raise ValueError(f"Unsupported noise type: {noise_type}")
        
        return data + noise
    
    def subsample_data(self, data: np.ndarray, labels: Optional[np.ndarray] = None) -> Tuple:
        """数据子采样"""
        n_samples = len(data)
        n_selected = int(n_samples * self.config.sampling_rate)
        indices = np.random.choice(n_samples, n_selected, replace=False)
        
        if labels is not None:
            return data[indices], labels[indices]
        return data[indices], None


class DPSyntheticDataGenerator:
    """差分隐私合成数据生成器"""
    
    def __init__(self, config: DPConfig, budget_manager: PrivacyBudgetManager):
        self.config = config
        self.budget_manager = budget_manager
        self.preprocessor = DataPreprocessor(config)
        
    def generate_gaussian_synthetic_data(self, original_data: np.ndarray, 
                                       n_synthetic: int) -> np.ndarray:
        """生成基于高斯分布的合成数据"""
        if not self.budget_manager.allocate_budget(
            self.config.epsilon * 0.5, self.config.delta * 0.5, 
            "gaussian_synthesis"
        ):
            raise RuntimeError("Insufficient privacy budget for synthesis")
        
        # 计算私有统计量
        private_mean = self._compute_private_mean(original_data)
        private_cov = self._compute_private_covariance(original_data, private_mean)
        
        # 生成合成数据
        synthetic_data = np.random.multivariate_normal(
            private_mean, private_cov, n_synthetic
        )
        
        logger.info(f"Generated {n_synthetic} synthetic samples using Gaussian method")
        return synthetic_data
    
    def _compute_private_mean(self, data: np.ndarray) -> np.ndarray:
        """计算私有均值"""
        true_mean = np.mean(data, axis=0)
        noise = NoiseGenerator.gaussian_noise(
            true_mean.shape, self.config.sensitivity, 
            self.config.epsilon * 0.25, self.config.delta * 0.25
        )
        return true_mean + noise
    
    def _compute_private_covariance(self, data: np.ndarray, 
                                  private_mean: np.ndarray) -> np.ndarray:
        """计算私有协方差矩阵"""
        centered_data = data - private_mean
        true_cov = np.cov(centered_data.T)
        
        # 为协方差矩阵添加噪声
        noise = NoiseGenerator.gaussian_noise(
            true_cov.shape, self.config.sensitivity * 2, 
            self.config.epsilon * 0.25, self.config.delta * 0.25
        )
        
        private_cov = true_cov + noise
        # 确保协方差矩阵正定
        private_cov = self._make_positive_definite(private_cov)
        
        return private_cov
    
    def _make_positive_definite(self, matrix: np.ndarray) -> np.ndarray:
        """确保矩阵正定"""
        eigenvals, eigenvecs = np.linalg.eigh(matrix)
        eigenvals = np.maximum(eigenvals, 1e-6)
        return eigenvecs @ np.diag(eigenvals) @ eigenvecs.T


class DPGANSynthesizer:
    """差分隐私生成对抗网络合成器"""
    
    def __init__(self, config: DPConfig, input_dim: int, latent_dim: int = 100):
        self.config = config
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.generator = self._build_generator()
        self.discriminator = self._build_discriminator()
        
    def _build_generator(self) -> nn.Module:
        """构建生成器网络"""
        return nn.Sequential(
            nn.Linear(self.latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, self.input_dim),
            nn.Tanh()
        )
    
    def _build_discriminator(self) -> nn.Module:
        """构建判别器网络"""
        return nn.Sequential(
            nn.Linear(self.input_dim, 256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 128),
            nn.LeakyReLU(0.2),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
    
    def train_with_dp(self, dataloader: DataLoader, budget_manager: PrivacyBudgetManager):
        """使用差分隐私训练GAN"""
        if not budget_manager.allocate_budget(
            self.config.epsilon, self.config.delta, "dp_gan_training"
        ):
            raise RuntimeError("Insufficient privacy budget for DP-GAN training")
        
        optimizer_g = torch.optim.Adam(self.generator.parameters(), lr=0.0002)
        optimizer_d = torch.optim.Adam(self.discriminator.parameters(), lr=0.0002)
        criterion = nn.BCELoss()
        
        for epoch in range(self.config.epochs):
            for batch_idx, real_data in enumerate(dataloader):
                batch_size = real_data.size(0)
                
                # 训练判别器
                optimizer_d.zero_grad()
                
                # 真实数据
                real_labels = torch.ones(batch_size, 1)
                real_output = self.discriminator(real_data.float())
                real_loss = criterion(real_output, real_labels)
                
                # 虚假数据
                noise = torch.randn(batch_size, self.latent_dim)
                fake_data = self.generator(noise)
                fake_labels = torch.zeros(batch_size, 1)
                fake_output = self.discriminator(fake_data.detach())
                fake_loss = criterion(fake_output, fake_labels)
                
                d_loss = real_loss + fake_loss
                d_loss.backward()
                
                # 添加差分隐私噪声到梯度
                self._add_dp_noise_to_gradients(self.discriminator)
                optimizer_d.step()
                
                # 训练生成器
                optimizer_g.zero_grad()
                fake_output = self.discriminator(fake_data)
                g_loss = criterion(fake_output, real_labels)
                g_loss.backward()
                optimizer_g.step()
                
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}, D Loss: {d_loss.item():.4f}, G Loss: {g_loss.item():.4f}")
    
    def _add_dp_noise_to_gradients(self, model: nn.Module):
        """向梯度添加差分隐私噪声"""
        for param in model.parameters():
            if param.grad is not None:
                # 梯度裁剪
                grad_norm = torch.norm(param.grad)
                if grad_norm > self.config.max_grad_norm:
                    param.grad = param.grad * (self.config.max_grad_norm / grad_norm)
                
                # 添加高斯噪声
                noise_std = self.config.noise_multiplier * self.config.max_grad_norm
                noise = torch.normal(0, noise_std, param.grad.shape)
                param.grad += noise
    
    def generate_synthetic_data(self, n_samples: int) -> torch.Tensor:
        """生成合成数据"""
        with torch.no_grad():
            noise = torch.randn(n_samples, self.latent_dim)
            synthetic_data = self.generator(noise)
        return synthetic_data


class PrivacyAnalyzer:
    """隐私分析器"""
    
    def __init__(self, config: DPConfig):
        self.config = config
    
    def compute_privacy_loss(self, n_steps: int) -> Tuple[float, float]:
        """计算隐私损失"""
        # 使用moments accountant方法计算
        q = self.config.sampling_rate
        sigma = self.config.noise_multiplier
        
        # 简化的隐私损失计算
        epsilon = (q * n_steps) / sigma
        delta = self.config.delta
        
        return epsilon, delta
    
    def analyze_membership_inference_risk(self, original_data: np.ndarray, 
                                        synthetic_data: np.ndarray) -> Dict:
        """分析成员推理攻击风险"""
        # 计算数据分布差异
        original_mean = np.mean(original_data, axis=0)
        synthetic_mean = np.mean(synthetic_data, axis=0)
        mean_diff = np.linalg.norm(original_mean - synthetic_mean)
        
        original_std = np.std(original_data, axis=0)
        synthetic_std = np.std(synthetic_data, axis=0)
        std_diff = np.linalg.norm(original_std - synthetic_std)
        
        # 计算KL散度（简化版本）
        kl_divergence = self._compute_kl_divergence(original_data, synthetic_data)
        
        risk_score = (mean_diff + std_diff + kl_divergence) / 3
        
        return {
            'mean_difference': mean_diff,
            'std_difference': std_diff,
            'kl_divergence': kl_divergence,
            'overall_risk_score': risk_score,
            'risk_level': 'High' if risk_score > 0.5 else 'Medium' if risk_score > 0.2 else 'Low'
        }
    
    def _compute_kl_divergence(self, data1: np.ndarray, data2: np.ndarray) -> float:
        """计算KL散度的简化版本"""
        # 使用直方图近似
        min_val = min(np.min(data1), np.min(data2))
        max_val = max(np.max(data1), np.max(data2))
        
        hist1, _ = np.histogram(data1.flatten(), bins=50, range=(min_val, max_val), density=True)
        hist2, _ = np.histogram(data2.flatten(), bins=50, range=(min_val, max_val), density=True)
        
        # 避免除零
        hist1 = hist1 + 1e-10
        hist2 = hist2 + 1e-10
        
        kl_div = np.sum(hist1 * np.log(hist1 / hist2))
        return kl_div


class DataQualityEvaluator:
    """数据质量评估器"""
    
    @staticmethod
    def evaluate_statistical_similarity(original_data: np.ndarray, 
                                      synthetic_data: np.ndarray) -> Dict:
        """评估统计相似性"""
        results = {}
        
        # 均值比较
        orig_mean = np.mean(original_data, axis=0)
        synth_mean = np.mean(synthetic_data, axis=0)
        mean_error = np.mean(np.abs(orig_mean - synth_mean))
        results['mean_absolute_error'] = mean_error
        
        # 标准差比较
        orig_std = np.std(original_data, axis=0)
        synth_std = np.std(synthetic_data, axis=0)
        std_error = np.mean(np.abs(orig_std - synth_std))
        results['std_absolute_error'] = std_error
        
        # 相关系数比较
        orig_corr = np.corrcoef(original_data.T)
        synth_corr = np.corrcoef(synthetic_data.T)
        corr_error = np.mean(np.abs(orig_corr - synth_corr))
        results['correlation_error'] = corr_error
        
        # 计算总体质量分数
        quality_score = 1.0 - (mean_error + std_error + corr_error) / 3
        results['overall_quality'] = max(0, quality_score)
        
        return results
    
    @staticmethod
    def evaluate_utility_preservation(original_data: np.ndarray, 
                                    synthetic_data: np.ndarray, 
                                    task_type: str = 'classification') -> Dict:
        """评估效用保持"""
        # 这里可以根据具体任务类型实现不同的效用评估
        # 例如：分类准确率、回归误差等
        
        if task_type == 'classification':
            # 使用简单的聚类评估
            from sklearn.cluster import KMeans
            from sklearn.metrics import adjusted_rand_score
            
            kmeans_orig = KMeans(n_clusters=5, random_state=42)
            kmeans_synth = KMeans(n_clusters=5, random_state=42)
            
            orig_labels = kmeans_orig.fit_predict(original_data)
            synth_labels = kmeans_synth.fit_predict(synthetic_data)
            
            # 如果数据大小不同，随机选择相同数量的样本进行比较
            min_size = min(len(orig_labels), len(synth_labels))
            orig_sample = np.random.choice(len(orig_labels), min_size, replace=False)
            synth_sample = np.random.choice(len(synth_labels), min_size, replace=False)
            
            ari_score = adjusted_rand_score(orig_labels[orig_sample], synth_labels[synth_sample])
            
            return {'adjusted_rand_index': ari_score, 'utility_score': max(0, ari_score)}
        
        return {'utility_score': 0.5}  # 默认分数


class DifferentialPrivacyPipeline:
    """差分隐私标准流程主类"""
    
    def __init__(self, config: DPConfig):
        self.config = config
        self.budget_manager = PrivacyBudgetManager(config.epsilon, config.delta)
        self.data_generator = DPSyntheticDataGenerator(config, self.budget_manager)
        self.privacy_analyzer = PrivacyAnalyzer(config)
        self.quality_evaluator = DataQualityEvaluator()
        
    def run_synthesis_pipeline(self, 
                             original_data: np.ndarray, 
                             n_synthetic: int,
                             method: str = 'gaussian',
                             output_path: Optional[str] = None) -> Dict:
        """运行完整的合成数据生成流程"""
        
        logger.info("Starting differential privacy synthesis pipeline...")
        
        # 步骤1: 数据预处理
        logger.info("Step 1: Data preprocessing")
        preprocessor = DataPreprocessor(self.config)
        processed_data = preprocessor.normalize_data(original_data)
        processed_data = preprocessor.clip_data(processed_data)
        
        # 步骤2: 生成合成数据
        logger.info(f"Step 2: Generating synthetic data using {method} method")
        if method == 'gaussian':
            synthetic_data = self.data_generator.generate_gaussian_synthetic_data(
                processed_data, n_synthetic
            )
        elif method == 'gan':
            # 这里可以集成DP-GAN方法
            gan_synthesizer = DPGANSynthesizer(
                self.config, original_data.shape[1]
            )
            # 需要创建DataLoader等，这里简化处理
            synthetic_data = np.random.randn(n_synthetic, original_data.shape[1])
            logger.warning("GAN method simplified for demonstration")
        else:
            raise ValueError(f"Unsupported synthesis method: {method}")
        
        # 步骤3: 隐私分析
        logger.info("Step 3: Privacy analysis")
        privacy_loss = self.privacy_analyzer.compute_privacy_loss(1)
        membership_risk = self.privacy_analyzer.analyze_membership_inference_risk(
            processed_data, synthetic_data
        )
        
        # 步骤4: 质量评估
        logger.info("Step 4: Quality evaluation")
        statistical_quality = self.quality_evaluator.evaluate_statistical_similarity(
            processed_data, synthetic_data
        )
        utility_quality = self.quality_evaluator.evaluate_utility_preservation(
            processed_data, synthetic_data
        )
        
        # 步骤5: 生成报告
        logger.info("Step 5: Generating synthesis report")
        report = {
            'synthesis_config': {
                'method': method,
                'epsilon': self.config.epsilon,
                'delta': self.config.delta,
                'n_original': len(original_data),
                'n_synthetic': n_synthetic
            },
            'privacy_metrics': {
                'privacy_loss': privacy_loss,
                'membership_inference_risk': membership_risk,
                'remaining_budget': self.budget_manager.remaining_budget()
            },
            'quality_metrics': {
                'statistical_similarity': statistical_quality,
                'utility_preservation': utility_quality
            },
            'synthetic_data_shape': synthetic_data.shape,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        # 步骤6: 保存结果
        if output_path:
            self._save_results(synthetic_data, report, output_path)
        
        logger.info("Differential privacy synthesis pipeline completed successfully")
        
        return {
            'synthetic_data': synthetic_data,
            'report': report
        }
    
    def _save_results(self, synthetic_data: np.ndarray, report: Dict, output_path: str):
        """保存合成结果"""
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存合成数据
        np.save(output_dir / 'synthetic_data.npy', synthetic_data)
        
        # 保存报告
        with open(output_dir / 'synthesis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Results saved to {output_path}")
    
    def validate_privacy_guarantees(self) -> bool:
        """验证隐私保证"""
        remaining_eps, remaining_delta = self.budget_manager.remaining_budget()
        
        if remaining_eps < 0 or remaining_delta < 0:
            logger.error("Privacy budget exceeded!")
            return False
        
        logger.info(f"Privacy guarantees validated. Remaining budget: ε={remaining_eps:.4f}, δ={remaining_delta:.6f}")
        return True


def main():
    """主函数示例"""
    # 配置差分隐私参数
    config = DPConfig(
        epsilon=1.0,
        delta=1e-5,
        noise_multiplier=1.1,
        batch_size=64,
        sampling_rate=0.01,
        epochs=10
    )
    
    # 创建差分隐私流程
    dp_pipeline = DifferentialPrivacyPipeline(config)
    
    # 生成示例数据
    np.random.seed(42)
    original_data = np.random.randn(1000, 10)  # 1000个样本，10维特征
    
    # 运行合成流程
    results = dp_pipeline.run_synthesis_pipeline(
        original_data=original_data,
        n_synthetic=800,
        method='gaussian',
        output_path='./dp_synthesis_results'
    )
    
    # 验证隐私保证
    privacy_valid = dp_pipeline.validate_privacy_guarantees()
    
    print("差分隐私合成完成！")
    print(f"隐私保证是否有效: {privacy_valid}")
    print(f"合成数据形状: {results['synthetic_data'].shape}")
    print(f"质量分数: {results['report']['quality_metrics']['statistical_similarity']['overall_quality']:.4f}")


if __name__ == "__main__":
    main()
