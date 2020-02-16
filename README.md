# get_kaisou_data
从main.js与api_start2.json中提取舰娘改造条件的脚本

## 使用方法
```bash
python3 get_kaisou_data.py
```

将自动下载最新的`api_start2.json`和`main.js`，并计算出改修所需特殊素材

注1：弹药、钢材也在计算，未输出。若需要，在step4中输出`kaisou_data`中`item`的`ammo`和`steel`字段即可。
注2：脚本运行需要几分钟时间，请稍事等待。
