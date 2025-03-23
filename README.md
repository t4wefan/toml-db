# TomlDB

`TomlDB` 是一个基于 TOML 文件的简单数据库库，它支持 `JSON` 和 `pickle/dill` 序列化，并可以选择将大型对象存储到文件系统中。该库提供了线程安全的读写操作，确保多个进程可以安全地访问同一个数据库文件。

## 安装

推荐使用`uv`在已经初始化的项目中

```bash
uv add t4wefan-tomldb
```

或者

```bash
pip install t4wefan-tomldb
```

## 功能描述

## 功能

- **存储和检索数据**：使用 `set` 方法存储键值对，使用 `get` 方法检索数据。
- **序列化支持**：自动选择 `JSON` 或 `pickle` 序列化方法存储数据。
- **文件系统存储**：对于大型或无法 JSON 序列化的对象，可以选择使用文件系统存储。
- **线程安全**：使用文件锁，确保多线程和多进程的安全访问。
- **基本数据库操作**：支持 `set`、`get`、`delete`、`exists` 和 `keys` 操作。

## 使用示例

```python
from tomldb import TomlDB

# 创建一个数据库实例，选择是否将大型对象存储到文件系统
db = TomlDB() # 默认 use_pickle=False, store_to_fs=True，无法直接原生存进toml的对象会转为dill然后存入本地的文件，可以通过参数存为pickle

# 存储一个复杂的字典
db.set('user', {'name': 'Alice', 'age': 30, 'emails': ['alice@example.com', 'a.smith@example.com']})

# 检查键是否存在
if 'user' in db:
    print('user key exists in the database.')

# 检索数据
user_data = db.get('user')
print(user_data)  # 输出: {'name': 'Alice', 'age': 30, 'emails': ['alice@example.com', 'a.smith@example.com']}

# 删除数据
db.delete('user')

# 获取所有键
keys = db.keys()
print(keys)  # 输出: 所有存在的键的列表

db.clear_database() # 清空数据库，这会删除toml文件和所有存储的文件
```

## 注意事项

- 如果选择将对象存储到文件系统中（`store_to_fs=True`），则会自动创建一个隐藏目录，用于存储 `pickle/dill` 文件。
- 确保对数据库文件有读写权限。
- 在多进程环境中使用时，建议使用 `FileLock` 提供的锁机制来确保线程安全。

## 许可证

本项目使用 MIT 许可证。有关更多信息，请参见 LICENSE 文件。
