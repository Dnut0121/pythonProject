import csv
import os
import datetime
import sounddevice as sd
import wavio
import speech_recognition as sr

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
def list_audio_files(records_dir):
    return [f for f in os.listdir(records_dir) if f.lower().endswith('.wav')]

def stt_file_to_csv(records_dir, filename):
    wav_path = os.path.join(records_dir, filename)
    csv_name = os.path.splitext(filename)[0] + '.csv'
    csv_path = os.path.join(records_dir, csv_name)
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language='ko-KR')
            print('인식 결과:', text)
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['시간', '인식된 텍스트'])
                writer.writerow(['00:00', text])
            print('CSV 저장 완료:', csv_path)
        except sr.UnknownValueError:
            print('음성을 인식할 수 없습니다.')
        except sr.RequestError as e:
            print('STT 요청에 실패했습니다:', e)

def stt_batch_all_files(records_dir):
    audio_files = list_audio_files(records_dir)
    if not audio_files:
        print('음성 파일이 없습니다.')
        return
    for wavfile in audio_files:
        stt_file_to_csv(records_dir, wavfile)

def search_keyword_in_csv(records_dir, keyword):
    found = False
    for file in os.listdir(records_dir):
        if file.lower().endswith('.csv'):
            csv_path = os.path.join(records_dir, file)
            with open(csv_path, encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, None) # skip header
                for row in reader:
                    if keyword in row[1]:
                        print(f'파일: {file} | 시간: {row[0]} | 내용: {row[1]}')
                        found = True
    if not found:
        print('해당 키워드를 포함한 텍스트가 없습니다.')

def main():
    records_dir = create_records_folder()
    while True:
        print('\n메뉴를 선택하세요:')
        print('1. 음성 녹음')
        print('2. 날짜 범위로 녹음 파일 보기')
        print('3. 녹음 파일 STT 후 CSV로 저장')
        print('4. 키워드로 CSV에서 내용 검색')
        print('5. 종료')
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
            stt_batch_all_files(records_dir)
        elif choice == '4':
            keyword = input('검색할 키워드를 입력하세요: ')
            search_keyword_in_csv(records_dir, keyword)
        elif choice == '5':
            print('프로그램을 종료합니다.')
            break
        else:
            print('올바른 메뉴를 선택하세요.')

if __name__ == '__main__':
    main()
