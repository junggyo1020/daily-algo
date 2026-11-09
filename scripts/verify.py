#!/usr/bin/env python3
"""하네스 자체 검사 — 문서가 약속한 것과 코드가 하는 일이 어긋났는지 잡는다.

이 저장소에서 가장 위험한 고장은 코드 버그가 아니라 **문서와 코드의 불일치**다.
문서는 "60일 뒤 복습한다"고 하는데 코드가 거기 도달하지 못하면, 사용자는 일어나지
않는 일을 믿고 공부하게 된다. 그런 종류만 골라서 검사한다.

하네스(스킬, 에이전트, 엔진)를 고친 뒤와 월간 점검 때 돌린다:
    python3 scripts/verify.py
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILED = []


def chk(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        FAILED.append(msg)
    return bool(cond)


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


def main():
    os.chdir(ROOT)
    agents = sorted(glob.glob(".claude/agents/*.md"))
    skills = sorted(glob.glob(".claude/skills/*/SKILL.md"))
    code = read("scripts", "algo.py")
    board = read("dashboard", "board.html")
    docs = "".join(read(p) for p in glob.glob(".claude/**/*.md", recursive=True)) + read("README.md") + board

    print("[1] 구조")
    chk(len(agents) == 4, f"에이전트 4개 (현재 {len(agents)})")
    chk(len(skills) == 5, f"스킬 5개 (현재 {len(skills)})")
    chk(not os.path.exists(".claude/commands"), "커맨드 미생성 (하네스는 커맨드를 만들지 않는다)")
    for f in ["scripts/algo.py", "scripts/build_dashboard.py", "data/types.json", "README.md",
              "dashboard/board.html", "dashboard/demo.json",
              ".claude/skills/algo-daily/assets/Solution_template.java",
              ".claude/skills/algo-daily/references/session-protocol.md"]:
        chk(os.path.exists(f), f)

    print("[2] frontmatter")
    for f in agents:
        fm = frontmatter(read(f))
        nm = re.search(r"^name:\s*(\S+)", fm, re.M)
        chk(nm and nm.group(1) == os.path.basename(f)[:-3] and "model: opus" in fm
            and "description:" in fm, f"{os.path.basename(f)} name, description, model:opus")
    for f in skills:
        s = read(f)
        fm = frontmatter(s)
        nm = re.search(r"^name:\s*(\S+)", fm, re.M)
        d = re.search(r"^description:\s*(.+)", fm, re.M)
        dirn = os.path.basename(os.path.dirname(f))
        chk(nm and nm.group(1) == dirn, f"{dirn} name이 폴더명과 일치")
        # description은 스킬의 유일한 트리거다. 짧으면 호출되지 않는다.
        chk(d and len(d.group(1)) >= 120, f"{dirn} description 트리거 구체성 ({len(d.group(1)) if d else 0}자)")
        chk(len(s.splitlines()) <= 500, f"{dirn} 본문 {len(s.splitlines())}줄 (≤500)")

    print("[3] 문서 주장 ↔ 코드 동작")
    grad = re.search(r"if clean >= (\d+):", code)
    chk(grad and f"{grad.group(1)}회 연속" in docs,
        f"복습 졸업 조건: 코드 {grad.group(1) if grad else '?'}회 ↔ 문서 동일")
    iv = re.search(r'"solved_in_time": \[([^\]]+)\]', code)
    chk(iv and all(f"{v.strip()}일" in docs or v.strip() in docs for v in iv.group(1).split(",")),
        f"복습 간격 {iv.group(1) if iv else '?'} 이 문서에 명시됨")
    chk("0.5 ** (days_since / half)" in code and "0.5^(경과일/60)" in docs, "감쇠 공식 일치")
    chk(re.search(r"half_life_days.*60", read("data", "types.json")) and "반감기 60일" in docs,
        "감쇠 반감기 일치")
    for th, lab in [(80, "80 이상"), (60, "60-79"), (35, "35-59")]:
        chk(f"mastery >= {th}" in code and lab in docs, f"상태 구간 {lab}")
    # 평가어가 다시 섞여 들어오지 않는지 지킨다
    banned = ["견고", "양호", "취약", "미진단", "녹슴", "뼈아프", "나쁘지 않", "우상향"]
    for w in banned:
        chk(w not in docs, f"평가어 '{w}' 미사용")
    chk("·" not in docs + code, "가운뎃점(·) 미사용 — 사용자 이름으로 공개되는 문서 규칙")
    # 부정형 대조("A가 아니라 B")는 문장을 길게 만들고 무엇을 말하는지 흐린다
    for w in ["이 아니라", "가 아니라", "에 그치지 않고"]:
        chk(w not in docs, f"부정형 대조 '{w}' 미사용")
    for w in ["표본", "트랙", "커버리지", "터치"]:
        chk(w not in docs, f"전문용어 '{w}' 미사용")
    wg = re.search(r"WEEKLY_GOAL = (\d+)", code)
    chk(wg and f"주 {wg.group(1)}일" in docs, f"주간 목표 {wg.group(1) if wg else '?'}일 일치")
    out_codes = set(re.findall(r'"(solved_\w+|failed)": [\d.]+', code))
    chk(all(o in docs for o in out_codes), "결과 코드 4종이 문서에 모두 설명됨")

    print("[4] 죽은 필드 — 기록만 하고 아무도 읽지 않는 값")
    blk = code[code.index("    rec = {"):code.index("    os.makedirs(os.path.dirname(LOG)")]
    reader = code[code.index("def d(s):"):]
    for f in re.findall(r'^\s+"(\w+)":', blk, re.M):
        used = (re.search(rf'\["{f}"\]', reader) or re.search(rf'\.get\("{f}"', reader)
                or re.search(rf"\.{f}\b", board) or f in docs)
        chk(used, f"log 필드 '{f}' 를 읽는 곳이 있다")

    print("[5] 데이터 흐름 — 산출물을 쓰는 쪽과 읽는 쪽이 맞물리는가")
    weekly = read(".claude/skills/algo-weekly/SKILL.md")
    for art, producer in [("_workspace/01_diagnosis.md", "algo-diagnostician"),
                          ("_workspace/02_curriculum.md", "algo-curriculum-designer"),
                          ("_workspace/scout_result.json", "algo-problem-scout")]:
        chk(art in read(f".claude/agents/{producer}.md"), f"{producer} 가 {art} 를 생산한다고 명시")
    for art in ["_workspace/01_diagnosis.md", "_workspace/02_curriculum.md"]:
        chk(art in weekly, f"algo-weekly 가 {art} 를 소비")
    chk("algo-problem-scout" in read(".claude/agents/algo-curriculum-designer.md"),
        "커리큘럼 설계자가 스카우트를 호출한다고 명시")
    names = {os.path.basename(p)[:-3] for p in agents} | {os.path.basename(os.path.dirname(p)) for p in skills}
    for ref in sorted(set(re.findall(r"algo-[a-z-]+", docs))):
        chk(ref in names, f"참조 '{ref}' 가 실존하는 에이전트/스킬")

    print("[6] 엔진과 빌드 실행")
    for cmd in (["scripts/algo.py", "today"], ["scripts/algo.py", "stats"],
                ["scripts/algo.py", "export"], ["scripts/build_dashboard.py"]):
        r = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
        chk(r.returncode == 0, " ".join(cmd) + ("" if r.returncode == 0 else f" → {r.stderr.strip()[:70]}"))

    data = json.loads(read("dashboard", "data.json"))
    chk(len(data["types"]) == 12, "12유형")
    chk("targets" in data["types"][0], "export에 난이도별 목표시간")
    html = read("dashboard", "index.html")
    chk("__REAL__" not in html and "__DEMO__" not in html, "대시보드 플레이스홀더 치환 완료")
    chk("focus-visible" in html, "키보드 포커스 스타일")
    chk("var(--mid)" not in html, "죽은 CSS 토큰 없음")
    demo = json.loads(re.search(r'id="demo-data" type="application/json">(.*?)</script>',
                                html, re.S).group(1).replace("<\\/", "</"))
    chk("targets" in demo["types"][0], "예시 데이터가 현재 엔진 스키마와 동일")

    print()
    if FAILED:
        print(f"=> 실패 {len(FAILED)}건")
        for m in FAILED:
            print("   -", m)
        return 1
    print("=> 전체 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
