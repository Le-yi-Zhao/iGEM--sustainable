# 光甘草定护肤品原料评价

本轮按用户确认的护肤品用途选定终点，而非按预测分数取舍。产品细节尚未提供；暂以非喷雾、留敷型面部护肤品组织分析，不以此假设计算暴露剂量。15 号光甘草定为目标原料，其余五分子是通路及潜在杂质参照，不代表已在产品中测出的杂质。

## 当前任务

- ADMET-AI：保留 AMES、Skin_Reaction、Carcinogens_Lagunin 三项主要危害，Solubility_AqSolDB、Lipophilicity_AstraZeneca 两项配方性质，以及十二项 Tox21 机理信号，共 17 项。其余 24 项退出默认评价。逐项理由见 `results/tables/skincare/admet_task_selection.csv`。
- 官方多任务网络共用前向计算；只提取所选输出，不声称拆除了其他输出头。新推理与原 41 任务文件分别保存。
- Chemprop：三项主要危害的五成员积分梯度，六分子共 90 个数值完整性检查。原子及分配到原子的键贡献解释相对于零特征图的输出差，不是因果毒性。
- MapLight：仅 AMES，五随机种子，固定 TDC 训练/测试划分。DILI/hERG 不再默认训练；GNN 扩展未运行。
- admetSAR：利用已验证的官方批次提取皮肤/眼刺激与腐蚀、致敏、光诱导毒性、光刺激、光过敏及遗传/致癌性。重复暴露、生殖及受体信号保留供暴露驱动的后续分析。各原生分数和试验定义保持独立。
- ADMETlab、VEGA、ProTox：保留相关已有皮肤、眼部、遗传与致癌性结果。ProTox 原生类别置信度不转为阳性概率；口服 LD50 和肝毒性留在历史文件。
- VEGA/EPI/ECOSAR 环境归趋与生态毒性继续用于生产和使用后环境筛查，保留全部适用域与源警告。

## 运行与证据

全部代码和新计算在 Matvision `/root/autodl-tmp/IGEM/GALATEA-sustainable` 执行。默认重建不训练模型或提交网页任务；强制推理与训练分别使用：

```bash
python -m analysis.adapters.admet_ai_local --force
python -m analysis.models.chemprop_attribution
python -m analysis.models.maplight_local
python analysis/run_all.py
python -m unittest discover -s tests -v
```

新原始记录位于 `data/raw/skincare/`，处理表位于 `data/processed/skincare/` 与 `results/tables/skincare/`。先前广泛药物开发筛查结果原样保留，明确作为历史记录。重新选择网页结果不等于网页服务重新计算。

## 解释边界与缺口

0.5 不是护肤品安全阈值，本轮不输出低风险结论或跨平台共识投票。已有 DrugBank 药物预测分布不作为无毒对照；独立阳性/阴性对照与护肤品领域校准尚未完成。

没有把 Caco-2、PAMPA 或 logP 当作经皮吸收率。经皮吸收、配方浓度、使用量和频次缺失，因此不计算 SED 或 MoS。外用不能直接豁免全身、重复暴露、生殖、遗传或内分泌相关风险。

皮肤刺激和致敏、光毒性和光稳定性、原料预测和成品耐受性分别处理。光学谱、光稳定性、最终配方评价、微生物/防腐、杂质与残留溶剂、包装相容性等仍缺实验数据。本模块不推导美白功效，不推导 LLPS 工艺收益。

## 范围依据

SCCS/1647/22，第 12 版及 2023-12-21 勘误：3-2 原料规格、3-3 暴露评估、3-4.5 皮肤腐蚀/刺激、3-4.6 眼部、3-4.7 致敏、3-4.8 重复给药、3-4.9 生殖、3-4.10 遗传毒性、3-4.11 致癌性、3-4.12 光诱导毒性。用于科学范围选择，不代表满足任何特定市场的注册或法规要求。

- https://health.ec.europa.eu/publications/sccs-notes-guidance-testing-cosmetic-ingredients-and-their-safety-evaluation-12th-revision_en
- https://lmmd.ecust.edu.cn/admetsar3/
- https://github.com/swansonk14/admet_ai
- https://github.com/maplightrx/MapLight-TDC
