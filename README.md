# 卫戍协议·规程速查

《明日方舟》卫戍协议·规程（序列Ⅰ）的玩家自制速查表：

- 叠层：每个盟约随层数涨什么、有哪些层数门槛，以及 143 名干员按叠层方式（一次性、每回合、战斗中、放大、吃层数）分类。
- 经济：调度中心各级升级费用和栏位、干员和装备价格、各模式回合安排、61 个策略的初始生命和经济效果，以及和资金有关的干员、盟约。

在线查看：https://sulinmk.github.io/ak-stronghold-guide/

## 文件

- `data/raw.json`：从 PRTS「卫戍协议·规程/PRTS盟约记录」页导出的盟约和干员原始数据（游戏数据版本 26-11-06）
- `data/gamedata.json`：从国服客户端数据摘出的经济表，由 `build/fetch_gamedata.py` 生成
- `build/classify.py`：给干员特质分类、提取叠层对象、数值和上限
- `build/econ.py`：整理经济页数据，策略的经济标签和经济干员名单在这里手工维护
- `build/fetch_gamedata.py`：下载客户端数据并摘出经济表（需要联网；换赛季改里面的 `ACT_ID`）
- `build/page.html`：网页模板
- `build/build.py`：生成脚本
- `index.html`：生成出来的网页，不要直接改

## 更新

改分类规则改 `build/classify.py`，改经济页改 `build/econ.py`，改页面改 `build/page.html`，然后在仓库根目录运行：

```bash
python3 build/build.py
```

游戏更新后想刷新经济数值，先运行：

```bash
python3 -I build/fetch_gamedata.py
```

每回合发多少资金、调度中心各级刷出各阶干员的概率，客户端数据里没有，目前没有收录。

## 来源与授权

盟约和干员数据整理自 [PRTS](https://prts.wiki/w/卫戍协议·规程/PRTS盟约记录)，规则说明参考 [PRTS · 卫戍协议/帮助](https://prts.wiki/w/卫戍协议/帮助)。PRTS 的整理内容采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans) 授权，本仓库也按这个协议发布。经济数值取自 [ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData) 收录的国服客户端数据。游戏文本和数据版权归上海鹰角网络科技有限公司。本项目与官方无关。
