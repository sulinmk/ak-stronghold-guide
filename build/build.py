"""生成规程速查网页（叠层 + 经济）。

用法（在仓库根目录运行）：
    python3 build/build.py

读 data/raw.json（从 PRTS 导出的盟约和干员）和 data/gamedata.json（从客户端数据摘出的经济表，
由 build/fetch_gamedata.py 生成），分别用 build/classify.py、build/econ.py 整理，
再把结果嵌进 build/page.html，输出 index.html。
"""
import json
import pathlib
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parent.parent
subprocess.run([sys.executable, "-I", str(root / "build/classify.py"),
                str(root / "data/raw.json"), str(root / "data/ops.json")], check=True)
subprocess.run([sys.executable, "-I", str(root / "build/econ.py"), str(root / "data/gamedata.json"),
                str(root / "data/ops.json"), str(root / "data/econ.json")], check=True)

merged = json.loads((root / "data/ops.json").read_text(encoding="utf-8"))
merged["econ"] = json.loads((root / "data/econ.json").read_text(encoding="utf-8"))
data = json.dumps(merged, ensure_ascii=False).replace("</", "<\\/")
page = (root / "build/page.html").read_text(encoding="utf-8").replace("/*__DATA__*/null", data)
page = page.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
head, body = page.split("</style>", 1)
html = ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + head + "</style>\n</head>\n<body>" + body + "\n</body>\n</html>\n")
(root / "index.html").write_text(html, encoding="utf-8")
print("已生成 index.html，", len(html), "字节")
