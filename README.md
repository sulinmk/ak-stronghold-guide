# 卫戍协议叠层速查

《明日方舟》卫戍协议·规程（序列Ⅰ）的玩家自制速查表：每个盟约随层数涨什么、有哪些层数门槛，以及 143 名干员按叠层方式（一次性、每回合、战斗中、放大、吃层数）分类。

在线查看：https://sulinmk.github.io/ak-stronghold-guide/

## 文件

- `data/raw.json`：从 PRTS「卫戍协议·规程/PRTS盟约记录」页导出的盟约和干员原始数据（游戏数据版本 26-11-06）
- `build/classify.py`：给干员特质分类、提取叠层对象、数值和上限
- `build/page.html`：网页模板
- `build/build.py`：生成脚本
- `index.html`：生成出来的网页，不要直接改

## 更新

改分类规则改 `build/classify.py`，改页面改 `build/page.html`，然后在仓库根目录运行：

```bash
python3 build/build.py
```

## 来源与授权

数据整理自 [PRTS](https://prts.wiki/w/卫戍协议·规程/PRTS盟约记录)。PRTS 的整理内容采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans) 授权，本仓库也按这个协议发布。游戏文本原文版权归上海鹰角网络科技有限公司。本项目与官方无关。
