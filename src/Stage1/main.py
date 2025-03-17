def read_log_file( file_path ):
    try:
        with open( file_path, 'r', encoding = 'utf-8' ) as file:
            log_contents = file.readlines()
            for line in log_contents:
                print(line.strip())
            return log_contents
    except FileNotFoundError:
        print( '\n오류: ' + file_path + ' 파일을 찾을 수 없습니다.' )
        return None
    except Exception as e:
        print( '\n오류 발생: ' + str( e ) )
        return None

def parse_logs(log_contents):
    parsed_logs = []
    for line in log_contents:
        parts = line.strip().split(',', 2)
        if len(parts) == 3:
            timestamp, event, message = parts
            parsed_logs.append((timestamp, event, message))
    return parsed_logs

def write_markdown_report(report_path, parsed_logs):
    with open(report_path, 'w', encoding='utf-8') as file:
        file.write('# 보고서\n\n')
        file.write('## 개요\n')
        file.write('이 보고서는 로그 파일을 분석하여 정리한 문서입니다.\n\n')

        file.write('## 전체 로그 기록\n')
        for timestamp, event, message in parsed_logs:
            file.write('시간:' + timestamp + '\n')
            file.write('이벤트:' + event + '\n')
            file.write('메시지:' + message + '\n\n')

    print('\n보고서가 생성되었습니다: log_analysis.md')

def main():
    print('Hello Mars\n')
    log_file = 'mission_computer_main.log'
    report_file = 'log_analysis.md'

    log_contents = read_log_file(log_file)

    if log_contents is not None:
        parsed_logs = parse_logs(log_contents)
        write_markdown_report(report_file, parsed_logs)


if __name__ == '__main__':
    main()
