# Vibe Coding产品宣发助手

把已经做出来的 Vibe Coding 产品，整理成可以直接继续制作的自媒体图文、短视频、内容池和平台原生版本。

这个 Skill 默认接受开发者对产品意义、目标用户和继续投入的判断。它只负责产品如何在自媒体上表达，不做需求验证、PMF 评估、商业价值判断或项目劝退。

## 能完成什么

- 判断国内、海外或双市场内容方向。
- 区分 ToC、ToB 或 Hybrid 叙事。
- 推荐一个主平台、两个备选平台，并制作平台原生版本。
- 提炼三到五个适合传播的产品亮点。
- 生成100个与当前产品绑定的内容角度。
- 生成六套图文案例，国内封面默认使用2:3竖版。
- 生成八套包含口播、分镜、屏幕文字、标题、配文和Tags的完整短视频案例。
- 生成响应式HTML宣发报告。
- 生成项目专属Agent提示词，方便后续继续扩写内容。

## 不包含什么

- 产品是否有意义、值不值得做、会不会有人用的判断。
- 发布时间、发布频率、30天日历或账号运营计划。
- 转化漏斗、私域、销售流程、投放和自动发布。
- KPI、实验、复盘和停止条件。
- 未经证实的功能、案例、评价、数据或产品效果。

## SkillHub安装

Skill上架后可使用：

```bash
skillhub install vibe-product-gtm --dir ~/.codex/skills
```

不同Agent的Skills目录不同，请按实际环境修改 `--dir`。

## 从GitHub安装到Codex

```bash
git clone https://github.com/CybHammer/vibe-product-gtm.git ~/.codex/skills/vibe-product-gtm
```

重启或重新打开Codex任务后即可调用：

```text
使用 $vibe-product-gtm 读取我已经完成的产品，只做国内ToC的自媒体宣发，生成完整HTML报告。
```

也可以只请求一个子任务：

```text
使用 $vibe-product-gtm 为这个产品生成一套小红书图文案例。
使用 $vibe-product-gtm 写八条面向家长的完整短视频脚本。
使用 $vibe-product-gtm 把现有中文内容改成海外平台原生版本。
```

## 仓库结构

```text
SKILL.md
agents/openai.yaml
references/
scripts/validate_promotion_package.py
```

`SKILL.md` 是SkillHub和Agent读取的入口，详细内容规则按任务路由到 `references/`，结构化推广包可以使用校验脚本检查。

## 版本

当前SkillHub发布版本：`1.0.0`。
