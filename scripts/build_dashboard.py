#!/usr/bin/env python3
"""board.html 템플릿에 data.json을 주입해 dashboard/index.html을 만든다.

발행된 Artifact는 로컬 파일을 읽을 수 없으므로 데이터를 페이지에 인라인으로 박는다.
즉 갱신 = 재빌드 + 재발행이다. 예시 데이터(demo.json)는 있으면 함께 넣는다.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "dashboard", "board.html")
DATA = os.path.join(ROOT, "dashboard", "data.json")
DEMO = os.path.join(ROOT, "dashboard", "demo.json")
OUT = os.path.join(ROOT, "dashboard", "index.html")


def main():
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "algo.py"), "export"],
                   check=True, capture_output=True)
    with open(TPL, encoding="utf-8") as f:
        html = f.read()
    with open(DATA, encoding="utf-8") as f:
        real = json.load(f)
    demo = real
    if os.path.exists(DEMO):
        with open(DEMO, encoding="utf-8") as f:
            demo = json.load(f)

    def blob(o):
        # </script> 조각이 생기지 않게 막는다 (JSON 문자열 안에서도 안전하다)
        return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")

    html = html.replace("__REAL__", blob(real)).replace("__DEMO__", blob(demo))
    if "__REAL__" in html or "__DEMO__" in html:
        sys.exit("플레이스홀더 치환 실패")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    kb = os.path.getsize(OUT) / 1024
    print(f"{OUT} ({kb:.0f}KB, 기록 {real['totals']['records']}건, 예시 {demo['totals']['records']}건)")


if __name__ == "__main__":
    main()
