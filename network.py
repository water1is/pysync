import socket
import threading
import json
import time
import os
from config import config
from file_utils import FileUtils

class NetworkManager:
    def __init__(self):
        self.peers = {}  # 已知的peer设备 {ip: last_seen_time}
        self.running = True
        
    def start_discovery(self):
        """启动设备发现服务"""
        # 广播线程
        broadcast_thread = threading.Thread(target=self.broadcast_presence)
        broadcast_thread.daemon = True
        broadcast_thread.start()
        
        # 监听线程
        listen_thread = threading.Thread(target=self.listen_for_peers)
        listen_thread.daemon = True
        listen_thread.start()
        
    def broadcast_presence(self):
        """定期广播本机存在"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while self.running:
            try:
                message = json.dumps({'type': 'discovery', 'port': config.FILE_SYNC_PORT})
                sock.sendto(message.encode(), ('<broadcast>', config.BROADCAST_PORT))
                time.sleep(config.BROADCAST_INTERVAL)
            except Exception as e:
                print(f"Broadcast error: {e}")
    
    def listen_for_peers(self):
        """监听其他设备的广播"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', config.BROADCAST_PORT))
        
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode())
                
                if message['type'] == 'discovery':
                    ip = addr[0]
                    self.peers[ip] = time.time()
                    print(f"Discovered peer: {ip}")
            except Exception as e:
                print(f"Discovery listener error: {e}")
    
    # 修改network.py中的文件传输方法
    

    def sync_with_peer(self, peer_ip):
        """与指定peer同步文件"""
        try:
            # 连接peer
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((peer_ip, config.FILE_SYNC_PORT))
            
            # 发送本地文件列表
            local_files = FileUtils.get_sync_files()
            sock.send(json.dumps(local_files).encode())
            
            # 接收远程文件列表
            remote_files = json.loads(sock.recv(config.BUFFER_SIZE).decode())
            
            # 比较文件差异
            to_download, to_upload = FileUtils.compare_files(local_files, remote_files)
            
            # 处理需要下载的文件
            for file_info in to_download:
                self._download_file(sock, file_info)
            
            # 处理需要上传的文件
            for file_info in to_upload:
                self._upload_file(sock, file_info)
            
            sock.close()
            print(f"Sync with {peer_ip} completed")
            
        except Exception as e:
            print(f"Sync error with {peer_ip}: {e}")
    
    def _download_file(self, sock, file_info):
        print(f"下载 {file_info['name']} ({file_info['size']} bytes)")
        received = 0
        file_path = os.path.join(config.SYNC_FOLDER, file_info['name'])
        with open(file_path, 'wb') as f:
            while received < file_info['size']:
                data = sock.recv(min(config.BUFFER_SIZE, file_info['size'] - received))
                if not data:
                    break
                f.write(data)
                received += len(data)
                progress = int(received / file_info['size'] * 50)
                print(f"[{'#'*progress}{' '*(50-progress)}] {int(received/file_info['size']*100)}%", end='\r')
        print()  # 换行
    
    def _upload_file(self, sock, file_info):
        """上传文件到peer"""
        try:
            # 通知peer准备接收文件
            sock.send(json.dumps({'action': 'upload', 'file': file_info['name']}).encode())
            
            # 发送文件内容
            file_path = os.path.join(config.SYNC_FOLDER, file_info['name'])
            with open(file_path, 'rb') as f:
                while True:
                    bytes_read = f.read(config.BUFFER_SIZE)
                    if not bytes_read:
                        break
                    sock.sendall(bytes_read)
            
            print(f"Uploaded: {file_info['name']}")
            
        except Exception as e:
            print(f"Upload error: {e}")
    
    def start_file_server(self):
        """启动文件同步服务器"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', config.FILE_SYNC_PORT))
        sock.listen(5)
        
        while self.running:
            try:
                conn, addr = sock.accept()
                threading.Thread(target=self._handle_client, args=(conn, addr)).start()
            except Exception as e:
                print(f"File server error: {e}")
    
    def _handle_client(self, conn, addr):
        """处理客户端连接"""
        try:
            # 接收客户端文件列表
            local_files = FileUtils.get_sync_files()
            remote_files = json.loads(conn.recv(config.BUFFER_SIZE).decode())
            
            # 发送本地文件列表
            conn.send(json.dumps(local_files).encode())
            
            # 比较文件差异
            to_download, to_upload = FileUtils.compare_files(local_files, remote_files)
            
            # 处理客户端请求
            while True:
                request = json.loads(conn.recv(config.BUFFER_SIZE).decode())
                
                if request['action'] == 'download':
                    self._send_file(conn, request['file'])
                elif request['action'] == 'upload':
                    self._receive_file(conn, request['file'])
                else:
                    break
                    
        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            conn.close()
    
    def _send_file(self, conn, filename):
        """发送文件给客户端"""
        file_path = os.path.join(config.SYNC_FOLDER, filename)
        with open(file_path, 'rb') as f:
            while True:
                bytes_read = f.read(config.BUFFER_SIZE)
                if not bytes_read:
                    break
                conn.sendall(bytes_read)
    
    def _receive_file(self, conn, filename):
        """接收客户端发送的文件"""
        file_path = os.path.join(config.SYNC_FOLDER, filename)
        with open(file_path, 'wb') as f:
            while True:
                data = conn.recv(config.BUFFER_SIZE)
                if not data:
                    break
                f.write(data)