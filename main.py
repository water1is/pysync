import threading
import time
from network import NetworkManager
import os

def main():
    print("PySync - 简易局域网文件同步工具")
    print(f"同步文件夹: {os.path.abspath('sync_folder')}")
    
    # 初始化网络管理器
    net_manager = NetworkManager()
    
    # 启动设备发现服务
    net_manager.start_discovery()
    
    # 启动文件同步服务器
    server_thread = threading.Thread(target=net_manager.start_file_server)
    server_thread.daemon = True
    server_thread.start()
    
    # 主循环
    try:
        while True:
            print("\n当前已知设备:")
            for ip in net_manager.peers:
                print(f"- {ip}")
            
            print("\n1. 手动同步所有设备")
            print("2. 退出")
            
            choice = input("请选择操作: ")
            
            if choice == '1':
                for ip in net_manager.peers:
                    print(f"正在与 {ip} 同步...")
                    net_manager.sync_with_peer(ip)
            elif choice == '2':
                net_manager.running = False
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        net_manager.running = False
        print("\n程序退出")
333
if __name__ == "__main__":
    main()