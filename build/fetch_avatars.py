"""下载干员头像，缩小成 64×64 的 webp，存到 assets/avatars/<charId>.webp。

用法（在仓库根目录运行，需要联网，需要 cwebp：brew install webp）：
    python3 -I build/fetch_avatars.py

对应表在 data/avatars.json（干员名 → charId，以及素材仓库的固定版本）。
已经存在的文件会跳过；素材库里没有的编号会列出来，页面上对应位置不显示头像。
图从 jsDelivr 镜像取（本机直连 raw.githubusercontent.com 不稳定）。
"""
import concurrent.futures as cf
import json
import pathlib
import subprocess
import tempfile
import urllib.error
import urllib.request

root = pathlib.Path(__file__).resolve().parent.parent
cfg = json.loads((root / "data/avatars.json").read_text(encoding="utf-8"))
ref = cfg["sourceRef"]
out_dir = root / "assets/avatars"
out_dir.mkdir(parents=True, exist_ok=True)
ids = sorted(set(cfg["map"].values()))


def fetch(cid):
    dst = out_dir / f"{cid}.webp"
    if dst.exists():
        return cid, "skip"
    # jsDelivr 对个别文件固定返回 403，拿不到时改走 GitHub 接口取原文件（不带令牌，每小时限 60 次）
    sources = [
        urllib.request.Request(f"https://cdn.jsdelivr.net/gh/yuanyan3060/ArknightsGameResource@{ref}/avatar/{cid}.png"),
        urllib.request.Request(f"https://api.github.com/repos/yuanyan3060/ArknightsGameResource/contents/avatar/{cid}.png?ref={ref}",
                               headers={"Accept": "application/vnd.github.raw"}),
    ]
    data, errs = None, []
    for req in sources:
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            break
        except Exception as e:  # 换下一个来源；都失败就下次重跑再补
            errs.append(str(getattr(e, "code", e)))
    if data is None:  # 最后用本机已登录的 gh 读公开文件，额度比匿名接口高
        r = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                            f"repos/yuanyan3060/ArknightsGameResource/contents/avatar/{cid}.png?ref={ref}"],
                           capture_output=True)
        if r.returncode == 0 and r.stdout[:8] == b"\x89PNG\r\n\x1a\n":
            data = r.stdout
        else:
            errs.append("gh " + r.stderr.decode(errors="ignore").strip()[:60])
    if data is None:
        return cid, "failed (" + " / ".join(errs) + ")"
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        tmp.write(data)
        tmp.flush()
        subprocess.run(["cwebp", "-quiet", "-q", "80", "-resize", "64", "64", tmp.name, "-o", str(dst)], check=True)
    return cid, "ok"


with cf.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(fetch, ids))
bad = [(c, s) for c, s in results if s not in ("ok", "skip")]
print("共", len(ids), "个编号；新下载", sum(s == "ok" for _, s in results), "；跳过", sum(s == "skip" for _, s in results))
for c, s in bad:
    print("  没拿到：", c, s)
