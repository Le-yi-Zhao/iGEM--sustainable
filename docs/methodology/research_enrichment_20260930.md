# 本轮功效、生产、资源与模型补充

数据日期：2026-09-30。运行环境：Matvision。原有文献数据库与旧模型结果保留；没有新增项目湿实验。

## 文献数据与图

`python -m analysis.plotting.research_enrichment` 读取论文原始工作簿并输出七张图、六张 CSV 及来源摘要。Fig. 4d/4e 的 198 个位置中，197 个有数据、1 个为空；每项保留工作表、Excel 行列和重复编号。零值按原文保留。仅作描述性重画，不拟合未测量曲线或推算代谢通量。

功效比较来自三篇原始论文的四个同试验配对；2022 年两个终点不是两个独立研究。单位统一为 μmol/L。原摘要的 ± 数值保存在下载表中，但不当作统一类型的误差，不构造不明依据的置信区间。全文与摘要可访问性不同，各项提供具体定位。新增检索为定向补充，不是系统综述。动物分歧和人体复方归因限制均保留。

提取纯度换算为 `粗提物质量 = 100 / 纯度百分数`，对应粗提物中包含的 1 g 光甘草定，不等于纯化后得到 1 g。发酵液体积情景为 `1000 / (浓度 mg/L × 总回收率)`，不等于用水量或完整环境足迹。

## MapLight 图表示扩展

官方来源：https://github.com/maplightrx/MapLight-TDC ，源提交 `c249378c63232354d17083c83fe94fe728960a27`，参考 `maplight_gnn.py`。

分两个环境计算：保留现有 Python 3.12 的 RDKit/CatBoost 基础特征和检查点；独立 Python 3.10 环境使用 torch 2.2.2 CPU、DGL 1.1.3、molfeat 0.10.1 与 DGLLife 提取冻结的 `gin_supervised_masking` 表示。实际所有包版本记录在运行元数据。基础特征经行顺序及校验绑定，随后回到原环境拼接训练 CatBoost，避免更换基础指纹实现造成不公平比较。

molfeat 的默认公共 GCS 列表接口返回 401，未使用受限存储内容；改为 DGLLife 官方公开的同名 `load_pretrained` 检查点，继续使用 molfeat 原有图特征化和均值池化代码。权重校验值记录在元数据，不能声称与无法访问的 molfeat 托管文件逐字节相同。

```sh
# 以下在仓库根目录执行；模型缓存保存在工作盘以外。
PYTHONPATH=. /root/autodl-tmp/IGEM/.venv/bin/python analysis/models/prepare_maplight_gnn.py
/root/IGEM-storage/enrichment/gnn-env/bin/python analysis/models/embed_maplight_gnn.py
/root/autodl-tmp/IGEM/.venv/bin/python -m analysis.models.maplight_gnn_run
```

训练仅使用缓存的 TDC AMES train_val；测试不用于训练、早停、参数选择或校准拟合。模型参数匹配旧配方：5 个种子、1000 次迭代、深度 6、random_strength=2、CatBoost 缺失值策略 Min。GIN 不做终点微调；不是端到端 GNN。原基础模型在逐测试分子上的输出需复现到 1e-10 以内。

同时报告原固定测试集和去除训练连接结构重叠后的子集。配对重采样在后者按化学连接结构分组进行，固定种子 20260930，1000 次，报告 GIN 减去基础模型的差值区间。它只覆盖样本抽样的不确定性，不是全部模型误差。结构邻域使用半径 2、2048 位 Morgan 指纹，不设人为安全阈值。

## 页面复现

OPERA 发布包为 `https://github.com/kmansouri/OPERA/releases/tag/v2.9.5`。运行于 Linux MATLAB Runtime R2023b Update 11，命令为：

```sh
python analysis/models/prepare_opera.py
cd /root/IGEM-storage/enrichment/opera/installed/application
MCR_CACHE_ROOT=/root/IGEM-storage/enrichment/opera/mcr-cache ./run_OPERA.sh \
  /root/IGEM-storage/enrichment/opera/installed/R2023b \
  -s /root/autodl-tmp/IGEM/GALATEA-sustainable/data/raw/skincare/opera/input.sdf \
  -o /root/autodl-tmp/IGEM/GALATEA-sustainable/data/raw/skincare/opera/predictions.csv \
  -e logP WS BCF Koc RB KM -n -v 2
```

非默认安装目录需要将运行时缓存父目录中的 `OPERA_installdir.txt` 设置为实际 `application` 目录。安装时先解决了存储空间，再安装到 `/root/IGEM-storage/enrichment`；原 Python 环境保持原路径的符号链接。

OPERA 事前选择六个终点，共 21×6 个目标输出，123 个有数值。尿素的三个环境终点缺失；单独重算尿素仍在 ReadyBiodeg 描述符处报错，记录保留在原始目录。仅适用于烃类的 BioDeg 半衰期事前排除。KM 是鱼体转化半衰期，与环境降解时间不同。下载表包含原生预测范围，该范围不解释为统一置信区间。各模型训练集并非独立，也不通过平均或投票给出环境安全判定。

`python analysis/run_all.py` 只读取已完成的模型缓存、生成派生表格与图、重建中文页面并检查链接；不会在页面重建时重新访问模型服务或自动重训。实际新模型运行与页面重建分别记录。

图片同时提供 PNG 和 SVG；CSV 保留数值精度。外部文献实验、机器学习预测、条件计算分别标注。对照成分不自动成为阴性标准品，模型分数不转写为人体发生率。
