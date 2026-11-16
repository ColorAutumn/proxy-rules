#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 v4-cn-direct.json 是否符合 v2rayN 规则集格式。

v2rayN 的规则是"从上到下、命中即止"，字段写错不会报错，
只会静默失效（比如 Domain 少写 domain: 前缀就永远匹配不上）。
所以这里把容易踩的坑全部前置检查。
"""

import json
import sys
from pathlib import Path

FILE = Path(__file__).resolve().parent.parent / "v4-cn-direct.json"

VALID_OUTBOUND = {"direct", "proxy", "block"}
VALID_PREFIX = ("domain:", "full:", "geosite:", "regexp:", "keyword:", "ext:")


def main() -> int:
    try:
        rules = json.loads(FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"✗ JSON 解析失败：{e}")
        return 1

    if not isinstance(rules, list):
        print("✗ 顶层必须是数组")
        return 1
    if not rules:
        print("✗ 规则为空")
        return 1

    errors = []
    ids = set()

    for i, r in enumerate(rules):
        tag = f"第 {i} 条（{r.get('Remarks', '无备注')}）"

        if not isinstance(r, dict):
            errors.append(f"{tag}: 不是对象")
            continue

        out = r.get("OutboundTag")
        if out not in VALID_OUTBOUND:
            errors.append(f"{tag}: OutboundTag = {out!r}，只能是 {sorted(VALID_OUTBOUND)}")

        rid = r.get("Id")
        if not rid:
            errors.append(f"{tag}: 缺少 Id")
        elif rid in ids:
            errors.append(f"{tag}: Id 重复（{rid}）")
        else:
            ids.add(rid)

        dom = r.get("Domain")
        if dom is not None:
            if not isinstance(dom, list):
                errors.append(f"{tag}: Domain 必须是数组，不能是字符串")
            else:
                for d in dom:
                    if not isinstance(d, str):
                        errors.append(f"{tag}: Domain 元素必须是字符串 -> {d!r}")
                    elif not d.startswith(VALID_PREFIX):
                        errors.append(
                            f"{tag}: {d!r} 缺少类型前缀，应为 domain:/full:/geosite: 等"
                        )

        ip = r.get("Ip")
        if ip is not None:
            if not isinstance(ip, list):
                errors.append(f"{tag}: Ip 必须是数组")

        if not any(k in r for k in ("Domain", "Ip", "Port", "Protocol", "Network", "Process")):
            errors.append(f"{tag}: 没有任何匹配条件，会匹配全部流量")

        if r.get("Port") is not None and not isinstance(r.get("Port"), str):
            errors.append(f"{tag}: Port 必须是字符串（如 \"443\"）")

    # 兜底检查：整份规则里必须有中国域名直连，否则国内站点会全部走代理
    if not any(
        any(d == "geosite:cn" for d in (r.get("Domain") or []))
        for r in rules
        if isinstance(r, dict)
    ):
        errors.append("缺少 geosite:cn 兜底规则，国内站点会全部走代理")

    # 顺序检查：自定义 direct 必须在 geosite:cn 之前
    def idx_of(pred):
        for i, r in enumerate(rules):
            if isinstance(r, dict) and pred(r):
                return i
        return -1

    mc = idx_of(lambda r: "domain:mojang.com" in (r.get("Domain") or []))
    cn = idx_of(lambda r: "geosite:cn" in (r.get("Domain") or []))
    if mc > cn > -1:
        errors.append(f"MC 直连在第 {mc} 条，却在 geosite:cn（第 {cn} 条）之后，可能不生效")

    if errors:
        print(f"✗ 校验失败，共 {len(errors)} 个问题：\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    total_domains = sum(len(r.get("Domain") or []) + len(r.get("Ip") or []) for r in rules)
    print(f"✓ 校验通过：{len(rules)} 条规则，{total_domains} 个匹配项")
    for i, r in enumerate(rules):
        print(f"  {i:>2}. {r['OutboundTag']:<6} {r.get('Remarks', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
