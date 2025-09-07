import os
import sys
import datetime
import sounddevice as sd
import wavio

def create_records_folder():
    records_dir = os.path.join(os.getcwd(), 'records')
    if not os.path.exists(records_dir):
        os.makedirs(records_dir)
    return records_dir


def get_filename():
    now = datetime.datetime.now()
    filename = now.strftime('%Y%m%d-%H%M%S') + '.wav'
    return filename


def record_audio(duration=5, fs=44100):
    print('녹음을 시작합니다. ({}초)'.format(duration))
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    print('녹음이 완료되었습니다.')
    return audio, fs


def save_audio(audio, fs, file_path):
    wavio.write(file_path, audio, fs, sampwidth=2)
    print('파일이 저장되었습니다: {}'.format(file_path))


def show_record_files(start_date, end_date, records_dir):
    files = os.listdir(records_dir)
    selected_files = []
    for file in files:
        if file.endswith('.wav'):
            try:
                date_str = file[:15]
                file_date = datetime.datetime.strptime(date_str, '%Y%m%d-%H%M%S')
                if start_date <= file_date <= end_date:
                    selected_files.append(file)
            except Exception:
                continue
    if not selected_files:
        print('지정한 날짜에 해당하는 파일이 없습니다.')
    else:
        print('지정한 날짜의 파일 목록:')
        for file in selected_files:
            print(file)


def input_date(prompt):
    while True:
        date_str = input(prompt)
        try:
            return datetime.datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            print('날짜 형식이 올바르지 않습니다. (예: 20240531)')


def main():
    records_dir = create_records_folder()
    while True:
        print('\n메뉴를 선택하세요:')
        print('1. 음성 녹음')
        print('2. 날짜 범위로 녹음 파일 보기')
        print('3. 종료')
        choice = input('입력: ')
        if choice == '1':
            filename = get_filename()
            audio, fs = record_audio()
            save_audio(audio, fs, os.path.join(records_dir, filename))
        elif choice == '2':
            print('날짜 범위를 입력하세요.')
            start_date = input_date('시작 날짜 (YYYYMMDD): ')
            end_date = input_date('종료 날짜 (YYYYMMDD): ')
            end_date = end_date.replace(hour=23, minute=59, second=59)
            show_record_files(start_date, end_date, records_dir)
        elif choice == '3':
            print('프로그램을 종료합니다.')
            break
        else:
            print('올바른 메뉴를 선택하세요.')


if __name__ == '__main__':
    main()