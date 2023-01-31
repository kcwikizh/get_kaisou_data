import re
import json
import requests

kaisou_data = {}
"""
kaisou_data 改造所需素材

key: cur_ship_id 改前id

value: a dict: {
    "api_id": after_ship_id,        # 改造后id
    "cur_ship_id": cur_ship_id,     # 当前id
    "ammo": ship["api_afterbull"],  # 改造弹耗
    "steel": ship["api_afterfuel"], # 改造钢耗（为什么api里写的是fuel油？？？）
    "drawing": 0,                   # 图纸          暂置0
    "catapult": 0,                  # 甲板          暂置0
    "report": 0,                    # 详报          暂置0
    "devkit": 0,                    # 开发紫菜      暂置0
    "buildkit": 0,                  # 喷火          暂置0
    "aviation": 0,                  # 新航空紫菜    暂置0
    "hokoheso": 0,                  # 新火炮紫菜    暂置0
    "arms":     0,                  # 新兵装紫菜    暂置0
}
"""


id2name = {}
"""
key: 船的id
value: 船的名字
"""


id2sortno = {}
"""
key: 船的id
value: sortno, 图鉴编号
"""


# main_js_url = 'http://ooi.moe/kcs2/js/main.js'
# 2020.04: Because of c2's technology progress,
# We use this one: https://raw.githubusercontent.com/kcwikizh/kancolle-main/master/dist/main.js
main_js_url = 'https://raw.githubusercontent.com/kcwikizh/kancolle-main/master/dist/main.js'
main_js_path = './main.js'
api_start2_json_url = 'http://api.kcwiki.moe/start2'
api_start2_json_path = './api_start2.json'

# step 0: download latest api_start2.json and main.js
print('step 0: download latest api_start2.json and main.js')
with open(api_start2_json_path, 'w', encoding='utf8') as f:
    print("Downloading api_start2.json")
    api_start2 = json.loads(requests.get(api_start2_json_url).text)
    json.dump(api_start2, f, ensure_ascii=False, indent=2)
with open(main_js_path, 'w', encoding='utf8') as f:
    print("Downloading main.js")
    f.write(requests.get(main_js_url).text)


# step 1: get id2name and id2sortno from api_start2.json
print('step 1: get id2name dict from api_start2.json')
with open(api_start2_json_path, 'r', encoding='utf8') as f:
    api_start2 = json.load(f)
    for ship in api_start2["api_mst_ship"]:
        id_ = ship["api_id"]
        name = ship["api_name"]
        sortno = ship.get("api_sortno", -1)     # 深海不存在api_sortno
        id2name[id_] = name
        id2sortno[id_] = sortno


# step 2.1: parse api_start2.json, get all KaiSou-able ships , get ammo and steel cost
print('step 2.1: parse api_start2.json, get all KaiSou-able ships, get ammo and steel cost')
with open(api_start2_json_path, 'r', encoding='utf8') as f:
    api_start2 = json.load(f)
    for ship in api_start2["api_mst_ship"]:
        if ship["api_id"] > 1500:
            continue      # 深海舰id>=1501
        after_ship_id = int(ship["api_aftershipid"])
        if after_ship_id:
            cur_ship_id = ship["api_id"]
            kaisou_data[cur_ship_id] = {
                "api_id": after_ship_id,        # 改造后id
                "cur_ship_id": cur_ship_id,     # 当前id
                "ammo": ship["api_afterbull"],  # 改造弹耗
                "steel": ship["api_afterfuel"], # 改造钢耗（为什么api里写的是fuel油？？？）
                "drawing": 0,                   # 图纸              暂置0
                "catapult": 0,                  # 甲板              暂置0
                "report": 0,                    # 详报              暂置0
                "devkit": 0,                    # 开发紫菜          暂置0
                "buildkit": 0,                  # 喷火              暂置0
                "aviation": 0,                  # 新航空紫菜        暂置0
                "hokoheso": 0,                  # 新火炮紫菜        暂置0
                "arms": 0,                      # 新兵装紫菜        暂置0
                "boiler": 0,                    # 新型高温高圧缶    暂置0
            }


# step 2.2: parse api_start2.json again, get api_id, cur_ship_id, drawing, catapult, report, aviation, and arms (key: cur_ship_id)
print('step 2.2: parse api_start2.json again, get api_id, cur_ship_id, drawing, catapult, report, aviation (key: cur_ship_id)')
with open(api_start2_json_path, 'r', encoding='utf8') as f:
    api_start2 = json.load(f)
    for item in api_start2["api_mst_shipupgrade"]:
        api_id = item["api_id"]
        cur_ship_id = item["api_current_ship_id"]
        if 0 == cur_ship_id:
            continue        # 原生舰船，非改造而来
        kaisou_data[cur_ship_id]["drawing"] = item["api_drawing_count"]
        kaisou_data[cur_ship_id]["catapult"] = item["api_catapult_count"]
        kaisou_data[cur_ship_id]["report"] = item["api_report_count"]
        kaisou_data[cur_ship_id]["aviation"] = item["api_aviation_mat_count"]
        kaisou_data[cur_ship_id]["arms"] = item["api_arms_mat_count"]
        kaisou_data[cur_ship_id]["boiler"] = item.get("api_boiler_count", 0)


# step 3.1: parse main.js, get newhokohesosizai
print('step 3.1: parse main.js, get newhokohesosizai')
rex_hokoheso_func = re.compile(r'''Object.defineProperty\(\w+.prototype, *["']newhokohesosizai["'], *\{\s*'?get'?: *function\(\) *\{\s*switch *\(this.mst_id_after\) *\{\s*((.*\n)+?)\s*default:\s*return 0;\s*\}''', re.M)
rex_hokoheso_item = re.compile(r'((case *\d+:\s*)+)return *(\d+);\s*')
rex_case = re.compile(r'case *(\d+):')

with open(main_js_path, 'r', encoding='utf8') as f:
    ctx = f.read()
    match = rex_hokoheso_func.search(ctx)
    for m in rex_hokoheso_item.finditer(match.group(1)):
        hokoheso_num = int(m.group(3))
        for m_c in rex_case.finditer(m.group(1)):
            api_id = int(m_c.group(1))
            for k, v in kaisou_data.items():        # 此处可优化，但现在我太困了
                # 算了不优化了，这一部分素材是根据“改后的舰船”决定的，可能由多种路径改造而来
                # 最简明的写法就是遍历一遍
                if v['api_id'] == api_id:           
                    v['hokoheso'] = hokoheso_num
                    cur_ship_id = k
                    print(f"{cur_ship_id=}\t{api_id=}\t{hokoheso_num=}")

'''
大和改 -> 大和改二 特殊规则：
case 911:
    return 136 == this.mst_id_before ? 3 : 0;
原本这段代码是根据“改后的舰船”决定炮坟紫菜数量
但对于大和改二，仅对大和改 -> 大和改二需要3个紫菜，改二重->改二不需紫菜
田中代码过于sb，明明直接写到api_start2.json就可以了
'''
kaisou_data[136]['hokoheso'] = 3


# step 3.2: parse main.js again, get DevKit and BuildKit
print('step 3.2: parse main.js again, get DevKit and BuildKit')
rex_devkit = re.compile(r'\w+.prototype._getRequiredDevkitNum *= *function\(\w+, *\w+, *\w+\) *\{\s*switch *\(\w+\) *{\s*(((case *\d+:\s*)+return *\d+;\s*)+)')
rex_buildkit = re.compile(r'\w+.prototype._getRequiredBuildKitNum *= *function\(\w+\) *\{\s*switch *\(\w+\) *{\s*(((case *\d+:\s*)+return *\d+;\s*)+)')
rex_case_ret = re.compile(r'((case *\d+:\s*)+)return *(\d+);\s*')
rex_case = re.compile(r'case *(\d+):')

def add_kaisou_key_value(key_name, rex_func):
    with open(main_js_path, 'r', encoding='utf8') as f:
        ctx = f.read()
        match = rex_func.search(ctx)
        for m_ct in rex_case_ret.finditer(match.group(1)):
            value = int(m_ct.group(3))
            for m_c in rex_case.finditer(m_ct.group(1)):
                c = int(m_c.group(1))
                if c in kaisou_data:
                    kaisou_data[c][key_name] = value
                else:
                    print(f'ERROR: key "{c}" is not in kaisou_data!')

add_kaisou_key_value('devkit', rex_devkit)
add_kaisou_key_value('buildkit', rex_buildkit)


# step 4: get DevKit with another rule. 
#         (At 2021-09-04, only 503: 鈴谷改二 -> 鈴谷航改二 and 504: 熊野改二 -> 熊野航改二 use this rule)
print('step 4: get DevKit with another rule.')
'''
i: steel cost
e: blue print/drawing cost
t: cur_ship_id
this._USE_DEVKIT_GROUP_ = [503, 504];
default:
    return 0 != e && -1 == this._USE_DEVKIT_GROUP_.indexOf(t) ?
        0 :
        i < 4500 ?
        0 :
        i < 5500 ?
        10 :
        i < 6500 ?
        15 :
        20;
'''
rex_use_devkit_group = re.compile(r'this._USE_DEVKIT_GROUP_ *= *\[\s*((\d+,?\s*)+)\]', re.M)
use_devkit_group = []
with open(main_js_path, 'r', encoding='utf8') as f:
    ctx = f.read()
    match = rex_use_devkit_group.search(ctx)
    for m in re.finditer(r'\d+', match.group(1)):
        use_devkit_group.append(int(m.group()))

for k, v in kaisou_data.items():
    if v["devkit"] != 0:
        continue        # 属于上述case的情况，已赋值
    if 0 != v["drawing"] and k not in use_devkit_group:
        v["devkit"] = 0
    else:
        steel = v["steel"]
        v["devkit"] = 0 if steel < 4500 else 10 if steel < 5500 else 15 if steel < 6500 else 20


# print(kaisou_data)

# step 5.1: generate output
print('step 5.1: generate output')
output = {}
output_for_human = {}
for cur_ship_id, item in kaisou_data.items():
    msg = []
    key_name = [
        ("drawing",     "改装设计图"), 
        ("buildkit",    "高速建造材"),
        ("devkit",      "开发资材"),
        ("catapult",    "试制甲板用弹射器"),
        ("report",      "战斗详报"),
        ("aviation",    "新型航空兵装资材"),
        ("hokoheso",    "新型火炮兵装资材"),
        ("arms",        "新型兵装资材"),
        ("boiler",      "新型高温高圧缶"),
    ]
    for key, name in key_name:
        if key in item and item[key] > 0:
            msg.append(f'{name}x{item[key]}')

    if msg:
        output[cur_ship_id] = ' '.join(msg)     # 以cur_ship_id作为key，改造才是唯一的。不能以转换后的船为key，因为一艘船可以由她的上位或下位转换而来，存在多种情况
                                                # 换句话说：舰娘的依改造关系形成一个有向图，每个节点的出度只能是0或1，但入度可以大于1；因此表达改造关系时，可使用「起点」带代指，但不能用「终点」
        name1 = id2name[item["cur_ship_id"]]
        name2 = id2name[item["api_id"]]
        output_for_human[cur_ship_id] = f'{name1} -> {name2}: ' + output[cur_ship_id]
        # sortno1 = id2sortno[item["cur_ship_id"]]
        # sortno2 = id2sortno[item["api_id"]]
        # id2 = item["api_id"]
        # output_for_human[cur_ship_id] = f'{name1}(图鉴{sortno1}) -> {name2}(图鉴{sortno2})(id={id2}): ' + output[cur_ship_id]


# step 5.2: output and save
print('step 5.2: output and save')
for k, v in output_for_human.items():
    print(f'"{k}": "{v}",')

output_path = './kaisou_data.json'
with open(output_path, 'w', encoding='utf8') as f:
    json.dump(output, f, ensure_ascii=False, sort_keys=True, indent=4)
    print(f'saved to {output_path} successfully!')

output_path = './kaisou_data_for_human.json'
with open(output_path, 'w', encoding='utf8') as f:
    json.dump(output_for_human, f, ensure_ascii=False, sort_keys=True, indent=4)
    print(f'saved to {output_path} successfully!')
