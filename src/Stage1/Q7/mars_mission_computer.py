import threading
import time
from dummy_sensor import DummySensor

class MissionComputer:

    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': None,
            'mars_base_external_temperature': None,
            'mars_base_internal_humidity': None,
            'mars_base_external_illuminance': None,
            'mars_base_internal_co2': None,
            'mars_base_internal_oxygen': None
        }
        self.ds = DummySensor()
        self.stop_flag = False
        self.iteration_count = 0
        self.accumulated = {key: [] for key in self.env_values}

    def _input_thread(self):
        while True:
            user_input = input("출력을 중단하려면 'stop' 메시지를 입력하세요...\n")
            if user_input.strip().lower() == "stop":
                self.stop_flag = True
                break

    def get_sensor_data(self):
        input_thread = threading.Thread(target=self._input_thread)
        input_thread.daemon = True
        input_thread.start()

        while not self.stop_flag:
            self.ds.set_env()
            sensor_data = self.ds.get_env()
            self.env_values = sensor_data.copy()

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            output = (
                "============================================\n"
                "       센서 데이터 출력\n"
                "============================================\n"
                f"현재 시간: {timestamp}\n"
                f"화성 기지 내부 온도      : {self.env_values['mars_base_internal_temperature']} °C\n"
                f"화성 기지 외부 온도      : {self.env_values['mars_base_external_temperature']} °C\n"
                f"화성 기지 내부 습도      : {self.env_values['mars_base_internal_humidity']} %\n"
                f"화성 기지 외부 광량      : {self.env_values['mars_base_external_illuminance']} W/m2\n"
                f"화성 기지 내부 이산화탄소: {self.env_values['mars_base_internal_co2']} %\n"
                f"화성 기지 내부 산소      : {self.env_values['mars_base_internal_oxygen']} %\n"
                "============================================\n"
            )
            print(output)

            for key, value in self.env_values.items():
                self.accumulated[key].append(value)

            self.iteration_count += 1

            if self.iteration_count % 60 == 0:
                avg_values = {}
                for key, readings in self.accumulated.items():
                    avg_values[key] = round(sum(readings) / len(readings), 2)
                avg_output = (
                    "\n********** 5분 평균 값 **********\n"
                    f"화성 기지 내부 온도      : {avg_values['mars_base_internal_temperature']} °C\n"
                    f"화성 기지 외부 온도      : {avg_values['mars_base_external_temperature']} °C\n"
                    f"화성 기지 내부 습도      : {avg_values['mars_base_internal_humidity']} %\n"
                    f"화성 기지 외부 광량      : {avg_values['mars_base_external_illuminance']} W/m2\n"
                    f"화성 기지 내부 이산화탄소: {avg_values['mars_base_internal_co2']} %\n"
                    f"화성 기지 내부 산소      : {avg_values['mars_base_internal_oxygen']} %\n"
                    "********************************\n"
                )
                print(avg_output)
                self.accumulated = {key: [] for key in self.env_values}
            time.sleep(5)

        print("시스템 종료….")


if __name__ == "__main__":
    RunComputer = MissionComputer()
    RunComputer.get_sensor_data()
