# Matvision 实际运行记录与解释边界

2026-09-28 至 29 日在 Matvision 的 `/root/autodl-tmp/IGEM/GALATEA-sustainable` 完成下列选定计算。输入始终是通过结构核查的六个化合物 9、10、11、13、14、15。网页服务请求通过官方界面提交公开结构，结果回存到虚拟机。所有结果属于 **PREDICTED**，不能代替实验安全性或生产可持续性证据。

| 计算 | 实际覆盖 | 可核查产物 |
|---|---|---|
| ADMET-AI / Chemprop | 10 个官方检查点；6 × 41 个任务；每个任务 5 个成员 | 246 个结果、1,230 个成员预测，模型 SHA-256 与原始日志 |
| Chemprop 解释 | 6 个结构 × 4 个端点 × 5 个成员 | 原子和键特征积分梯度、120 个数值完整性检查 |
| VEGA 1.2.6 | 10 个选定模型 × 6 个结构 | 60 条预测及原生 ADI、可靠性、结构警告 |
| EPA EPI Web Suite 1.1.0 | 6 个结构批量请求 | 原始宽表、54 个选定性质值 |
| ECOSAR | 同一批次，保留所有返回的类别 | 118 条生态毒性结果；24 条 logKow 超限、35 条源警告，二者可能重合 |
| ProTox 3.0 | 6 个结构，4 个额外端点及默认口服毒性 | 24 条端点结果、6 条口服毒性摘要、逐结构原始 CSV 和结果链接 |
| admetSAR 3.0 | 官方批量任务 175746，6 个结构 | 原始 TXT、121 列原生导出与结构匹配表；适用域未导出 |
| MapLight（无 GNN） | DILI、hERG、AMES；每个任务 5 个种子 | 15 次模型训练、90 个项目成员预测、15 组留出集指标 |

## 推理、训练与缓存

ADMET-AI 使用官方打包检查点重新推理，不以读取旧 CSV 作为执行证明。原缓存保存在 `data/raw/admet_ai/archive/`。当前环境采用 PyTorch 2.8.0+cpu；没有替换系统环境中的 GPU PyTorch。实际版本见 `results/summaries/matvision_reproduction.json`，模型及输入校验和见 `data/raw/admet_ai/run_metadata.json`。

```bash
# 在仓库目录，使用项目环境
/root/autodl-tmp/IGEM/.venv/bin/python -m analysis.adapters.admet_ai_local --force
/root/autodl-tmp/IGEM/.venv/bin/python -m analysis.models.chemprop_attribution

# MapLight 使用固定公开 TDC 分割；PyTDC 旧版依赖声明包含旧 RDKit，单独安装
/root/autodl-tmp/IGEM/.venv/bin/pip install --no-deps PyTDC==0.4.1
/root/autodl-tmp/IGEM/.venv/bin/python -m analysis.models.maplight_local

# 默认重建读取现有结果，不重新训练，也不提交外部网页请求
/root/autodl-tmp/IGEM/.venv/bin/python analysis/run_all.py
/root/autodl-tmp/IGEM/.venv/bin/python -m unittest discover -s tests -v
```

VEGA 使用官方 Java 包内的模型 API，未重新实现模型。安装官方包后，将其实际路径赋给 `VEGA_JAR`，运行：

```bash
mkdir -p /tmp/galatea-vega-classes
javac -cp "$VEGA_JAR" -d /tmp/galatea-vega-classes analysis/adapters/GalateaVega.java
java -Djava.awt.headless=true -Xmx4g -cp "/tmp/galatea-vega-classes:$VEGA_JAR" GalateaVega data/raw/vega/input.tsv data/raw/vega/reports
```

## 解释方法和限制

Chemprop 采用固定拓扑、零原子/键特征基线的积分梯度。每条有向键的贡献均分到两个端点原子；梯形积分从 128 步逐次增加到最多 1,024 步。120 个检查的最大绝对完整性残差为 0.0047472，均通过 0.005 阈值。原始前向输出与新推理吻合。零特征图是非物理的数学基线，五模型标准差是模型间差异，均不是因果毒性片段、实验置信区间或安全证明。替代基线敏感性尚未验证。

VEGA 保留每个模型自己的 ADI 和可靠性判断；12 条原始分子量字段与 RDKit 相差超过 0.5 g/mol，已标记而未修饰数据。输出结构与输入的连接关系一致，但不保留完整立体化学。EPA 按提交的精确 SMILES 关联，保留 ECOSAR 类别、物种、时间、终点、mg/L 单位、源警告和 logKow 上限。无警告不等于适用域通过。BIOWIN 时间框架分值不换算为天。相关 VEGA/EPI 方法不能作为独立投票。

ProTox API 示例链接仍为 404；官方网页请求成功。服务器是否复用缓存未知，因此不声称远程服务器一定重新训练或重新推理。CSV 中的 Probability 是所报告 Active/Inactive 类别的置信程度，未当作阳性类别概率，也未加入未经定义对齐的共识。

MapLight 官方源代码固定在 `c249378c63232354d17083c83fe94fe728960a27`，MIT 许可和源码保存在 `analysis/vendor/`。采用原官方 ECFP/Avalon/ErG/200 描述符、CatBoost Logloss、random_strength=2、种子 1–5、1,000 次迭代、深度 6；使用 CPU 12 线程。RDKit 未定义描述符由 CatBoost 原生 `nan_mode=Min` 处理；无限值统一作为缺失（本次为零）。没有删除样本或根据测试集拟合填充值。

DILI、hERG、AMES 的训练/测试行数分别为 379/96、523/132、5,821/1,457；按固定 TDC 分割训练，无测试集调参或早停。三个任务的规范连接关系训练/测试交集为零，六个项目结构也不在这些训练/测试集合中。所有种子、测试预测和 ROC-AUC/AP/Brier 指标均保留；这仍不是 GALATEA 独立实验验证。当前依赖版本和原论文环境不同，结果应称为方法复现，不能宣称精确复现排行榜。没有运行 MapLight+GNN 或其余任务。

本次未产生匹配 No-LLPS/LLPS 湿实验、真实资源清单或独立毒理校准数据。CompTox 个体 API 密钥仍未提供。状态文件继续保留这些缺口。

## 来源

- ADMET-AI: https://github.com/swansonk14/admet_ai
- MapLight: https://github.com/maplightrx/MapLight-TDC
- VEGA: https://www.vegahub.eu/download/vega-qsar-download/
- EPA ECOSAR 官方入口说明: https://www.epa.gov/tsca-screening-tools/ecological-structure-activity-relationships-ecosar-predictive-model
- EPI Web Suite: https://episuite.dev/
- ProTox: https://tox.charite.de/protox3/

逐文件校验和见 `results/summaries/fresh_execution_manifest.json`；源报告及置信/适用域字段保留在原始结果目录。

补充：admetSAR 官方六结构批次已完成，输入和输出以规范立体 SMILES 一一匹配。原始输出实际列数以其 metadata 为准。
