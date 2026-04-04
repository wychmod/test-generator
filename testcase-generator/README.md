# TestCase Generator Skill

AI 测试用例生成器，五阶段流程，命令简化为 `/testcase`。

## 快速开始

```bash
# 安装到全局
cp -r testcase-generator ~/.claude/skills/

# 使用
/testcase 用户登录功能测试
/testcase ./requirements.txt
/testcase 请为支付模块生成测试用例
```

## 五阶段流程

```
需求预处理 → 代码分析 → 领域分析 → MBT设计 → 用例生成
```

## 产物清单

每个阶段都有产出物，共 16 个文件 + 1 个质量报告。

## 目录结构

```
testcase-generator/
├── SKILL.md           # Skill 主文件
├── prompts/           # 详细提示词（可选）
├── templates/         # 输出模板（可选）
└── resources/         # 参考资源（可选）
```
