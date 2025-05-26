import string

def caesar_cipher_decode(target_text, shift):
    result = []
    for ch in target_text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            decoded = chr((ord(ch) - base - shift) % 26 + base)
            result.append(decoded)
        else:
            result.append(ch)
    return ''.join(result)

def load_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"경고: 파일을 찾을 수 없습니다: {filepath}")
    except IOError as e:
        print(f"경고: 파일을 읽는 중 오류 발생: {e}")
    return ""

def save_text_file(filepath, text):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"복호화 결과를 '{filepath}'에 저장했습니다.")
    except IOError as e:
        print(f"경고: 파일을 쓰는 중 오류 발생: {e}")

def main():
    cipher_text = load_text_file("password.txt")
    if not cipher_text:
        return

    #키워드 정리
    # shift 1: lzqr06, shift 2: kypq06, shift 3: jxop06, shift 4: iwno06, shift 5: hvmn06, shift 6: gulm06,
    # shift 7: ftkl06, shift 8: esjk06, shift 9: drij06, shift 10: cqhi06, shift 11: bpgh06, shift 12: aofg06,
    # shift 13: znef06, shift 14: ymde06, shift 15: xlcd06, shift 16: wkbc06, shift 17: vjab06, shift 18: uiza06,
    # shift 19: thyz06, shift 20: sgxy06, shift 21: rfwx06, shift 22: qevw06, shift 23: pduv06, shift 24: octu06, shift 25: nbst06
    keywords = [""]
    found = False

    # 1) 키워드 자동 탐지 루프
    for shift in range(1, 26):
        decoded = caesar_cipher_decode(cipher_text, shift)
        print(f"=== shift = {shift} ===")
        print(decoded)
        print()

        lower = decoded.lower()
        for kw in keywords:
            if kw in lower:
                print(f"키워드 '{kw}' 발견! shift={shift} 에서 복호화가 완료되었습니다.")
                save_text_file("result.txt", decoded)
                found = True
                break
        if found:
            break

    if not found:
        while True:
            choice = input("키워드가 발견되지 않았습니다. 올바른 shift 값을 입력하세요 (1-25), 또는 그냥 Enter로 종료: ").strip()
            if not choice:
                print("종료합니다. result.txt가 생성되지 않았습니다.")
                break
            if not choice.isdigit() or not (1 <= int(choice) <= 25):
                print("1에서 25 사이의 숫자를 입력해주세요.")
                continue

            shift = int(choice)
            result_text = caesar_cipher_decode(cipher_text, shift)
            save_text_file("result.txt", result_text)
            break

if __name__ == "__main__":
    main()
