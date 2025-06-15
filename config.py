import os

# 配置类
class Config:
    def __init__(self):
        self.SYNC_FOLDER = "sync_folder"
        self.BROADCAST_PORT = 37020
        self.FILE_SYNC_PORT = 37021
        self.BUFFER_SIZE = 4096          # 传输缓冲区大小
        self.BROADCAST_INTERVAL = 5      # 广播间隔(秒)
        
        # 确保同步文件夹存在
        if not os.path.exists(self.SYNC_FOLDER):
            os.makedirs(self.SYNC_FOLDER)

config = Config()