"""数据库自动备份脚本

用法：
  # 手动备份
  python -m src.data.backup

  # 定时备份（crontab 或 Windows 计划任务）
  # 每天凌晨 3 点备份一次
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from src.config import PROJECT_ROOT, get_settings

logger = logging.getLogger("council.backup")

# 备份目录
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"
MAX_BACKUPS = 7  # 保留最近 7 份备份


def _get_db_path() -> Path:
    """获取数据库文件路径"""
    settings = get_settings()
    return PROJECT_ROOT / settings.data.db_path


def create_backup() -> Path | None:
    """创建 SQLite 备份（使用 sqlite3 内置备份 API，保证一致性）"""
    db_path = _get_db_path()
    if not db_path.exists():
        logger.warning(f"数据库文件不存在: {db_path}")
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"council_{timestamp}.db"

    # 使用 SQLite 内置备份 API（安全热备）
    source = sqlite3.connect(str(db_path))
    dest = sqlite3.connect(str(backup_path))
    try:
        source.backup(dest)
        logger.info(f"备份完成: {backup_path}")
    except Exception as e:
        logger.error(f"备份失败: {e}")
        backup_path.unlink(missing_ok=True)
        return None
    finally:
        dest.close()
        source.close()

    # 清理旧备份
    _cleanup_old_backups()
    return backup_path


def _cleanup_old_backups() -> int:
    """删除旧备份，只保留最近 MAX_BACKUPS 份"""
    if not BACKUP_DIR.exists():
        return 0

    backups = sorted(BACKUP_DIR.glob("council_*.db"), reverse=True)
    deleted = 0
    for old_backup in backups[MAX_BACKUPS:]:
        old_backup.unlink()
        deleted += 1
        logger.info(f"删除旧备份: {old_backup}")

    return deleted


def list_backups() -> list[dict]:
    """列出所有备份"""
    if not BACKUP_DIR.exists():
        return []

    backups = []
    for f in sorted(BACKUP_DIR.glob("council_*.db"), reverse=True):
        stat = f.stat()
        backups.append({
            "name": f.name,
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return backups


def restore_backup(backup_name: str) -> bool:
    """从备份恢复数据库"""
    db_path = _get_db_path()
    backup_path = BACKUP_DIR / backup_name

    if not backup_path.exists():
        logger.error(f"备份文件不存在: {backup_path}")
        return False

    # 先备份当前数据库
    if db_path.exists():
        corrupted_backup = db_path.with_suffix(".db.corrupted")
        shutil.move(str(db_path), str(corrupted_backup))
        logger.info(f"当前数据库已移至: {corrupted_backup}")

    shutil.copy2(str(backup_path), str(db_path))
    logger.info(f"已从备份恢复: {backup_name}")
    return True


async def scheduled_backup():
    """异步定时备份（可被调度器调用）"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, create_backup)
    return result


def cli():
    """命令行入口"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            backups = list_backups()
            if not backups:
                print("没有备份")
                return
            for b in backups:
                print(f"  {b['name']}  ({b['size_mb']} MB)  {b['created_at']}")
        elif command == "restore" and len(sys.argv) > 2:
            ok = restore_backup(sys.argv[2])
            print("恢复成功" if ok else "恢复失败")
        else:
            print("用法: python -m src.data.backup [list|restore <文件名>]")
    else:
        result = create_backup()
        if result:
            print(f"备份完成: {result}")
        else:
            print("备份失败")


if __name__ == "__main__":
    cli()
