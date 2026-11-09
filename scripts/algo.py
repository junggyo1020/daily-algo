#!/usr/bin/env python3
"""daily-algo 학습 엔진.

log.jsonl 하나를 단일 진실 원천으로 삼고, 숙련도, 복습큐, 스트릭, 대시보드 데이터를
모두 거기서 파생한다. 상태를 따로 저장하지 않으므로 기록과 지표가 어긋날 수 없다.

사용법:
  algo.py log   --platform P --id ID --title T --level N --types t04[,t06] \
                --minutes M --outcome solved_in_time [--attempts N] \
                [--errors 경계조건,구현실수] [--note "..."] [--target 분] \
                [--path src/...] [--mode new|review] [--date YYYY-MM-DD]
  algo.py today     오늘 무엇을 풀어야 하는지 추천
  algo.py stats     터미널 요약
  algo.py export    dashboard/data.json 생성
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "data", "log.jsonl")
TYPES = os.path.join(ROOT, "data", "types.json")
OUT = os.path.join(ROOT, "dashboard", "data.json")

WEEKLY_GOAL = 5

# 결과별 점수. 1차 시도에 제한시간 내 정답만 1.0으로 둔다 — 코딩테스트는
# 시간 압박이 본질이므로 "풀긴 풀었다"를 만점으로 치면 숙련도가 과대평가된다.
OUTCOME_SCORE = {
    "solved_in_time": 1.0,
    "solved_over_time": 0.7,
    "solved_with_hint": 0.4,
    "failed": 0.1,
}
# 결과별 다음 복습 간격(일). 실패는 바로 다음날, 깔끔한 정답은 길게 미룬다.
REVIEW_INTERVAL = {
    "failed": 1,
    "solved_with_hint": 3,
    "solved_over_time": 7,
    "solved_in_time": [21, 60],  # 연속 정답 횟수에 따라
}
RECENCY_WEIGHT = 0.8  # 평균을 낼 때 최근 시도에 더 큰 가중치


def today() -> date:
    return date.today()


def load_types():
    with open(TYPES, encoding="utf-8") as f:
        return json.load(f)


def d(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def parse_date(s, where="--date"):
    try:
        return d(s)
    except ValueError:
        sys.exit(f"{where} 는 YYYY-MM-DD 형식이어야 한다: {s!r}")


def load_log():
    if not os.path.exists(LOG):
        return []
    out = []
    with open(LOG, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError as e:
                sys.exit(f"log.jsonl {i}번째 줄이 깨졌다: {e}")
            # 여기서 막지 않으면 깨진 한 줄이 이후 모든 명령을 크래시시킨다
            missing = [k for k in ("date", "key", "types", "outcome", "mode") if k not in r]
            if missing:
                sys.exit(f"log.jsonl {i}번째 줄에 필수 키가 없다: {missing}")
            parse_date(r["date"], f"log.jsonl {i}번째 줄의 date")
            if r["outcome"] not in OUTCOME_SCORE:
                sys.exit(f"log.jsonl {i}번째 줄의 outcome이 알 수 없는 값이다: {r['outcome']}")
            out.append(r)
    out.sort(key=lambda r: r["date"])
    return out


def type_target(cfg, type_id, level):
    """유형×난이도 목표시간. types.json에 없는 난이도(Lv.4, Lv.5)는 가장 높은 단계로 올려 쓴다."""
    t = next((x for x in cfg["types"] if x["id"] == type_id), None)
    if not t:
        return 0
    tm = t["target_minutes"]
    key = str(level)
    if key not in tm:
        key = max(tm, key=lambda k: int(k))
    return tm[key]


# --------------------------------------------------------------------------- log
def cmd_log(args):
    cfg = load_types()
    valid_types = {t["id"]: t["name"] for t in cfg["types"]}
    valid_errors = {e["id"] for e in cfg["error_causes"]}

    if args.outcome not in OUTCOME_SCORE:
        sys.exit(f"outcome은 {list(OUTCOME_SCORE)} 중 하나여야 한다: {args.outcome}")
    tids = [t.strip() for t in args.types.split(",") if t.strip()]
    bad = [t for t in tids if t not in valid_types]
    if bad:
        sys.exit(f"알 수 없는 유형 id: {bad} (가능: {sorted(valid_types)})")
    errs = [e.strip() for e in (args.errors or "").split(",") if e.strip()]
    bad = [e for e in errs if e not in valid_errors]
    if bad:
        sys.exit(f"알 수 없는 오답원인: {bad} (가능: {sorted(valid_errors)})")
    if args.outcome != "solved_in_time" and not errs:
        sys.exit("정답(제한시간내)이 아니면 --errors 로 오답원인을 최소 1개 분류해야 한다")

    rec_date = parse_date(args.date).isoformat() if args.date else today().isoformat()
    target = args.target or type_target(cfg, tids[0], args.level)

    rec = {
        "date": rec_date,
        "key": f"{args.platform}:{args.id}",
        "title": args.title,
        "level": args.level,
        "url": args.url or "",
        "types": tids,
        "minutes": args.minutes,
        "target_minutes": target,
        "outcome": args.outcome,
        "attempts": args.attempts,
        "errors": errs,
        "note": args.note or "",
        "solution_path": args.path or "",
        "mode": args.mode,
    }
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"기록 완료: {rec['date']} {rec['title']} "
          f"[{', '.join(valid_types[t] for t in tids)}] {rec['outcome']} "
          f"({rec['minutes']}분 / 목표 {target}분)")


# ---------------------------------------------------------------------- 파생 지표
def mastery_table(cfg, log, ref=None):
    """유형별 숙련도. 최근 시도에 가중을 주고, 마지막 시도 이후 경과일로 감쇠시킨다.

    감쇠를 넣는 이유: 목표가 '녹슬지 않게'이므로 한 번 잘 풀었다는 사실보다
    '최근에도 되는가'가 중요하다. 반감기 60일이면 30일 방치 시 약 71%로 떨어진다.
    """
    ref = ref or today()
    half = cfg.get("half_life_days", 60)
    by_type = defaultdict(list)
    for r in log:
        for t in r["types"]:
            by_type[t].append(r)

    rows = []
    for t in cfg["types"]:
        recs = sorted(by_type.get(t["id"], []), key=lambda r: r["date"])
        if not recs:
            rows.append({
                "id": t["id"], "name": t["name"], "mastery": 0, "base": 0,
                "samples": 0, "last_seen": None, "days_since": None,
                "status": "표본 0", "avg_minutes": None,
                "target_minutes": t["target_minutes"].get("2"),
                "targets": t["target_minutes"],
                "outcomes": {}, "concepts": t["concepts"],
            })
            continue
        num = den = 0.0
        for k, r in enumerate(reversed(recs)):
            w = RECENCY_WEIGHT ** k
            num += w * OUTCOME_SCORE[r["outcome"]]
            den += w
        base = num / den
        last = d(recs[-1]["date"])
        days_since = (ref - last).days
        recency = 0.5 ** (days_since / half)
        mastery = round(100 * base * recency)
        # 평가어("견고", "취약") 대신 점수 구간을 그대로 노출한다.
        # 평가어는 읽는 사람마다 기준이 달라지고, 구간은 기준이 화면에 드러난다.
        if mastery >= 80:
            status = "80 이상"
        elif mastery >= 60:
            status = "60-79"
        elif mastery >= 35:
            status = "35-59"
        else:
            status = "35 미만"
        mins = [r["minutes"] for r in recs[-3:] if r.get("minutes")]
        # 목표시간은 실제로 푼 문제들의 목표를 평균낸다. 고정 Lv.2 기준으로 비교하면
        # Lv.3 문제를 푼 유형이 늘 "느린" 것처럼 보인다.
        tgts = [r["target_minutes"] for r in recs[-3:] if r.get("target_minutes")]
        rows.append({
            "id": t["id"], "name": t["name"], "mastery": mastery,
            "base": round(base * 100), "samples": len(recs),
            "last_seen": recs[-1]["date"], "days_since": days_since,
            "status": status,
            "avg_minutes": round(sum(mins) / len(mins), 1) if mins else None,
            "target_minutes": round(sum(tgts) / len(tgts)) if tgts else t["target_minutes"].get("2"),
            "targets": t["target_minutes"],
            "outcomes": dict(Counter(r["outcome"] for r in recs)),
            "concepts": t["concepts"],
        })
    return rows


def review_queue(log, ref=None):
    """문제별 다음 복습일. 간격 반복이 이 루틴의 핵심 장치다.

    새 문제만 계속 푸는 공부는 쌓이지 않는다. 틀린 문제를 1, 3, 7, 21, 60일 간격으로
    다시 풀어 '그때 왜 틀렸는지'가 반사신경이 될 때까지 끌고 간다.
    """
    ref = ref or today()
    by_key = defaultdict(list)
    for r in log:
        by_key[r["key"]].append(r)

    q = []
    for key, recs in by_key.items():
        recs.sort(key=lambda r: r["date"])
        clean = 0
        for r in recs:
            clean = clean + 1 if r["outcome"] == "solved_in_time" else 0
        last = recs[-1]
        if last["outcome"] == "solved_in_time":
            if clean >= 3:
                continue  # 졸업 — 21일과 60일 확인을 모두 통과했다
            interval = REVIEW_INTERVAL["solved_in_time"][min(clean - 1, 1)]
        else:
            interval = REVIEW_INTERVAL[last["outcome"]]
        nxt = d(last["date"]) + timedelta(days=interval)
        q.append({
            "key": key, "title": last["title"], "level": last["level"],
            "types": last["types"], "url": last.get("url", ""),
            "last_date": last["date"], "last_outcome": last["outcome"],
            "errors": last.get("errors", []), "interval": interval,
            "solution_path": last.get("solution_path", ""),
            "platform": key.split(":", 1)[0],
            "next_review": nxt.isoformat(), "days_until": (nxt - ref).days,
            "total_attempts": len(recs),
        })
    q.sort(key=lambda x: x["days_until"])
    return q


def streaks(log, ref=None):
    ref = ref or today()
    days = sorted({r["date"] for r in log})
    day_streak = 0
    if days:
        cur = d(days[-1])
        if (ref - cur).days <= 1:  # 오늘 아직 안 했어도 어제까지면 살아있다
            day_streak = 1
            s = set(days)
            while (cur - timedelta(days=1)).isoformat() in s:
                cur -= timedelta(days=1)
                day_streak += 1

    by_week = Counter()
    for ds in days:
        y, w, _ = d(ds).isocalendar()
        by_week[(y, w)] += 1
    cy, cw, _ = ref.isocalendar()
    week_streak = 0
    probe = ref - timedelta(days=7)
    while True:
        y, w, _ = probe.isocalendar()
        if by_week.get((y, w), 0) >= WEEKLY_GOAL:
            week_streak += 1
            probe -= timedelta(days=7)
        else:
            break
    return {
        "day": day_streak,
        "week": week_streak,
        "this_week": by_week.get((cy, cw), 0),
        "weekly_goal": WEEKLY_GOAL,
    }


def phase_of(rows):
    """커리큘럼 단계는 달짜가 아니라 상태로 정한다 — 교대근무로 날짜가 밀려도
    단계가 멋대로 넘어가지 않게 하려는 것이다."""
    if any(r["samples"] == 0 for r in rows):
        return "진단"
    if any(r["mastery"] < 60 for r in rows):
        return "보강"
    return "실전"


def recommend(cfg, log, ref=None):
    ref = ref or today()
    rows = mastery_table(cfg, log, ref)
    phase = phase_of(rows)
    q = review_queue(log, ref)
    by_id = {r["id"]: r for r in rows}
    order = [t["id"] for t in cfg["types"]]

    overdue = [x for x in q if x["days_until"] <= -2]
    due = [x for x in q if x["days_until"] <= 0]
    cy, cw, _ = ref.isocalendar()
    reviews_this_week = sum(
        1 for r in log
        if r["mode"] == "review" and d(r["date"]).isocalendar()[:2] == (cy, cw)
    )

    if overdue:
        pick = overdue[0]
        return {"phase": phase, "mode": "review", "target": pick,
                "reason": f"복습이 {-pick['days_until']}일 밀렸다. 밀린 복습이 2일 이상이면 신규보다 먼저 처리한다.",
                "suggested_level": pick["level"], "rows": rows, "queue": q}

    if phase == "진단":
        untouched = [i for i in order if by_id[i]["samples"] == 0]
        if untouched:
            tid = untouched[0]
            return {"phase": phase, "mode": "new", "type": by_id[tid],
                    "reason": f"진단 단계다. 12유형 중 아직 손대지 않은 {len(untouched)}개가 남았고 커리큘럼 순서상 {by_id[tid]['name']} 차례다.",
                    "suggested_level": 2, "rows": rows, "queue": q}

    if due and reviews_this_week < 2:
        pick = due[0]
        return {"phase": phase, "mode": "review", "target": pick,
                "reason": f"복습 예정일이 됐고 이번 주 복습이 {reviews_this_week}회뿐이다(주 2회 목표).",
                "suggested_level": pick["level"], "rows": rows, "queue": q}

    weak = sorted(
        (r for r in rows if r["samples"] > 0),
        key=lambda r: (r["mastery"], -(r["days_since"] or 0)),
    )
    tid = weak[0]["id"] if weak else order[0]
    lvl = 3 if phase == "실전" else 2
    return {"phase": phase, "mode": "new", "type": by_id[tid],
            "reason": f"숙련도가 가장 낮은 유형이 {by_id[tid]['name']}({by_id[tid]['mastery']}점)이다.",
            "suggested_level": lvl, "rows": rows, "queue": q}


# -------------------------------------------------------------------- 출력 커맨드
def cmd_today(args):
    cfg, log = load_types(), load_log()
    rec = recommend(cfg, log)
    print(f"[단계] {rec['phase']}   [오늘] {'복습' if rec['mode']=='review' else '신규'}")
    print(f"[이유] {rec['reason']}")
    if rec["mode"] == "review":
        t = rec["target"]
        names = {x["id"]: x["name"] for x in cfg["types"]}
        print(f"[문제] {t['title']} (lv.{t['level']}, {', '.join(names[i] for i in t['types'])})")
        print(f"       지난 시도 {t['last_date']} / {t['last_outcome']} / 원인: {', '.join(t['errors']) or '-'}")
        print(f"       {t['url']}")
        if t.get("solution_path"):
            print(f"       이전 풀이 {t['solution_path']}  ← 지금 열지 말 것. 피드백 단계에서 비교용으로만 연다")
    else:
        t = rec["type"]
        tgt = next(x for x in cfg["types"] if x["id"] == t["id"])
        print(f"[유형] {t['name']}  (숙련도 {t['mastery']} / 표본 {t['samples']})")
        print(f"[난이도] 프로그래머스 Lv.{rec['suggested_level']}  목표시간 {tgt['target_minutes'][str(rec['suggested_level'])]}분")
        print("[개념 체크리스트]")
        for c in t["concepts"]:
            print(f"  - {c}")
    overdue = [x for x in rec["queue"] if x["days_until"] <= 0]
    if overdue:
        print(f"\n[복습 대기] {len(overdue)}건")
        for x in overdue[:5]:
            print(f"  D{x['days_until']:+d} {x['title']} ({x['last_outcome']})")


def cmd_stats(args):
    cfg, log = load_types(), load_log()
    rows = mastery_table(cfg, log)
    st = streaks(log)
    print(f"총 {len(log)}회 기록 / 단계: {phase_of(rows)}")
    print(f"연속 {st['day']}일   주간 {st['this_week']}/{st['weekly_goal']}   "
          f"주단위 연속 {st['week']}주\n")
    print(f"{'유형':<20}{'숙련도':>6} {'상태':<6}{'표본':>4}{'최근':>6}  평균/목표")
    for r in rows:
        ds = "-" if r["days_since"] is None else f"{r['days_since']}일"
        tm = f"{r['avg_minutes']}/{r['target_minutes']}분" if r["avg_minutes"] else "-"
        bar = "█" * (r["mastery"] // 10)
        print(f"{r['name']:<20}{r['mastery']:>6} {r['status']:<6}{r['samples']:>4}{ds:>6}  {tm:<12}{bar}")
    errs = Counter(e for r in log for e in r.get("errors", []))
    if errs:
        print("\n오답 원인 분포")
        for k, v in errs.most_common():
            print(f"  {k:<14}{v}회")


def cmd_export(args):
    cfg, log = load_types(), load_log()
    ref = today()
    rec = recommend(cfg, log, ref)
    rows = rec["rows"]
    q = rec["queue"]

    heat = Counter()
    best = {}
    for r in log:
        heat[r["date"]] += 1
        prev = best.get(r["date"])
        if prev is None or OUTCOME_SCORE[r["outcome"]] > OUTCOME_SCORE[prev]:
            best[r["date"]] = r["outcome"]

    rust = sorted(
        [r for r in rows if r["samples"] > 0 and (r["days_since"] or 0) >= 14],
        key=lambda r: -(r["days_since"] or 0),
    )[:3]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": rec["phase"],
        "weekly_goal": WEEKLY_GOAL,
        "totals": {
            "records": len(log),
            "problems": len({r["key"] for r in log}),
            "days": len({r["date"] for r in log}),
            "solved_in_time": sum(1 for r in log if r["outcome"] == "solved_in_time"),
            "types_touched": sum(1 for r in rows if r["samples"] > 0),
            "types_total": len(rows),
            "avg_mastery": round(sum(r["mastery"] for r in rows) / len(rows)) if rows else 0,
        },
        "streak": streaks(log, ref),
        "types": [{k: v for k, v in r.items() if k != "concepts"} for r in rows],
        "concepts": {r["id"]: r["concepts"] for r in rows},
        "rust_alerts": [{"name": r["name"], "days_since": r["days_since"],
                         "mastery": r["mastery"], "base": r["base"]} for r in rust],
        "heatmap": [{"date": k, "count": v, "outcome": best[k]} for k, v in sorted(heat.items())],
        "errors": [{"cause": c["id"], "desc": c["desc"],
                    "count": sum(1 for r in log if c["id"] in r.get("errors", []))}
                   for c in cfg["error_causes"]],
        "review_queue": q[:20],
        "time_trend": [{"date": r["date"], "minutes": r["minutes"],
                        "target": r["target_minutes"], "outcome": r["outcome"],
                        "title": r["title"], "types": r["types"]}
                       for r in log[-30:]],
        "recent": [{"date": r["date"], "title": r["title"], "level": r["level"],
                    "types": r["types"], "minutes": r["minutes"],
                    "target": r["target_minutes"], "outcome": r["outcome"],
                    "errors": r.get("errors", []), "mode": r["mode"],
                    "url": r.get("url", ""), "path": r.get("solution_path", "")}
                   for r in reversed(log[-15:])],
        "recommendation": {
            "mode": rec["mode"],
            "reason": rec["reason"],
            "suggested_level": rec["suggested_level"],
            "type": rec.get("type", {}).get("name") if rec["mode"] == "new" else None,
            "type_id": rec.get("type", {}).get("id") if rec["mode"] == "new" else None,
            "target": rec.get("target") if rec["mode"] == "review" else None,
        },
        "type_names": {t["id"]: t["name"] for t in cfg["types"]},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"{OUT} 생성 ({len(log)}개 기록 기준)")


def main():
    p = argparse.ArgumentParser(description="daily-algo 학습 엔진")
    sub = p.add_subparsers(dest="cmd", required=True)

    lg = sub.add_parser("log", help="풀이 1건 기록")
    lg.add_argument("--platform", required=True)
    lg.add_argument("--id", required=True)
    lg.add_argument("--title", required=True)
    lg.add_argument("--level", type=int, required=True)
    lg.add_argument("--types", required=True, help="t04 또는 t04,t06")
    lg.add_argument("--minutes", type=int, required=True)
    lg.add_argument("--outcome", required=True,
                    help="solved_in_time|solved_over_time|solved_with_hint|failed")
    lg.add_argument("--attempts", type=int, default=1)
    lg.add_argument("--errors", default="")
    lg.add_argument("--note", default="")
    lg.add_argument("--path", default="")
    lg.add_argument("--url", default="")
    lg.add_argument("--target", type=int, default=0,
                    help="미지정 시 유형×난이도 기본 목표시간이 들어간다")
    lg.add_argument("--mode", default="new", choices=["new", "review"])
    lg.add_argument("--date", default="", help="YYYY-MM-DD, 미지정 시 오늘")
    lg.set_defaults(func=cmd_log)

    sub.add_parser("today", help="오늘 추천").set_defaults(func=cmd_today)
    sub.add_parser("stats", help="요약 출력").set_defaults(func=cmd_stats)
    sub.add_parser("export", help="대시보드 데이터 생성").set_defaults(func=cmd_export)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
