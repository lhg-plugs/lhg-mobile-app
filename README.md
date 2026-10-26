<!-- About 简介（推送后填写到仓库 About 栏）：
移动 App 专家：想法→MVP 范围→跨端选型→上架 checklist，规划一次到位 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-mobile-app
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, mobile-app, mvp, app-store -->

# lhg-mobile-app：移动 App 专家

> **一句话介绍**：给 AI 编程助手装上"移动 App 规划一条龙"——一句话想法→MVP 范围界定→跨端方案选型→功能清单→上架 checklist，26 条确定性规则自查，规划一次到位。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-mobile-app
> /plugin install lhg-mobile-app@lhg-plugs
> ```

## 它是什么

`lhg-mobile-app` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **3 个命令**（小白入口）：`mobile-app` 规划一条龙，`mobile-app-check` 范围蔓延+上架完整度自查，`store-kit` 上架资料包生成
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：MVP 范围界定、跨端方案选型、应用商店上架规范、隐私合规基础
- **3 个专家 agent**：MVP 范围审查、跨端选型、上架资料审查
- **2 个硬门 hooks**：commit 前规划审计拦截（有 blocker 不让提交）、写计划文件时缺上架章节提醒（均可一键豁免）
- **26 条确定性规划审计规则**：纯 Python、零第三方依赖，5 秒出结果

**边界**：本插件聚焦"规划 + checklist"，**不承诺一键上架、不代提交、不保证过审**。审核结果取决于官方政策与你的资料质量；隐私政策模板不是法律意见，发布前请法务确认。

## 3 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-mobile-app:mobile-app` | 想法→MVP 范围→跨端选型→功能清单→上架 checklist，一条龙 | `/lhg-mobile-app:mobile-app "3 秒记账 App"` |
| `/lhg-mobile-app:mobile-app-check` | MVP 范围蔓延检测 + 上架资料完整度检查 | `/lhg-mobile-app:mobile-app-check ./PLAN.md` |
| `/lhg-mobile-app:store-kit` | 生成上架资料包：商店文案/截图清单/隐私政策模板/审核避坑 | `/lhg-mobile-app:store-kit "闪记"` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工复核清单（人）：

1. 先跑 `scripts/audit/mobile_audit.py`（26 条规则：范围类/上架类/隐私类/承诺红线），零 LLM 成本；
2. 发现分三级：**blocker**（"一键上架"承诺、缺隐私政策、缺上架 checklist，commit 前 hook 会拦截）、**warning**（修或写豁免理由）、**nit**（顺手修）；
3. 再按各 skill 的人工清单复核（范围蔓延信号、上架资料逐项打勾）。

blocker 清零才算通过；为清零改规则算作弊，不许。

## 目录结构

```
lhg-mobile-app/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 3 个命令：mobile-app / mobile-app-check / store-kit
├── skills/                  # 4 个平台中立 skill（lhg-ma-mvp/cross/store/privacy）
├── agents/                  # 3 个专家 agent（mvp-scoper / tech-chooser / launch-checker）
├── hooks/                   # 2 个硬门（commit 前审计拦截 / 计划文件提醒）+ 豁免说明
├── scripts/audit/           # 26 条确定性规划审计规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 只有一个 App 想法，不知道第一版该做多少时 → 用 `/lhg-mobile-app:mobile-app`
- 功能清单越列越长，怀疑范围蔓延时 → 用 `/lhg-mobile-app:mobile-app-check`
- 在"原生 / 混合 / 跨端框架"之间摇摆不定时 → 选型对比见 `lhg-ma-cross`
- App 快做完了，准备提交应用商店时 → 用 `/lhg-mobile-app:store-kit` 备齐资料
- 写隐私政策、申请敏感权限时 → 看 `lhg-ma-privacy`

**什么时候不用：**

- 你要的是"一键上架""包过审" → 本插件不承诺这个，任何承诺包过审的都是骗子
- 你要的是完整 App 工程代码生成 → 本插件只做规划与 checklist，不写完整工程
- 你只需要单一平台（如只要 iOS 版）→ 跨端选型部分可跳过
- 你的 App 走企业内部分发不走商店审核 → 上架 checklist 部分不适用

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-mobile-app](https://github.com/lhg-plugs/lhg-mobile-app) | 移动 App 专家：想法→MVP 范围→跨端选型→上架 checklist | `/plugin install lhg-mobile-app@lhg-plugs` |
| *（后续插件在此追加，保持表格格式一致）* | | |

## 自检与反馈

- 每次用完任一 skill，按其「自检与反馈」节做轻量自检。
- 标准冒烟用例：`python3 smoke_test.py`（仓库根目录），全绿才算过。
- 反馈渠道：以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-mobile-app/issues，正文写清「输入 → 错误输出 → 期望输出」。规则误报/漏报请附最小复现代码。

## 出品

**出品：刘洪光**（安徽合肥），归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
