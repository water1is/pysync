import os
import time
from config import config

class FileUtils:
    @staticmethod
    def get_file_info(file_path):
        """获取文件信息"""
        if not os.path.exists(file_path):
            return None
            
        return {
            'name': os.path.basename(file_path),
            'size': os.path.getsize(file_path),
            'mtime': os.path.getmtime(file_path)
        }

    @staticmethod
    def get_sync_files():
        """获取同步文件夹中的所有文件信息"""
        files = []
        for filename in os.listdir(config.SYNC_FOLDER):
            file_path = os.path.join(config.SYNC_FOLDER, filename)
            if os.path.isfile(file_path):
                files.append(FileUtils.get_file_info(file_path))
        return files

    @staticmethod
    def compare_files(local_files, remote_files):
        """比较本地和远程文件，返回需要下载和上传的文件列表"""
        local_dict = {f['name']: f for f in local_files}
        remote_dict = {f['name']: f for f in remote_files}
        
        to_download = []
        to_upload = []
        
        # 检查需要下载的文件
        for name, remote_file in remote_dict.items():
            if name not in local_dict:
                to_download.append(remote_file)
            elif remote_file['mtime'] > local_dict[name]['mtime']:
                to_download.append(remote_file)
        
        # 检查需要上传的文件
        for name, local_file in local_dict.items():
            if name not in remote_dict:
                to_upload.append(local_file)
            elif local_file['mtime'] > remote_dict[name]['mtime']:
                to_upload.append(local_file)
        
        return to_download, to_upload