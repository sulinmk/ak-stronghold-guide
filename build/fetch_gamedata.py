"""从游戏客户端数据里摘出经济相关的表，写到 data/gamedata.json。

用法（在仓库根目录运行，需要联网）：
    python3 -I build/fetch_gamedata.py

数据源是 Kengxxiao/ArknightsGameData 的国服 activity_table.json（约 15MB，只在内存里处理，
不落盘）。换赛季时把 ACT_ID 改成新活动的编号。
"""
import json
import pathlib
import re
import urllib.request

URL = "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/activity_table.json"
ACT_ID = "act3autochess"  # 卫戍协议·规程

root = pathlib.Path(__file__).resolve().parent.parent
with urllib.request.urlopen(URL, timeout=120) as r:
    table = json.load(r)

basic = table["basicInfo"][ACT_ID]
act = next(iter(table["activity"]["AUTOCHESS"][ACT_ID].values()))
acd = table["autoChessData"]
strip = lambda s: re.sub(r"<[@$/][^>]*>", "", s or "").replace("\\n", "\n").strip()

modes = {}
for mid, m in act["modeDataDict"].items():
    battles = act["battleDataDict"].get(mid, {})
    rounds = sorted(battles, key=int)
    modes[mid] = {
        "name": m["name"], "code": m["code"], "type": m["modeType"],
        "rounds": len(rounds),
        "special": [int(r) for r in rounds if any(x["isSpPrepare"] for x in battles[r])],
        "boss": [int(r) for r in rounds if any(x["bossId"] for x in battles[r])],
        "shop": [
            {"lv": int(lv), "up": v["initialUpgradePrice"], "chars": v["charChessCount"], "items": v["itemCount"]}
            for lv, v in sorted(act["shopLevelDataDict"].get(mid, {}).items(), key=lambda x: int(x[0]))
        ],
    }

prices = {
    int(tier): {"buy": lst[0]["purchasePrice"], "sell": lst[0]["chessSoldPrice"],
                "buyElite": lst[1]["purchasePrice"], "sellElite": lst[1]["chessSoldPrice"]}
    for tier, lst in act["shopCharChessInfoData"].items()
}

equips = {}
for iid, s in act["trapShopChessDatas"].items():
    if s["itemType"] != "EQUIP" or s["hideInShop"]:
        continue
    p = act["trapChessDataDict"].get(iid, {}).get("purchasePrice")
    if p is not None:
        equips.setdefault(s["itemLevel"], []).append(p)

bands = []
for bid, b in act["bandDataListDict"].items():
    bands.append({
        "id": bid, "name": acd["bandDataDict"].get(bid, {}).get("bandName", bid),
        "type": b["bandType"], "hp": b["totalHp"], "desc": strip(b["bandDesc"]),
    })

c = act["constData"]
out = {
    "season": basic["name"], "startTime": basic["startTime"], "contentUpdateTime": c.get("contentUpdateTime"),
    "const": {k: c[k] for k in ("shopRefreshPrice", "maxDeckChessCnt", "maxDeckEquipmentChessCnt",
                                "maxBattleChessCnt", "costPlayerHpLimit", "storeCntMax")},
    "modes": modes, "prices": prices,
    "equips": {lv: sorted(v) for lv, v in sorted(equips.items())},
    "bands": bands,
}
(root / "data/gamedata.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("已写入 data/gamedata.json：", len(modes), "个模式，", len(bands), "个策略")
