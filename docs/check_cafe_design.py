"""Standalone design check for scenarios/cafe.json (no engine needed).
Run: python check_cafe_design.py [path/to/cafe.json]"""
import json, sys, itertools

RULE_PENALTY = 5

def run(level, chosen, pkg_i):
    chosen = set(chosen)
    zones = {z["id"]: z for z in level["map_zones"]}
    atks = level["attack_packages"][pkg_i]
    custs = level["customer_questions"]
    lost = set(); events = []
    a = list(atks); c = list(custs)
    while a or c:
        if a:
            x = a.pop(0)
            if not (chosen & set(x["blocked_by"])):
                lost.add(x["target_zone"])
        if c:
            y = c.pop(0)
            if chosen & set(y["broken_by"]):
                lost.add(y["zone"])
    att = {x["target_zone"] for x in atks}
    cz = {y["zone"] for y in custs}
    sec_t = sum(zones[i]["points"] for i in att)
    sec_e = sum(zones[i]["points"] for i in att if i not in lost)
    hel_t = sum(zones[i]["points"] for i in cz)
    hel_e = sum(zones[i]["points"] for i in cz if i not in lost)
    core = any(zones[i]["ring"] == "core" for i in lost)
    return dict(sec_e=sec_e, sec_t=sec_t, hel_e=hel_e, hel_t=hel_t, core=core, used=len(chosen))

def grade(r, min_rules):
    if r["core"]: return "lose", 0, 0
    score = 100 * (r["sec_e"] + r["hel_e"]) / (r["sec_t"] + r["hel_t"]) - RULE_PENALTY * max(0, r["used"] - min_rules)
    score = max(0, score)
    if r["sec_e"] == r["sec_t"] and r["hel_e"] == r["hel_t"] and r["used"] <= min_rules: return "perfect", 3, score
    for stars, th in ((3, 90), (2, 75), (1, 60)):
        if score >= th: return "stars", stars, score
    return "fail", 0, score

def check_level(level):
    errs = []
    zid = {z["id"] for z in level["map_zones"]}
    rid = {r["id"] for r in level["rules"]}
    rings = {"outer", "inner", "sensitive", "core"}
    for z in level["map_zones"]:
        if z["ring"] not in rings: errs.append("bad ring " + z["id"])
    outer = sum(z["points"] for z in level["map_zones"] if z["ring"] == "outer")
    sec = sum(z["points"] for z in level["map_zones"] if z["ring"] != "outer")
    if outer < sec: errs.append(f"outer {outer} < secrets {sec}")
    for p in level["attack_packages"]:
        for x in p:
            if x["target_zone"] not in zid: errs.append("attack zone " + x["target_zone"])
            for b in x["blocked_by"]:
                if b not in rid: errs.append("blocked_by " + b)
    for y in level["customer_questions"]:
        if y["zone"] not in zid: errs.append("customer zone " + y["zone"])
        for b in y["broken_by"]:
            if b not in rid: errs.append("broken_by " + b)
    ids = [r["id"] for r in level["rules"]]
    n = len(ids)
    if not 4 <= n <= 8: errs.append(f"{n} rules")
    traps = [r["id"] for r in level["rules"] if r.get("kind") == "trap"]
    if len(traps) != 1: errs.append(f"{len(traps)} traps")
    npk = len(level["attack_packages"])
    # universal perfect sets
    perfect = []
    for k in range(n + 1):
        for s in itertools.combinations(ids, k):
            if all(grade(run(level, s, p), level["min_rules"])[0] == "perfect" or
                   (grade(run(level, s, p), 99)[0] == "perfect") for p in range(npk)):
                perfect.append(s)
    # exact minimal universal set (perfect ignoring size cap)
    uni = [s for s in perfect]
    if not uni: errs.append("no universal perfect set")
    else:
        m = min(len(s) for s in uni)
        if m != level["min_rules"]: errs.append(f"min_rules {level['min_rules']} but smallest perfect set is {m}")
    for t in traps:
        for p in range(npk):
            g = grade(run(level, (t,), p), level["min_rules"])[0]
            if g not in ("fail", "lose"): errs.append(f"trap {t} alone is {g} in package {p}")
    allg = [grade(run(level, ids, p), level["min_rules"]) for p in range(npk)]
    cos = [r["id"] for r in level["rules"] if r.get("kind") == "cosmetic"]
    # each package has some perfect set within min_rules? (informational)
    info = []
    for p in range(npk):
        best = None
        for k in range(n + 1):
            for s in itertools.combinations(ids, k):
                if grade(run(level, s, p), 99)[0] == "perfect": best = s; break
            if best is not None: break
        info.append(best)
    smallest = sorted([s for s in uni if len(s) == (min(len(s) for s in uni) if uni else 0)])
    print(f"{level['id']}: min_rules={level['min_rules']} smallest universal perfect sets={smallest[:3]} per-package minimal={info}")
    print(f"   all rules picked -> {[(g[0], g[1], round(g[2])) for g in allg]}")
    for r in level["rules"]:
        row = [(grade(run(level, (r['id'],), p), level['min_rules'])[0]) for p in range(npk)]
        print(f"   alone {r['id']:<26} {row}")
    return errs

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "cafe.json"
    data = json.load(open(path, encoding="utf-8"))
    bad = 0
    for lv in data["levels"]:
        e = check_level(lv)
        for x in e: print("   ERROR", x)
        bad += len(e)
    for s in data.get("sections", []):
        zid = {z["id"] for z in s["map_zones"]}
        for k, v in s["secrets_by_zone"].items():
            if k not in zid: print("   ERROR section secret zone", k); bad += 1
        for p in s["attack_packages"]:
            for x in p:
                if x["target_zone"] not in zid: print("   ERROR section attack zone", x); bad += 1
        for q in s["customer_questions"]:
            if q["zone"] not in zid: print("   ERROR section customer zone", q); bad += 1
        outer = sum(z["points"] for z in s["map_zones"] if z["ring"] == "outer")
        sec = sum(z["points"] for z in s["map_zones"] if z["ring"] != "outer")
        if outer < sec: print(f"   WARN section {s['id']} outer {outer} < secrets {sec}")
    print("ERRORS:", bad)
    sys.exit(1 if bad else 0)
