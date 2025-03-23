import os
import toml
import json
import dill
import pickle
import base64
import hashlib
from filelock import FileLock

class TomlDB:
    def __init__(self, filename: str = 'db.toml', store_to_fs: bool = True, use_pickle: bool = False):
        self.filename = filename
        self.lockfile = f"{filename}.lock"
        self.lock = FileLock(self.lockfile)
        self.store_to_fs = store_to_fs
        self.pickle_dir = f".{os.path.splitext(filename)[0]}_tdbdata"
        if self.store_to_fs:
            os.makedirs(self.pickle_dir, exist_ok=True)

        self.serializer_name = 'pickle' if use_pickle else 'dill'
        self.pickle_module = pickle if use_pickle else dill

        self._load_database()

    def _load_database(self):
        """Load the database from a TOML file."""
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.data = toml.load(f)

            # 检查数据库中存储的序列化模块和存储方式是否与当前一致
            stored_serializer = self.data.get('__serializer__')
            stored_store_to_fs = self.data.get('__store_to_fs__')
            if stored_serializer and stored_serializer != self.serializer_name:
                raise ValueError(f"Serializer mismatch: expected {stored_serializer}, got {self.serializer_name}")
            if stored_store_to_fs is not None and stored_store_to_fs != self.store_to_fs:
                raise ValueError(f"Store to fs mismatch: expected {stored_store_to_fs}, got {self.store_to_fs}")
        else:
            self.data = {}

        # 在数据库中存储当前使用的序列化模块和存储方式
        self.data['__serializer__'] = self.serializer_name
        self.data['__store_to_fs__'] = self.store_to_fs

    def _save_database(self):
        """Save the database to a TOML file."""
        with open(self.filename, 'w', encoding='utf-8') as f:
            toml.dump(self.data, f)

    def _serialize_value(self, value):
        """Serialize the value to a JSON-compatible format if possible, else use the specified serializer."""
        try:
            return json.dumps(value), 'json'
        except (TypeError, OverflowError):
            if self.store_to_fs:
                # 序列化对象并计算其 SHA-1 哈希值
                pickled_value = self.pickle_module.dumps(value)
                sha1_hash = hashlib.sha1(pickled_value).hexdigest()
                # 使用 SHA-1 生成唯一的文件名
                pickle_filename = f"{sha1_hash}tdbdata"
                pickle_path = os.path.join(self.pickle_dir, pickle_filename)
                with open(pickle_path, 'wb') as pf:
                    pf.write(pickled_value)
                return pickle_filename, 'file'
            else:
                base64_value = base64.b64encode(self.pickle_module.dumps(value)).decode('utf-8')
                return base64_value, 'pickle'

    def _deserialize_value(self, value, value_type):
        """Deserialize the value based on its storage type."""
        if value_type == 'json':
            return json.loads(value)
        elif value_type == 'pickle':
            pickled_value = base64.b64decode(value.encode('utf-8'))
            return self.pickle_module.loads(pickled_value)
        elif value_type == 'file':
            pickle_path = os.path.join(self.pickle_dir, value)
            with open(pickle_path, 'rb') as pf:
                return self.pickle_module.load(pf)
        else:
            raise ValueError("Unsupported value type")

    def set(self, key, value):
        """Set a key-value pair in the database."""
        with self.lock:
            self._load_database()

            # 检查旧值是否存在且为文件类型，并删除对应的文件
            if key in self.data and self.data[key]['type'] == 'file':
                old_entry = self.data[key]
                old_file_path = os.path.join(self.pickle_dir, old_entry['value'])
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            serialized_value, value_type = self._serialize_value(value)
            self.data[key] = {'value': serialized_value, 'type': value_type}
            self._save_database()

    def get(self, key, default=None):
        """Get a value by key from the database, with an optional default value."""
        with self.lock:
            self._load_database()
            entry = self.data.get(key, None)
            if entry is None:
                return default
            try:
                return self._deserialize_value(entry['value'], entry['type'])
            except (json.JSONDecodeError, dill.UnpicklingError, pickle.UnpicklingError, TypeError, ValueError):
                return default

    def delete(self, key):
        """Delete a key-value pair from the database."""
        with self.lock:
            self._load_database()
            if key in self.data:
                entry = self.data[key]
                if entry['type'] == 'file':
                    os.remove(os.path.join(self.pickle_dir, entry['value']))
                del self.data[key]
                self._save_database()

    def exists(self, key):
        """Check if a key exists in the database."""
        with self.lock:
            self._load_database()
            return key in self.data

    def keys(self):
        """Return all keys in the database."""
        with self.lock:
            self._load_database()
            return list(self.data.keys())

    def __contains__(self, key):
        """Check if a key exists in the database using 'in' operator."""
        return self.exists(key)

    def clear_database(self):
        """Delete the entire database and associated files."""
        with self.lock:
            # 删除 TOML 文件
            if os.path.exists(self.filename):
                os.remove(self.filename)
            
            # 删除 pickle 文件目录中的所有文件
            if os.path.exists(self.pickle_dir):
                for filename in os.listdir(self.pickle_dir):
                    file_path = os.path.join(self.pickle_dir, filename)
                    os.remove(file_path)
                os.rmdir(self.pickle_dir)
            
            # 重置内存中的数据
            self.data = {}
    
    def __getitem__(self, key):
        """Enable bracket access for getting values."""
        value = self.get(key)
        if value is None:
            raise KeyError(f"Key '{key}' not found in the database.")
        return value
    
    def __setitem__(self, key, value):
        """Enable bracket access for setting values."""
        self.set(key, value)
        
    def __delitem__(self, key):
        """Enable the use of 'del' to remove a key."""
        if key not in self.data:
            raise KeyError(f"Key '{key}' not found in the database.")
        self.delete(key)



# 示例使用
if __name__ == '__main__':
    # 创建数据库实例时，指定是否使用 pickle（默认为使用 dill）
    db = TomlDB(store_to_fs=True, use_pickle=False)

    db.set('user', {'name': 'Alice', 'age': 30, 'emails': ['alice@example.com', 'a.smith@example.com']})
    
    db["user"] = {'name': 'Alice', 'age': 30, 'emails': ['alice@example.com', 'a.smith@example.com']}

    # 使用 'in' 运算符检查键是否存在
    if 'user' in db:
        print('user key exists in the database.')

    if 'nonexistent' not in db:
        print('nonexistent key does not exist in the database.')

    # 清空数据库
    db.clear_database()
    print("Database cleared.")
    