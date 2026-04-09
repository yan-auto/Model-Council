"""
密钥管理和加密工具

用于加密敏感信息如 API 密钥，防止数据库泄露时凭证完全暴露。
"""

from __future__ import annotations

import os
import base64
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("council.security")


class SecretManager:
    """敏感信息管理器"""
    
    _cipher = None
    _initialized = False
    
    @classmethod
    def _init_cipher(cls):
        """初始化加密器（仅一次）"""
        if cls._initialized:
            return
        
        # 从环境变量或配置文件读取密钥
        # 如果没有配置，使用 FERNET_KEY 或生成新的
        key = os.environ.get('COUNCIL_ENCRYPTION_KEY')
        
        if not key:
            # 开发环境：生成临时密钥（每次启动不同）
            logger.warning("[安全警告] COUNCIL_ENCRYPTION_KEY 未设置，使用临时加密密钥（仅适合开发环境）")
            key = Fernet.generate_key()
        else:
            # 生产环境：使用配置的密钥
            try:
                key = key.encode() if isinstance(key, str) else key
            except Exception as e:
                logger.error(f"加密密钥格式错误：{str(e)}")
                key = Fernet.generate_key()
        
        try:
            cls._cipher = Fernet(key)
            cls._initialized = True
        except Exception as e:
            logger.error(f"初始化加密器失败：{str(e)}")
            # 降级：不加密，直接使用
            cls._cipher = None
            cls._initialized = True
    
    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """加密敏感信息"""
        if not plaintext:
            return ""
        
        cls._init_cipher()
        
        if cls._cipher is None:
            # 降级模式：返回原文（应该告警）
            logger.warning("[安全警告] 加密器初始化失败，敏感信息未加密")
            return plaintext
        
        try:
            encrypted = cls._cipher.encrypt(plaintext.encode())
            # 返回 Base64 编码的密文，便于存储
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"加密失败：{str(e)}")
            return plaintext
    
    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """解密敏感信息"""
        if not ciphertext:
            return ""
        
        cls._init_cipher()
        
        if cls._cipher is None:
            logger.warning("[安全警告] 加密器初始化失败，无法解密")
            return ciphertext
        
        try:
            encrypted = base64.b64decode(ciphertext.encode())
            plaintext = cls._cipher.decrypt(encrypted)
            return plaintext.decode()
        except (InvalidToken, ValueError, Exception) as e:
            # 解密失败可能是：1. 密钥不对，2. 数据损坏，3. 该字段从前没加密
            logger.debug(f"解密失败（可能该字段从未加密）：{str(e)}")
            # 降级：假设这是未加密的明文
            return ciphertext
    
    @classmethod
    def mask_secret(cls, secret: str, visible_chars: int = 4) -> str:
        """掩盖敏感信息用于日志或 UI 展示
        
        例如：sk-xxx...xxxx
        """
        if not secret or len(secret) <= visible_chars * 2:
            return "***"
        
        return f"{secret[:visible_chars]}...{secret[-visible_chars:]}"
