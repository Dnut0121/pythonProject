import random
from datetime import datetime


class DummySensor:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': None,
            'mars_base_external_temperature': None,
            'mars_base_internal_humidity': None,
            'mars_base_external_illuminance': None,
            'mars_base_internal_co2': None,
            'mars_base_internal_oxygen': None
        }

    def set_env(self):
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18, 30), 2)
        self.env_values['mars_base_external_temperature'] = round(random.uniform(0, 21), 2)
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(50, 60), 2)
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(500, 715), 2)
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.1), 3)
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(4, 7), 2)

    def get_env(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = (
            f"현재 시간: {now}\n"
            f"  화성 기지 내부 온도: {self.env_values['mars_base_internal_temperature']}°C\n"
            f"  화성 기지 외부 온도: {self.env_values['mars_base_external_temperature']}°C\n"
            f"  화성 기지 내부 습도: {self.env_values['mars_base_internal_humidity']}%\n"
            f"  화성 기지 외부 광량: {self.env_values['mars_base_external_illuminance']} W/m2\n"
            f"  화성 기지 내부 이산화탄소 농도: {self.env_values['mars_base_internal_co2']}%\n"
            f"  화성 기지 내부 산소 농도: {self.env_values['mars_base_internal_oxygen']}%\n"
            f"{'-' * 50}\n"
        )
        with open("sensor_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(log_line)
        return self.env_values

if __name__ == "__main__":
    ds = DummySensor()
    ds.set_env()
    env_data = ds.get_env()
    print(env_data)
