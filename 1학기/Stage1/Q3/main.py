def read_csv(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        inventory_list = []
        header = lines[0].strip().split(',')
        for line in lines[1:]:
            parts = line.strip().split(',')
            if len(parts) == 5:
                substance = parts[0]
                weight = parts[1]
                specific_gravity = parts[2]
                strength = parts[3]
                flammability = float(parts[4])

                inventory_list.append((substance, weight, specific_gravity, strength, flammability))

        return header, inventory_list
    except FileNotFoundError:
        return None, None
    except Exception as e:
        return None, None
def sort_flammability(inventory_list):
    return sorted(inventory_list, key=lambda x: x[4], reverse=True)


def filter_dangerous_items(inventory_list, threshold=0.7):
    return [item for item in inventory_list if item[4] >= threshold]


def save_csv_file(file_path, header, inventory_list):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(','.join(header) + '\n')
            for item in inventory_list:
                file.write(f'{item[0]},{item[1]},{item[2]},{item[3]},{item[4]}\n')
        print(f'\n위험 물질 목록이 저장되었습니다: {file_path}')
    except Exception as e:
        print(f'\n오류 발생: {e}')


def save_binary_file(file_path, inventory_list):
    try:
        with open(file_path, 'wb') as file:
            for item in inventory_list:
                line = f'{item[0]},{item[1]},{item[2]},{item[3]},{item[4]}\n'
                file.write(line.encode('utf-8'))
        print(f'\n이진 파일이 저장되었습니다: {file_path}')
    except Exception as e:
        print(f'\n오류 발생: {e}')


def read_binary_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            content = file.read().decode('utf-8')
            print('\n저장된 이진 파일 내용')
            print(content)
    except FileNotFoundError:
        print(f'\n오류: {file_path} 파일을 찾을 수 없습니다.')
    except Exception as e:
        print(f'\n오류 발생: {e}')


def main():

    print('Mars Base Inventory List 처리 시작')

    csv_file = 'Mars_Base_Inventory_List.csv'
    danger_csv_file = 'Mars_Base_Inventory_danger.csv'
    binary_file = 'Mars_Base_Inventory_List.bin'

    header, inventory_list = read_csv(csv_file)

    if inventory_list is not None:
        sorted_inventory = sort_flammability(inventory_list)
        dangerous_items = filter_dangerous_items(sorted_inventory)
        save_csv_file(danger_csv_file, header, dangerous_items)
        save_binary_file(binary_file, sorted_inventory)
        read_binary_file(binary_file)

if __name__ == '__main__':
    main()
