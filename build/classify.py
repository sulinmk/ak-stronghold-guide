"""把 PRTS 导出的原始数据整理成叠层速查用的数据。用法：python3 -I classify.py raw.json out.json"""
import json, re, sys

raw = json.load(open(sys.argv[1], encoding="utf-8"))
CORE = ["炎", "萨尔贡", "维多利亚", "谢拉格", "阿戈尔", "叙拉古", "卡西米尔", "乌萨斯", "伊比利亚", "莱塔尼亚"]

# 每个盟约随层数涨什么（从效果原文里归纳）
GAIN = {
    "炎": "攻击力 +0.9%/层",
    "萨尔贡": "开技能攻速的持续时间 +0.22 秒/层；满人后流沙伤害 +25/层",
    "维多利亚": "带装备时伤害 +0.8%/层；每 25 层送一把维式重锤",
    "谢拉格": "对寒冷、冻结敌人伤害 +1%/层；每 100 层送一件不融冰",
    "阿戈尔": "生命值 +1%/层",
    "叙拉古": "部署后攻速 +0.8/层，持续时间 +0.4 秒/层",
    "卡西米尔": "部署叠攻击的上限 +1%/层",
    "乌萨斯": "攻击力 +0.75%/层，生命值 +0.3%/层",
    "伊比利亚": "持续法伤 +0.06%攻击力/秒/层",
    "莱塔尼亚": "干员和召唤物攻击力 +1%/层",
    "精准": "攻击力 +1.2%/层",
    "迅捷": "技能结束回技力的概率 +0.35%/层；40 层起全队生效",
    "灵巧": "攻速 +1/层；40 层起范围扩大到周围 8 格",
    "坚守": "全队生命值 +1.2%/层",
    "助力": "全队防御力 +1.2%/层；本身每回合给所有已激活盟约 +2（3 人 +4）",
    "远见": "每 10 层给 2 资金；80、150 层远见干员各降价 1",
    "奇迹": "免费刷新概率 +0.25%/层；100 层起刷新保底出当前等级干员",
    "投资人": "100 层起“获得时”特质触发 3 次（平时 2 次）",
    "突袭": "再部署期间攻击、生命 +1%/层；50 层起全队攻速 +50",
    "不屈": "被击倒后立刻重新部署的概率 +0.4%/层",
    "调和": "不随层数变化",
    "协防干员": "不随层数变化",
    "独行": "不随层数变化",
    "绝技": "不随层数变化，看场上精锐干员数",
    "聚合": "治疗量 +0.12%攻击力/层",
    "奥术": "附加法伤 +0.4%攻击力/层",
}

AMPLIFY = {"阿米娅", "Mon3tr", "凛御银灰", "薇薇安娜", "塔露拉", "铃兰", "塞雷娅"}
AMPLIFY_NOTE = {
    "阿米娅": "身前一格干员每次叠层额外 +1/+2，不受上限限制",
    "Mon3tr": "周围 8 格干员每场战斗的叠层上限 +30%/+60%",
    "凛御银灰": "身前一格谢拉格、灵巧干员每场战斗叠层上限 +75%/+150%",
    "薇薇安娜": "场上同盟约干员本回合叠层上限 +7/+14",
    "塔露拉": "乌萨斯击倒单位时叠的临时层数提高",
    "铃兰": "每回合重新触发身前 1/2 格干员的“获得时”效果",
    "塞雷娅": "复制身前一格干员的“休整期结束时”特质",
}

def bonds_in(s):
    return re.findall(r"【([^】]+)】", s)

def first_timing(s):
    m = re.match(r"\s*<([^>]+)>", s)
    return m.group(1) if m else ""

def trigger(s):
    for k, v in [("敌人被击倒", "范围内击倒敌人时"), ("部署", "部署时"), ("开启技能", "开技能时"), ("开技能", "开技能时"), ("被击倒", "被击倒时"),
                 ("击倒", "击倒时"), ("冻结", "冻结时"), ("恐惧", "恐惧时"), ("元素损伤爆发", "元素爆发时"),
                 ("沉睡或眩晕", "沉睡或眩晕时")]:
        if k in s:
            return v
    return "战斗中"

def amounts(s):
    return re.findall(r"层数\s*\+\s*(\d+)", s) or re.findall(r"转化(\d+)层", s)

def caps(s1, s2):
    c1 = re.findall(r"(每名干员每回合|每回合|每场战斗)至多叠加(\d+)层", s1)
    c2 = re.findall(r"(?:每名干员每回合|每回合|每场战斗)至多叠加(\d+)层", s2)
    return [f"{a}至多 {b}" + (f" / {c2[i]}" if i < len(c2) else "") for i, (a, b) in enumerate(c1)]

ops = []
for name, tier, bl, gtype, t1, t2 in raw["ops"]:
    both = t1 + " " + t2
    timing = first_timing(t1)
    stacks = bool(re.search(r"层数\s*\+|叠加等同于|转化\d+层|获得等同于", t1))
    consumes = bool(re.search(r"每叠加\d+层", t1))
    if name in AMPLIFY:
        mode = "放大"
    elif stacks:
        if timing == "获得时":
            mode = "一次性"
        elif timing == "战斗中":
            mode = "战斗中"
        else:
            mode = "每回合"
    elif consumes:
        mode = "吃层数"
    else:
        mode = "不叠层"

    # 叠给谁
    scope, targets = "", []
    if mode in ("一次性", "每回合", "战斗中"):
        if "层数最多的盟约" in t1:
            scope = "层数最高的盟约"
        elif "核心盟约" in t1:
            scope = "所有已激活核心盟约"
        elif "整备区每名干员" in t1:
            scope = "整备区每名干员的盟约"
        elif re.search(r"自身(及|以及)身前一格", t1):
            scope = "自己和身前一格干员的盟约"
        elif "自身及身后一格" in t1:
            scope = "自己和身后一格干员的盟约"
        elif "身前一格干员获得特质" in t1:
            scope = "身前一格干员的盟约"
        elif "自身已激活的盟约" in t1:
            scope = "自己所属的全部盟约"
        else:
            targets = [b for b in dict.fromkeys(bonds_in(t1.split(" / <战斗中>")[0])) if b in {x["n"] for x in raw["bonds"]}]
            scope = "、".join(targets)
    if mode == "一次性" and name == "矩":
        targets, scope = ["炎"], "炎"
    if mode == "每回合" and name == "旅骨":
        targets, scope = [], "自己和身前一格干员的盟约"

    if mode == "放大":
        note = AMPLIFY_NOTE[name]
    else:
        note = ""

    when = {"获得时": "拿到时", "休整期结束时": "休整期结束", "进入休整期时": "进入休整期", "战斗结束时": "战斗结束",
            "战斗开始时": "战斗开始", "刷新时": "首次主动刷新", "售出时": "卖出时"}.get(timing, "")
    if timing == "战斗中":
        when = trigger(t1)
    a1, a2 = amounts(t1), amounts(t2)
    amt = ""
    if mode in ("一次性", "每回合", "战斗中"):
        if re.search(r"每有一名|每获得过|每进行过|每消耗|等同于|同一行每有|整备区每有", t1):
            amt = "按条件 "
        if a1:
            amt += "+" + a1[0] + (" / +" + a2[0] if a2 else "")
        elif name == "矩":
            amt = "= 调度中心等级 / ×2"
        elif name == "旅骨":
            amt = "= 售出价格 / ×2"
        elif name == "棘刺":
            amt = "= 场上售价总和 / ×2"
        amt = amt.strip()
        if name in ("折桠", "乌啾"):
            note = "把乌萨斯的临时层数转成固定层数"
        if name == "烈夏":
            note = "加的是乌萨斯临时层数"
    cap = caps(t1, t2)
    if name == "华法琳":
        mode, when, scope = "战斗中", "身前干员开技能时", "身前一格干员的盟约"
        note = "战斗开始时把开技能叠层的特质送给身前一格干员"
    OVR = {
        "黍": dict(a="炎 +8 / +16，远见 +4 / +8"),
        "逻各斯": dict(a="奥术 +10 / +20，远见 +5 / +10", note="另外按奥术、远见层数给自己加攻速"),
        "安洁莉娜": dict(a="每次刷新：叙拉古 +2 / +4，奇迹 +1 / +2"),
        "耀骑士临光": dict(sc="自己和被召唤干员的盟约", note="被击倒时从整备区召唤卡西米尔或突袭干员"),
    }
    if name in OVR:
        o = OVR[name]
        amt = o.get("a", amt); scope = o.get("sc", scope); note = o.get("note", note)
    ops.append({
        "n": name, "t": tier, "b": bl, "gt": gtype, "m": mode, "w": when, "sc": scope, "tg": targets,
        "a": amt, "cap": "；".join(cap), "bench": "整备区也生效" in both, "note": note,
        "eat": consumes, "t1": t1, "t2": t2,
    })

bonds = []
for b in raw["bonds"]:
    e = b["e"]
    full = [int(x) for x in re.findall(r"<在场(\d+)名", e)]
    th = re.findall(r"<((?:每叠加|首次到达|达到)\d+层)>", e)
    members = [o for o in ops if b["n"] in o["b"]]
    stackers = [o for o in members if o["m"] in ("一次性", "每回合", "战斗中") and (b["n"] in o["tg"] or o["sc"] in ("自己所属的全部盟约", "自己和身前一格干员的盟约", "自己和身后一格干员的盟约", "身前一格干员的盟约", "层数最高的盟约", "所有已激活核心盟约", "整备区每名干员的盟约"))]
    outside = [o["n"] for o in ops if b["n"] not in o["b"] and b["n"] in o["tg"]]
    bonds.append({
        "n": b["n"], "core": b["n"] in CORE, "ppl": int(b["ppl"]), "full": max(full) if full else None,
        "th": th, "gain": GAIN[b["n"]], "e": e, "cnt": len(members), "stk": len(stackers), "out": outside,
    })

json.dump({"bonds": bonds, "ops": ops}, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)

# 打印统计，便于人工核对
from collections import Counter
print(Counter(o["m"] for o in ops))
for o in ops:
    if o["m"] in ("一次性", "每回合", "战斗中") and not o["sc"]:
        print("缺少对象:", o["n"], o["t1"])
    if o["m"] in ("一次性", "每回合", "战斗中") and not o["a"]:
        print("缺少数值:", o["n"], o["t1"])
for b in bonds:
    print(b["n"], "成员", b["cnt"], "叠层手", b["stk"], "满人", b["full"], b["th"], "外援", b["out"])
