import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import colorlog

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../."))
def setup_logging(log_dir=f'{project_dir}/logs', log_level=logging.INFO, log_file='app.log'):
    """
    设置日志配置，使用 colorlog 实现彩色控制台输出
    
    Args:
        log_dir: 日志文件目录
        log_level: 日志级别
        log_file: 日志文件名
    
    Returns:
        logging.Logger: 配置好的根日志记录器
    """
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建彩色控制台处理器
    console_handler = colorlog.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(log_level)
    console_format = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_format)
    
    # 创建文件处理器（带日志轮换）
    log_file_path = os.path.join(log_dir, log_file)
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # 添加处理器到根日志记录器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # 返回根日志记录器
    return root_logger

def get_logger(name, log_level=None):
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别，如果提供则覆盖默认级别
    
    Returns:
        logging.Logger: 指定名称的日志记录器
    """
    logger = logging.getLogger(name)
    if log_level is not None:
        logger.setLevel(log_level)
    return logger

# 如果直接运行此模块，则设置日志并进行测试
if __name__ == "__main__":
    setup_logging(log_level=logging.DEBUG)
    logger = get_logger(__name__)
    
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.critical("这是一条严重错误日志")
    
    print("\n日志配置测试完成，请检查控制台输出和logs目录下的日志文件。")