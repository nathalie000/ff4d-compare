"""Build a 6-row comparison gallery: for each consist4D object, stack the
ff4d (SLat->gaussian) row above the SS-flow (occupancy) row for each of the
three methods (full-attn / spatial-temporal / baseline per-frame). Pairing
appearance over structure lets you tell whether SS-flow or SLat-flow is the
failure: if the occupancy row is clean but the gaussian row is broken -> SLat;
if the occupancy is also broken -> SS.

Outputs <cat>__<obj>.mp4 per object + index.html (GitHub-servable gallery).
"""
import os, subprocess, glob, base64, sys

ROOT = "/home/ncc2/ff4d"
OUT = os.path.join(ROOT, "runs/compare_ssflow_vs_ff4d_consist4D_stride4")
STITCH = os.path.join(ROOT, "src/ff4d/stitch/stitch_compare_grid.py")

# (run_dir, relative path within <cat>/<obj>, row label) — order = top->bottom
ROWS = [
    ("infer_ff4d_500_consist4D_stride4",     "sample_grid.mp4",                  "FF4D full-attn  ·  SLat -> gaussian"),
    ("infer_ss_flow_500_consist4D_stride4",  "sample_grid.mp4",                  "SS-flow full-attn  ·  occupancy"),
    ("infer_ff4d_500_st_consist4D_stride4",  "sample_grid.mp4",                  "FF4D spatial-temporal  ·  SLat -> gaussian"),
    ("infer_ss_flow_500_st_consist4D_stride4","sample_grid.mp4",                 "SS-flow spatial-temporal  ·  occupancy"),
    ("infer_ff4d_500_consist4D_stride4",     "baseline_perframe/sample_grid.mp4","Baseline per-frame  ·  SLat -> gaussian"),
    ("infer_ss_flow_500_consist4D_stride4",  "baseline_perframe/sample_grid.mp4","Baseline per-frame  ·  occupancy"),
]


def objects():
    base = os.path.join(ROOT, "runs", ROWS[0][0])
    objs = sorted("/".join(p.split("/")[-3:-1]) for p in glob.glob(f"{base}/*/*/"))
    return objs


def stitch_one(obj):
    cat, name = obj.split("/")
    out_mp4 = os.path.join(OUT, f"{cat}__{name}.mp4")
    rows = []
    for run_dir, rel, label in ROWS:
        p = os.path.join(ROOT, "runs", run_dir, obj, rel)
        if not os.path.isfile(p):
            print(f"  SKIP {obj}: missing {run_dir}/{rel}")
            return None
        rows += ["--row", p, label]
    cmd = [sys.executable, STITCH, "--out", out_mp4, *rows]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  FAIL {obj}: {r.stderr.strip()[-300:]}")
        return None
    return out_mp4


def write_gallery():
    mp4s = sorted(f for f in os.listdir(OUT) if f.endswith(".mp4"))
    cards = []
    for f in mp4s:
        stem = f[:-4]
        cat, _, obj = stem.partition("__")
        title = obj.replace("_", " ") or stem
        cards.append(f"""    <figure class="card">
      <figcaption><span class="cat">{cat}</span> {title}</figcaption>
      <video src="{f}" autoplay loop muted playsinline controls preload="metadata"></video>
    </figure>""")
    legend = ("Each clip stacks 6 rows (6 views/row). Methods are paired "
              "<b>appearance over structure</b>: "
              "1 FF4D full-attn (gaussian) · 2 SS-flow full-attn (occupancy) · "
              "3 FF4D spatial-temporal (gaussian) · 4 SS-flow spatial-temporal (occupancy) · "
              "5 baseline per-frame (gaussian) · 6 baseline per-frame (occupancy). "
              "If the occupancy row is clean but the gaussian row is broken, SLat-flow is failing; "
              "if occupancy is also broken, SS-flow is failing.")
    html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SS-flow vs FF4D (SLat) — consist4D stride4 ({len(mp4s)} objects)</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin:0; background:#111; color:#eee; font-family: system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }}
  header {{ padding:18px 22px; border-bottom:1px solid #333; position:sticky; top:0; background:#111; z-index:1; }}
  header h1 {{ font-size:18px; margin:0 0 6px; }}
  header p {{ margin:0; color:#aaa; font-size:13px; line-height:1.5; }}
  header b {{ color:#eee; }}
  .grid {{ display:grid; gap:18px; padding:22px; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); }}
  .card {{ margin:0; background:#1a1a1a; border:1px solid #2a2a2a; border-radius:10px; overflow:hidden; }}
  figcaption {{ padding:8px 12px; font-size:13px; border-bottom:1px solid #2a2a2a; }}
  .cat {{ color:#7aa2ff; font-size:11px; text-transform:uppercase; letter-spacing:.04em; margin-right:6px; }}
  video {{ width:100%; display:block; background:#000; }}
</style></head>
<body>
<header>
  <h1>SS-flow vs FF4D (SLat) — consist4D, frame-stride 4 — {len(mp4s)} objects</h1>
  <p>{legend}</p>
</header>
<div class="grid">
{chr(10).join(cards)}
</div>
</body></html>
"""
    with open(os.path.join(OUT, "index.html"), "w") as fh:
        fh.write(html)
    print(f"wrote {OUT}/index.html  ({len(mp4s)} videos)")


def main():
    os.makedirs(OUT, exist_ok=True)
    objs = objects()
    print(f"[gallery] {len(objs)} objects")
    ok = 0
    for o in objs:
        if stitch_one(o):
            ok += 1
            print(f"  ok {o}  ({ok}/{len(objs)})")
    write_gallery()
    print(f"[gallery] stitched {ok}/{len(objs)} -> {OUT}")


if __name__ == "__main__":
    main()
