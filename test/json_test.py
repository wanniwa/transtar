import json

import hjson
import json_repair

from app.common.utils.trans_util import deepl_translate

if __name__ == '__main__':
    file_path = 'file/MarriageDialogue.json'


    with open(file_path, 'r', encoding='utf-8') as f:
        # content = json5.load(f, encoding='utf-8')
        decoded_object = json_repair.repair_json(f.read(), ensure_ascii=False)
        loads = hjson.loads(decoded_object, encoding='utf-8')
        print(decoded_object)
        with open(file_path, 'w', encoding='utf-8') as f1:
            # json.dump(loads, f1, indent=4, ensure_ascii=False)
            json.dump(loads, f1, indent=4, ensure_ascii=False)
