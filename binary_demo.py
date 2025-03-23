from tomldb import TomlDB

bin = open("random_1mb.bin", "rb").read()

db = TomlDB("bin_demo.toml")

db["bin"] = bin

read_bin = db["bin"]

print(read_bin == bin)  # True