#!/usr/bin/env python3
"""lhg-mobile-app 硬门②：写入 PLAN.md（或 *plan*.md）后检查上架 checklist 完整性。

触发：PostToolUse / Write|Edit。只处理 Markdown 计划文件，其余快速放行。
若计划文件缺少"上架 checklist"章节，给出 additionalContext 提醒（不拦截）。

逃生方式：LHG_MA_HOOKS_OFF=1（本次会话内不再提醒）。
设计原则：内部出错 fail-open；纯提醒，不拦截写入。零第三方依赖。
"""

import json
import os
import re
import sys


def main() -> int:
    if os.environ.get("LHG_MA_HOOKS_OFF") == "1":
        return 0
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # fail-open

    tool_input = payload.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "") or ""
    base = os.path.basename(path).lower()
    if not (base.endswith(".md") and ("plan" in base or "计划" in base)):
        return 0  # 非计划文件：快速放行

    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return 0  # 读不到文件：fail-open

    missing = []
    if not re.search(r"上架清单|上架检查|上架 checklist", text, re.I):
        missing.append("缺少「上架 checklist」章节——商店资料/截图/隐私政策/审核避坑四项备齐才能提交")
    if "隐私政策" not in text:
        missing.append("未提及「隐私政策」——上架必备资料，见 skill lhg-ma-privacy")
    if "一键上架" in text:
        missing.append("发现「一键上架」表述——本插件不承诺一键上架，请删除该承诺")

    if not missing:
        return 0
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "lhg-mobile-app 提醒（计划文件 %s）：\n- %s\n"
                "跑 /lhg-mobile-app:mobile-app-check 可得完整分级报告。"
                % (base, "\n- ".join(missing))
            ),
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
