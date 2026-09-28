# story/fetch/*.json içindeki imzalı ses bağlantılarını indirir, sessizliği kırpar
# ve story/audio altına yazar. GitHub Actions içinde çalışır.
import glob, json, os, subprocess, sys, tempfile, urllib.request

ok = bad = 0
for jf in sorted(glob.glob("story/fetch/*.json")):
    items = json.load(open(jf, encoding="utf-8"))
    for it in items:
        out = it["out"]
        if not out.startswith("story/audio/") or ".." in out:
            print("atlandı (geçersiz yol):", out); bad += 1; continue
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                with urllib.request.urlopen(it["url"], timeout=60) as r:
                    tmp.write(r.read())
            if it.get("raw"):
                os.replace(tmp.name, out)
            else:
                af = ("silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                      "silenceremove=start_periods=1:start_threshold=-50dB,areverse,afade=t=in:d=0.02")
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp.name, "-af", af,
                                "-c:a", "libmp3lame", "-b:a", "96k", out], check=True)
                os.unlink(tmp.name)
            print("indirildi:", out, os.path.getsize(out)); ok += 1
        except Exception as e:
            print("HATA:", out, e); bad += 1
    os.remove(jf)
print(f"tamam {ok}, hata {bad}")
