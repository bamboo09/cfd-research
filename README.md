# cfd-research · CFD 科研工作流

面向流体力学研究人员的 Agent Skill。给它一个算例、一张目标论文图或两组计算结果，可以核查生效配置、只改指定工况、整理复现条件，或按统一定义重算指标。每项判断附上对应的文件与字段、论文位置或原始数据列。

## 安装与调用

在本仓库根目录运行以下命令，将完整 Skill 安装到本机。随包脚本使用 Python 3.9+ 标准库。读原始场或运行仿真时，使用算例对应版本的求解器及读写工具。

```sh
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$skills_dir"
if [ ! -e "$skills_dir/cfd-research" ] && [ ! -L "$skills_dir/cfd-research" ]; then
  ln -s "$PWD/skills/cfd-research" "$skills_dir/cfd-research"
else
  echo "安装位置已存在：$skills_dir/cfd-research"
fi
```

保留仓库目录即可通过链接使用后续更新。也可把整个 [cfd-research 目录](skills/cfd-research)复制到技能目录。在新会话中输入 `$cfd-research` 和任务，例如：

| 任务 | 请求示例 |
|---|---|
| 配置审查 | 审查这个算例是否实现了 Re=100 的二维周期圆柱绕流，列出生效文件、冲突和缺失证据。 |
| 受控修改 | 只把入口速度从 0.02 改为 0.03 m/s，展示补丁，并估算 Re 和入口 Co 尺度的变化。 |
| 论文复现 | 按图 3(b) 建复现方案，为各项条件标出页码或附件位置，说明指标定义与未公开条件。 |
| 后处理比较 | 在同一时间窗内计算两个工况的平均阻力系数，记录参考速度、面积、采样权重和差值。 |

## 验证与依据

从仓库根目录可离线回放两个示例。第一个逐项改变统计窗口、时间权重或归一化方式；第二个用 DFG 作者数据的一个周期重算力系数与 Strouhal 数。

```sh
python3 evaluations/paired/operators.py
python3 evaluations/dfg/replay.py
```

现有两道配对测试各组各运行一次。教学通道题两组均为 12/12；SU2 入口剖面题中，通用 Agent 为 5/6，加载 Skill 后为 6/6，差异来自对缺失重启输入的定位。完整判据、输入、输出及数据来源见[评测报告](evaluations/结果.md)。[Skill 入口](skills/cfd-research/SKILL.md) · [公开方案与文献调研](research/调研.md)
