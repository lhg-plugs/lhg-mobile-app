#!/usr/bin/env python3
"""lhg-mobile-app 确定性规划审计：26 条规则，零第三方依赖。

扫描目标目录下的 Markdown 计划文件（PLAN.md / 上架资料），检查
MVP 范围一致性、上架资料完整度、隐私合规要点与违规承诺。

用法：
    python3 mobile_audit.py --target <目录> [--format json|text] [--fail-on blocker|warning|nit]

退出码：2=有 blocker，1=仅有 warning，0=干净（仅 nit 或无问题）。
规则文案均为本项目原创。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-mobile-app/mobile-audit"

SKIP_DIRS = {".git", "node_modules", "__pycache__", "dist", "build"}
SCAN_EXTS = {".md", ".markdown", ".txt"}


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def collect_files(target):
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in sorted(files):
            if os.path.splitext(fn)[1].lower() in SCAN_EXTS:
                out.append(os.path.join(root, fn))
    return out


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().split("\n")


def first_line_of(files, pattern, flags=0):
    rx = re.compile(pattern, flags)
    for path in files:
        for i, ln in enumerate(read_lines(path), 1):
            if rx.search(ln):
                return os.path.basename(path), i, ln.strip()[:80]
    return None


def make_findings(files, texts):
    """texts: {path: full_text}；返回 findings 列表。"""
    text = "\n".join(texts.values())
    first = os.path.basename(files[0]) if files else "-"
    F = []

    def miss(rule_id, severity, category, title, detail):
        F.append(Finding(rule_id, severity, category, title, first, 1, "", detail))

    def hit(rule_id, severity, category, title, detail, pattern, flags=0):
        loc = first_line_of(files, pattern, flags)
        fn, ln, snip = loc if loc else (first, 1, "")
        F.append(Finding(rule_id, severity, category, title, fn, ln, snip, detail))

    has = lambda p, fl=0: re.search(p, text, fl) is not None

    # ---- MVP / 范围 ----
    if not has(r"MVP\s*目标|最小可行"):
        miss("MA-SCP-001", "blocker", "范围", "缺少 MVP 目标章节",
             "计划中找不到「MVP 目标」或「最小可行」章节：先定义成功标准，再列功能。")
    n_feat = len(re.findall(r"(?m)^-\s*功能", text))
    if n_feat > 8:
        hit("MA-SCP-002", "warning", "范围", "功能清单超过 8 条（%d 条），范围蔓延风险" % n_feat,
            "MVP 的 P0 功能建议≤8 条：超出的请降级为 P1 或移入二期。", r"^-\s*功能")
    if has(r"MVP\s*目标|最小可行") and not has(r"\d+\s*[%％]|转化率|留存|日活|DAU|MAU|≥"):
        miss("MA-SCP-003", "warning", "范围", "MVP 目标缺少可衡量指标",
             "MVP 目标应含 1-3 个可衡量指标（如注册转化率≥20%），否则无法判定做完没做完。")
    if not (has(r"v\d+\.\d+") and has(r"20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}")):
        miss("MA-SCP-004", "warning", "范围", "计划缺少版本与日期",
             "补上版本号（如 v0.1）与日期，便于后续追踪计划变更。")
    if not has(r"不做|范围外|二期|砍掉"):
        miss("MA-SCP-005", "warning", "范围", "缺少「不做清单」/二期规划",
             "明确写出这次不做什么（移到二期），是防范围蔓延最有效的一招。")
    if n_feat > 0 and not has(r"P0|P1|优先级|必须做"):
        miss("MA-SCP-006", "warning", "范围", "功能清单缺少优先级标记",
             "每条功能标 P0（必须）/P1（可延后），否则评审时无法取舍。")

    # ---- 承诺红线 ----
    if has(r"一键上架"):
        hit("MA-PRM-001", "blocker", "承诺", "含有「一键上架」承诺",
            "本插件不承诺一键上架：审核结果取决于官方政策与资料质量，删除该表述。", r"一键上架")
    if has(r"保证过审|一定过审|百分百过审|包过"):
        hit("MA-PRM-002", "warning", "承诺", "绝对化过审表述",
            "「保证过审/包过」类表述不诚实：改为「按 checklist 备齐资料，降低被拒概率」。", r"保证过审|一定过审|百分百过审|包过")
    if has(r"保证.{0,6}(下载|日活|排名)"):
        hit("MA-PRM-003", "blocker", "承诺", "承诺具体下载量/排名指标",
            "「保证下载/日活/排名」属于编造预期：改为诚实表述或删除。", r"保证.{0,6}(下载|日活|排名)")

    # ---- 跨端方案 ----
    if not has(r"跨端|原生开发|Capacitor|Flutter|React Native"):
        miss("MA-TEC-001", "warning", "技术", "缺少跨端方案章节",
             "补上跨端方案选型：原生 / 混合（Capacitor 等）/ 跨端框架思路对比。")
    elif not has(r"对比|优劣|选型理由|为什么选"):
        miss("MA-TEC-002", "warning", "技术", "方案选型缺少对比与理由",
             "只写了方案名、没写对比维度与选型理由：按成本/性能/维护/发布时间/团队技能五维补对比表。")
    if not has(r"热更新|推送|OTA|消息推送"):
        miss("MA-TEC-003", "warning", "技术", "缺少热更新/消息推送方案",
             "补上热更新与消息推送方案（影响发版节奏与用户触达）。")

    # ---- 上架资料 ----
    if not has(r"截图|screenshot", re.I):
        miss("MA-STO-001", "blocker", "上架", "上架资料缺少截图项",
             "应用商店要求多尺寸截图：补上截图规格清单与每张图的卖点分配。")
    if "隐私政策" not in text:
        miss("MA-STO-002", "blocker", "上架", "上架资料缺少隐私政策",
             "隐私政策是上架必备资料：补上章节或可访问的政策链接。")
    if not has(r"应用描述|关键词|ASO"):
        miss("MA-STO-003", "warning", "上架", "缺少应用描述/关键词（ASO）",
             "补上商店文案：应用名、副标题、描述、关键词、分类与年龄分级。")
    if not has(r"审核|被拒|驳回|避坑"):
        miss("MA-STO-004", "warning", "上架", "缺少审核避坑/被拒预案",
             "列出常见被拒原因对照表（权限说明、内购合规、测试账号等），逐项自查。")
    if not has(r"上架清单|上架检查|上架 checklist", re.I):
        miss("MA-STO-005", "blocker", "上架", "缺少上架 checklist 章节",
             "补上「上架 checklist」章节：商店资料/截图/隐私政策/审核避坑四项逐项打勾。")
    if not has(r"内购|付费|IAP|订阅|价格"):
        miss("MA-STO-006", "warning", "上架", "缺少内购/付费说明",
             "如有内购或订阅：说明价格档位与合规要点；无内购也请明确写「无内购」。")

    # ---- 隐私合规 ----
    if not has(r"##\s*隐私|隐私政策"):
        miss("MA-PRV-001", "blocker", "隐私", "缺少隐私政策章节",
             "补上隐私政策章节（或模板）：数据收集、第三方 SDK、联系方式、删除/注销四项为必要条款。")
    elif not has(r"收集|采集"):
        miss("MA-PRV-002", "warning", "隐私", "隐私政策缺少数据收集说明",
             "写明收集哪些数据、为何收集、保留多久。")
    if not has(r"第三方|SDK"):
        miss("MA-PRV-003", "warning", "隐私", "缺少第三方 SDK 声明",
             "列出集成的第三方 SDK 及其数据用途（推送、统计、崩溃上报等）。")
    if not has(r"联系|邮箱|privacy@", re.I):
        miss("MA-PRV-004", "warning", "隐私", "缺少隐私问题联系方式",
             "给出隐私问题联系人/邮箱，用户行使权利时找得到人。")
    if not has(r"删除|注销|撤回"):
        miss("MA-PRV-005", "warning", "隐私", "缺少数据删除/注销说明",
             "说明用户如何删除账号、注销数据、撤回同意。")

    # ---- 工程配套 ----
    if not has(r"登录|鉴权|OAuth|手机号"):
        miss("MA-SEC-001", "warning", "工程", "缺少登录/鉴权方案",
             "补上登录方式（手机号/第三方登录）与鉴权思路。")
    if not has(r"备份|离线|缓存"):
        miss("MA-DAT-001", "warning", "工程", "缺少数据备份/离线方案",
             "补上本地缓存与云端备份策略（用户换机、断网场景）。")
    if not has(r"测试|TestFlight|内测|灰度"):
        miss("MA-TST-001", "warning", "工程", "缺少测试计划",
             "补上测试计划：内测（TestFlight 等）、灰度发布节奏。")

    return F


# ---- 规则注册表（对外口径：26 条） ----
RULES = [
    ("MA-SCP-001", "blocker", "范围"), ("MA-SCP-002", "warning", "范围"),
    ("MA-SCP-003", "warning", "范围"), ("MA-SCP-004", "warning", "范围"),
    ("MA-SCP-005", "warning", "范围"), ("MA-SCP-006", "warning", "范围"),
    ("MA-PRM-001", "blocker", "承诺"), ("MA-PRM-002", "warning", "承诺"),
    ("MA-PRM-003", "blocker", "承诺"),
    ("MA-TEC-001", "warning", "技术"), ("MA-TEC-002", "warning", "技术"),
    ("MA-TEC-003", "warning", "技术"),
    ("MA-STO-001", "blocker", "上架"), ("MA-STO-002", "blocker", "上架"),
    ("MA-STO-003", "warning", "上架"), ("MA-STO-004", "warning", "上架"),
    ("MA-STO-005", "blocker", "上架"), ("MA-STO-006", "warning", "上架"),
    ("MA-PRV-001", "blocker", "隐私"), ("MA-PRV-002", "warning", "隐私"),
    ("MA-PRV-003", "warning", "隐私"), ("MA-PRV-004", "warning", "隐私"),
    ("MA-PRV-005", "warning", "隐私"),
    ("MA-SEC-001", "warning", "工程"), ("MA-DAT-001", "warning", "工程"),
    ("MA-TST-001", "warning", "工程"),
]

SEV_ORDER = {"blocker": 0, "warning": 1, "nit": 2}


def main():
    ap = argparse.ArgumentParser(description="lhg-mobile-app 规划审计")
    ap.add_argument("--target", required=True, help="待扫描目录")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"], default="blocker")
    args = ap.parse_args()

    files = collect_files(args.target)
    texts = {p: "\n".join(read_lines(p)) for p in files}
    findings = make_findings(files, texts)
    findings.sort(key=lambda f: (SEV_ORDER[f.severity], f.rule_id))
    summary = {
        "tool": TOOL, "version": VERSION, "target": args.target,
        "files_scanned": len(files), "rules_run": len(RULES),
        "blocker": sum(1 for f in findings if f.severity == "blocker"),
        "warning": sum(1 for f in findings if f.severity == "warning"),
        "nit": sum(1 for f in findings if f.severity == "nit"),
    }

    if args.format == "json":
        print(json.dumps({"summary": summary,
                          "findings": [f.to_dict() for f in findings]},
                         ensure_ascii=False, indent=2))
    else:
        print("lhg-mobile-app 规划审计  target=%s  文件=%d  规则=%d"
              % (args.target, summary["files_scanned"], summary["rules_run"]))
        print("blocker=%d warning=%d nit=%d"
              % (summary["blocker"], summary["warning"], summary["nit"]))
        for f in findings:
            print("[%s][%s] %s:%d %s" % (f.severity, f.rule_id, f.file, f.line, f.title))
            if f.detail:
                print("    %s" % f.detail)

    if summary["blocker"] > 0:
        return 2
    if args.fail_on in ("warning", "nit") and summary["warning"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
