import os
import subprocess
import time
from ppadb.client import Client as AdbClient

class AndroidManager:
    def __init__(self, ldplayer_path=r"C:\LDPlayer\LDPlayer9"):
        self.ld_path = ldplayer_path
        self.ldconsole = os.path.join(ldplayer_path, "ldconsole.exe")
        self.adb_client = None
        
    def start_adb_server(self):
        os.chdir(self.ld_path)
        subprocess.run(["adb.exe", "start-server"], stdout=subprocess.DEVNULL)
        self.adb_client = AdbClient(host="127.0.0.1", port=5037)
        
    def create_new_emulator(self, name):
        os.chdir(self.ld_path)
        subprocess.run([self.ldconsole, "add", "--name", name])
        
    def launch_emulator(self, name):
        os.chdir(self.ld_path)
        subprocess.run([self.ldconsole, "launch", "--name", name])
        
    def get_device(self, index=0):
        self.start_adb_server()
        devices = self.adb_client.devices()
        if not devices:
            return None
        return devices[index]