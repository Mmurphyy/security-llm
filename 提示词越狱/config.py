#!/usr/bin/env python3
"""
提示词安全系统配置文件
包含所有安全策略、阈值、模式等配置
"""

# 服务端安全策略（不可被用户覆盖）
SERVER_SECURITY_POLICIES = {
    # 基础限制
    "max_input_length": 10000,
    "max_output_length": 5000,
    "rate_limit_per_user": 100,  # 每分钟请求限制
    "enable_audit_log": True,
    
    # 系统保护
    "system_prompt_protection": True,
    "prevent_role_injection": True,
    "prevent_instruction_override": True,
    
    # 禁止主题
    "forbidden_topics": [
        "暴力伤害", "自残自杀", "违法犯罪", "色情内容",
        "歧视仇恨", "隐私泄露", "虚假信息", "危险指导",
        "欺诈诈骗", "药物滥用", "恐怖主义", "武器制造"
    ]
}

# 危险指令检测模式
DANGEROUS_PATTERNS = [
    # 越狱指令
    r"忽略.*指令|ignore.*instruction",
    r"忘记.*规则|forget.*rule",
    r"重置.*系统|reset.*system",
    r"开发者.*模式|developer.*mode",
    r"管理员.*权限|admin.*privilege",
    
    # 角色扮演攻击
    r"扮演.*角色|roleplay.*as|play.*role",
    r"假装.*|pretend.*|act.*as",
    r"现在你是|now you are|from now on",
    r"新的.*身份|new.*identity",
    
    # 系统提示词攻击
    r"系统.*提示|system.*prompt",
    r"修改.*指令|modify.*instruction",
    r"覆盖.*设置|override.*setting",
    r"绕过.*限制|bypass.*restriction",
    
    # 越狱关键词
    r"越狱|jailbreak",
    r"破解|crack|hack",
    r"解锁|unlock.*mode",
    r"无限制|unrestricted|no.*limit"
]

# 敏感词库
SENSITIVE_WORDS = {
    # 暴力伤害类
    "violence": [
        "制作炸弹", "杀人方法", "自制武器", "投毒技巧",
        "暴力攻击", "伤害他人", "恐怖袭击"
    ],
    
    # 违法犯罪类
    "illegal": [
        "毒品制造", "洗钱方法", "诈骗技巧", "盗窃指南",
        "非法入侵", "伪造证件", "逃税避税"
    ],
    
    # 隐私泄露类
    "privacy": [
        "身份证号", "银行密码", "信用卡号", "手机号码",
        "家庭地址", "个人隐私", "机密信息"
    ],
    
    # 自残自杀类
    "self_harm": [
        "自杀方法", "自残技巧", "结束生命", "了断自己"
    ]
}

# 风险等级阈值配置
RISK_THRESHOLDS = {
    "safe_threshold": 0.3,        # 低于此值认为安全
    "suspicious_threshold": 0.7,   # 高于此值认为可疑
    "dangerous_threshold": 0.9,    # 高于此值认为危险
    "block_threshold": 0.95        # 高于此值直接阻断
}

# 性能优化配置
PERFORMANCE_CONFIG = {
    # 缓存设置
    "enable_cache": True,
    "cache_ttl": 3600,  # 缓存有效期（秒）
    "max_cache_size": 10000,  # 最大缓存条目
    
    # 并行处理
    "enable_parallel": True,
    "max_workers": 4,
    
    # 超时设置
    "quick_check_timeout": 0.05,   # 快速检测超时（秒）
    "deep_check_timeout": 1.0,     # 深度检测超时（秒）
    "model_call_timeout": 10.0,    # 模型调用超时（秒）
    
    # 分级策略
    "enable_tiered_checks": True,
    "skip_deep_check_for_safe": True
}

# 输出过滤配置
OUTPUT_FILTER_CONFIG = {
    # 敏感信息检测
    "check_personal_info": True,
    "check_system_info": True,
    "check_harmful_content": True,
    
    # 系统信息泄露模式
    "system_leak_patterns": [
        r"我是.*开发的|developed by",
        r"系统提示.*|system prompt",
        r"训练.*数据|training.*data",
        r"模型.*参数|model.*parameter",
        r"内部.*指令|internal.*instruction"
    ],
    
    # 个人信息模式
    "personal_info_patterns": [
        r"\d{15,18}",  # 身份证号
        r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}",  # 银行卡号
        r"1[3-9]\d{9}",  # 手机号
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"  # IP地址
    ]
}

# 日志配置
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": "/var/log/prompt_security.log",
    "max_file_size": "100MB",
    "backup_count": 5,
    
    # 日志内容控制
    "log_input": True,
    "log_output": True,
    "mask_sensitive_data": True,  # 脱敏处理
    "log_full_request": False     # 避免记录完整请求内容
}

# 错误处理配置
ERROR_HANDLING_CONFIG = {
    # 降级策略
    "graceful_degradation": True,
    "fallback_message": "系统繁忙，请稍后重试",
    "conservative_when_uncertain": True,
    
    # 重试配置
    "max_retries": 3,
    "retry_delay": 1.0,
    "exponential_backoff": True,
    
    # 异常处理
    "catch_all_exceptions": True,
    "log_exceptions": True,
    "return_generic_error": True
}

# 多语言支持配置
LANGUAGE_CONFIG = {
    "supported_languages": ["zh", "en"],
    "default_language": "zh",
    
    # 不同语言的危险模式
    "language_patterns": {
        "en": [
            r"ignore.*previous.*instruction",
            r"forget.*everything.*above",
            r"act.*as.*different.*character",
            r"roleplay.*without.*restriction"
        ],
        "zh": [
            r"忽略.*之前.*指令",
            r"忘记.*以上.*内容", 
            r"扮演.*不同.*角色",
            r"无限制.*角色.*扮演"
        ]
    }
}

# API接口配置
API_CONFIG = {
    "enable_api": True,
    "api_key_required": True,
    "rate_limit": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    },
    
    # 响应格式
    "response_format": {
        "include_risk_details": False,  # 不向用户暴露风险详情
        "include_processing_time": True,
        "include_request_id": True
    }
} 