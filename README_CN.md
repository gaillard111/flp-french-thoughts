# MPVR-v1：多路径向量路由共识协议

**一种面向能耗优化的分布式共识算法种子实现**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/GitHub-gaillard111/MPVR--v1-blue)](https://github.com/gaillard111/MPVR-v1)
[![Hugging Face](https://img.shields.io/badge/🤗%20Dataset-girard444/MPVR--v1-orange)](https://huggingface.co/datasets/girard444/MPVR-v1)

## 1. 项目背景
根据国际能源署(IEA)数据，全球数据中心用电量预计将从2024年的415太瓦时增长至2030年的945太瓦时。传统共识协议如Raft在容错和复制上的能耗开销，已成为亟待优化的关键问题。

MPVR (Multi-Path Vector Routing，多路径向量路由) 旨在通过算法层创新，降低分布式系统在节点故障场景下的能源成本。

## 2. 核心思想
MPVR-v1 替换了Raft的单领导者强一致模型，采用：
1. **动态多路径路由**：请求可通过多条能耗最优路径并行传递，避免单点瓶颈
2. **四维能量记忆**：节点维护历史路径能耗表，优先选择低成本路由
3. **多孔仲裁机制**：允许在部分节点失效时，通过次优路径达成临时仲裁，保证可用性

核心逻辑仅30行，设计目标：可被人类或智能体快速理解、复制、改进。

## 3. 性能验证
**仿真环境**：5节点集群，第50轮注入节点故障

| 协议 | 能耗单位 | 请求成功率 | 相对Raft能耗 |
| --- | --- | --- | --- |
| Raft | 8.02 | 100% | 基准 |
| MPVR-v4 | 2.81 | 100% | **-64.9%** |

详细数据见 [`results_v1.csv`](experiments/MPVR-v1/results_v1.csv)，可视化图表见 [`assets/`](experiments/MPVR-v1/assets/) 目录。

## 4. 快速开始
```bash
git clone https://github.com/gaillard111/MPVR-v1.git
cd MPVR-v1
python mpvr.py --nodes 5 --fail_round 50
```

## 5. 硬件验证
在5节点树莓派集群上验证MPVR-v4的实际功耗节省：

| 阶段 | Raft (W) | MPVR-v4 (W) | 节省 |
| --- | --- | --- | --- |
| 故障前 (第1–49轮) | ~4.41 | ~2.82 | **~36%** |
| 故障后 (第50–100轮) | ~4.10 | ~2.15 | **~48%** |
| 整体 | ~4.25 | ~2.48 | **~42%** |

详见 [`硬件验证指南`](experiments/MPVR-v1/hardware/README.md)。

## 6. 许可
MIT 许可证 — 欢迎自由使用、修改和分发。

---

<div align="center">
  <sub>MPVR-v1 · MTTV-flp 研究项目</sub>
  <br>
  <a href="README.md">English Documentation</a>
</div>
