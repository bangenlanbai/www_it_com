import csv


def get_content(file_path):
    """
        读取 csv    
    """
    content = []
    with open(file_path, mode='r', encoding='utf-8-sig') as f:
        list_reader = csv.reader(f)
        for item in list_reader:
            content.append({'name': item[0], 'min': item[1], 'max': item[2]})
    return content


if __name__ == '__main__':
    from config import BASE_DIR
    import os
    file_path = os.path.join(BASE_DIR, 'product.xlsx') 
    get_content(file_path)
