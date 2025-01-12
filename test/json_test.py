
import wjson

if __name__ == '__main__':
    file_path = '/Users/wangning/Downloads/SVT Niki-29852-1-2-2-1735739709/[CP] SVT Niki/i18n/default1.json'
    
    # 读取JSON
    with open(file_path, 'r',
              encoding='utf-8') as f:
        decoded_object = wjson.load(f)
        print(decoded_object)
        # 写入新文件
        new_file_path = file_path.replace('.json', '_new.json')
        with open(new_file_path, 'w', encoding='utf-8') as f1:
            wjson.dump(decoded_object, f1)
