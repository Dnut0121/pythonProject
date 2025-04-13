import platform
import psutil
import json
import os

class MissionComputer:
    def __init__(self):
        self.setting_file = 'setting.txt'
        self.default_settings = [
            "os", "os_version", "cpu_type", "cpu_count",
            "memory", "cpu_usage", "memory_usage"
        ]
        self.settings = self.load_or_create_settings()

    def load_or_create_settings(self):
        if not os.path.exists(self.setting_file):
            print(f"'{self.setting_file}' 기본 옵션")
            with open(self.setting_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.default_settings))
            return set(self.default_settings)
        else:
            with open(self.setting_file, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())

    def get_mission_computer_info(self):
        try:
            info = {}
            if "os" in self.settings:
                info["Operating System"] = platform.system()
            if "os_version" in self.settings:
                info["OS Version"] = platform.version()
            if "cpu_type" in self.settings:
                info["CPU Type"] = platform.processor()
            if "cpu_count" in self.settings:
                info["CPU Core Count"] = psutil.cpu_count(logical=True)
            if "memory" in self.settings:
                mem_mb = round(psutil.virtual_memory().total / (1024 * 1024), 2)
                info["Total Memory (MB)"] = mem_mb

            print("\n[Mission Computer Info]")
            print(json.dumps(info, indent=4, ensure_ascii=False))
        except Exception as e:
            print(f"시스템 정보 수집 중 오류 발생: {e}")

    def get_mission_computer_load(self):
        try:
            load = {}
            if "cpu_usage" in self.settings:
                load["CPU Usage (%)"] = psutil.cpu_percent(interval=1)
            if "memory_usage" in self.settings:
                load["Memory Usage (%)"] = psutil.virtual_memory().percent

            print("\n[Mission Computer Load]")
            print(json.dumps(load, indent=4, ensure_ascii=False))
        except Exception as e:
            print(f"시스템 부하 수집 중 오류 발생: {e}")

if __name__ == "__main__":
    runComputer = MissionComputer()
    runComputer.get_mission_computer_info()
    runComputer.get_mission_computer_load()
