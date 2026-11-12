"""把 data/gamedata.json 和 data/ops.json 整理成经济页用的数据。用法：python3 -I econ.py gamedata.json ops.json out.json"""
import json
import re
import sys

g = json.load(open(sys.argv[1], encoding="utf-8"))
ops = json.load(open(sys.argv[2], encoding="utf-8"))

# 模式按「调度中心表」和「回合安排」分组，表一样的合成一行
ORDER = ["mode_single_funny", "mode_multi_funny", "mode_multi_normal", "mode_multi_hard", "mode_multi_abyss"] + \
        [f"mode_single_{i}" for i in range(1, 21)]
def group(keyfn):
    groups = []
    for mid in ORDER:
        m = g["modes"][mid]
        k = keyfn(m)
        for gr in groups:
            if gr["key"] == k:
                gr["modes"].append(m["name"]); break
        else:
            groups.append({"key": k, "modes": [m["name"]], "m": m})
    return groups

def label(names):
    # 「规程等级1」…「规程等级20」连续的缩写成一段
    lv = [int(n[4:]) for n in names if n.startswith("规程等级")]
    rest = [n for n in names if not n.startswith("规程等级")]
    if lv:
        rest.append(f"规程等级 {min(lv)}–{max(lv)}" if len(lv) > 1 else f"规程等级 {lv[0]}")
    return "、".join(rest)

shop = []
for gr in group(lambda m: json.dumps(m["shop"])):
    rows, total = [], 0
    levels = gr["m"]["shop"]
    for i, r in enumerate(levels):
        last = i == len(levels) - 1
        rows.append({"lv": r["lv"], "chars": r["chars"], "items": r["items"],
                     "up": None if last else r["up"], "total": total})
        if not last:
            total += r["up"]
    shop.append({"label": label(gr["modes"]), "rows": rows})

rounds = [{"label": label(gr["modes"]), "rounds": gr["m"]["rounds"], "special": gr["m"]["special"], "boss": gr["m"]["boss"]}
          for gr in group(lambda m: (m["rounds"], tuple(m["special"]), tuple(m["boss"])))]

prices = [{"tier": int(t), **p} for t, p in sorted(g["prices"].items(), key=lambda x: int(x[0]))]
equips = [{"tier": int(t), "min": min(v), "max": max(v), "n": len(v)} for t, v in g["equips"].items()]

# 策略：按效果原文打标签，标出和资金、调度中心有关的
TAGS = [
    ("给资金", r"获得[^，。]{0,6}资金|资金\+|额外获得\d+资金|资金可以继承|资金暂存|获得等同损失生命值的资金"),
    ("省钱", r"价格-|消耗资金-|消耗资金为1|升级消耗资金-"),
    ("刷新·换货", r"刷新"),
    ("送干员", r"获得\d+名|获[得取]当前调度中心|免费获[得取]其中1名|获得.{0,4}干员"),
    ("送装备", r"获得\d*件|免费获取其中1件"),
]
# 自动标签不准的，手工改
TAG_FIX = {
    "娜仁图亚": ["省钱"],                # 「获得3名萨尔贡干员」是条件，不是奖励
    "巫恋": ["刷新·换货"], "风丸": ["刷新·换货"], "引星棘刺": ["刷新·换货"],
    "复奏": ["送干员"],                  # 多一次晋升奖励 = 多选一名高一阶干员
}
bands = []
for b in g["bands"]:
    tags = TAG_FIX.get(b["name"]) or [t for t, rx in TAGS if re.search(rx, b["desc"])]
    title = re.match(r"【([^】]+)】", b["desc"])
    bands.append({"name": b["name"], "skill": title.group(1) if title else "", "hp": b["hp"],
                  "bond": b["type"] == "BONDRELEVANT", "tags": tags,
                  "desc": re.sub(r"^【[^】]+】\n?", "", b["desc"])})
bands.sort(key=lambda b: (-b["hp"], b["name"]))

# 和钱、调度中心有关的干员（手工挑的；只按层数加属性的不算）
ECON_OPS = {
    "奥斯塔": "免费刷新", "忍冬": "免费刷新", "灵知": "特殊刷新",
    "真理": "买价 1", "至简": "买价 1",
    "波登可": "卖出后给资金", "海沫": "卖出价会涨", "温蒂": "卖出价高",
    "吉星": "卖出换干员", "伊桑": "卖出换干员", "酒神": "每回合送装备",
}
NOT_ECON = {"复奏", "矩", "旅骨", "安洁莉娜", "棘刺", "溯光星源"}  # 提到刷新/售价/调度中心，但只是叠层
by_name = {o["n"]: o for o in ops["ops"]}
missing = [n for n in ECON_OPS if n not in by_name]
if missing:
    sys.exit(f"ECON_OPS 里有干员不在数据里：{missing}")
econ_ops = [{"n": n, "t": by_name[n]["t"], "b": by_name[n]["b"], "tag": tag, "t1": by_name[n]["t1"], "t2": by_name[n]["t2"]}
            for n, tag in ECON_OPS.items()]
econ_ops.sort(key=lambda o: (o["tag"], o["t"]))
econ_bonds = [{"n": b["n"], "ppl": b["ppl"], "e": b["e"]} for b in ops["bonds"] if b["n"] in ("远见", "奇迹")]

json.dump({"const": g["const"], "season": g["season"], "shop": shop, "rounds": rounds, "prices": prices,
           "equips": equips, "bands": bands, "ops": econ_ops, "bonds": econ_bonds},
          open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False)

# 打印出来便于人工核对
for s in shop:
    print("调度中心表：", s["label"], [(r["lv"], r["up"], r["chars"]) for r in s["rows"]])
for r in rounds:
    print("回合：", r["label"], r["rounds"], "特殊", r["special"], "领袖", r["boss"])
print("经济相关策略：", sum(1 for b in bands if b["tags"]), "/", len(bands))
for o in ops["ops"]:
    if re.search("资金|刷新|购买|售出|出售|价格|调度中心", o["t1"] + o["t2"]) and o["n"] not in ECON_OPS and o["n"] not in NOT_ECON:
        print("新出现、还没归类的干员：", o["n"], o["t1"])
