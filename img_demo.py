import time
from PIL import Image
from PIL.ImageFile import ImageFile
from tomldb import TomlDB

# 计时器装饰器
def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 耗时: {end_time - start_time:.4f} 秒")
        return result
    return wrapper

@timer
def open_image(file_path):
    return Image.open(file_path)

@timer
def create_db(file_name):
    return TomlDB(file_name, store_to_fs=False, use_pickle=False)

@timer
def set_image_to_db(db, key, img):
    db.set(key, img)

@timer
def get_image_from_db(db:TomlDB, key):
    res = db.get(key)
    # db.clear_database()
    return res

@timer
def save_image(img, file_path):
    # img.show()
    img.save(file_path)

# 打开图片
img = open_image("_demo.png")

# 创建数据库
db = create_db("img_demo1.toml")

# 将图片存储到数据库
set_image_to_db(db, "image", img)

# 从数据库读取图片
read_img: ImageFile = get_image_from_db(db, "image")

# 保存读取的图片
save_image(read_img, "read_demo.png")
