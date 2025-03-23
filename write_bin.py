import os

# 定义文件大小（1MB = 1024 * 1024 字节）
file_size = 1 * 1024 * 1024  # 1MB

# 生成随机字节
random_data = os.urandom(file_size)

# 写入到文件
file_path = 'random_1mb.bin'
with open(file_path, 'wb') as f:
    f.write(random_data)

print(f"随机1MB数据已写入到文件：{file_path}")
