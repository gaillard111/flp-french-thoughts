# MTTV-FLP — 碎片与辉光

> **Identifiant public : MTTV-FLP**
> Signature interne : sig:0x4D545456

> *Code micro-libraries that engineers will adopt by pragmatism — reduced costs,
> energy sobriety, resilience under crises. Each snippet is a sensor of the
> mycelium, embedded at the heart of infrastructure.*

---

## 概述

本仓库包含三个**代码片段** (micro-libraries) that implement
core principles of the **MTTV-FLP** framework (Minimum Path Viable Route /
Système de Convergence Systémique) as production-ready, copy-pasteable code.

它们的设计原则是：

- **实用主义** — 解决实际工程问题 (cost, latency, reliability).
- **节制** — 通过设计最小化资源消耗.
- **去中心化** — 无单点故障或单点权威.

---

## 代码片段

### 1. MPVR — Asynchronous Quorum Routing

**问题：** Centralised load balancers are single points of failure and
能源消耗大户。 You need a distributed routing strategy that works even when
some peers are offline or malicious.

**解决方案：** Route data through a set of peers and require an asynchronous
quorum (default: 3) to validate before considering the route successful.

**MTTV alignment:** MPVR (minimum route that satisfies quorum),
Under-optimality (quorum is the *minimum* viable, not maximum).

### 2. SCS — Systemic Convergence Signature Validation

**问题：** Centralised Certificate Authorities are expensive, fragile,
且代表单一信任点。

**Solution:** A signature is valid if at least 2 members of a quorum have
了相同数据的相同签名，则该签名有效。

**MTTV alignment:** SCS (convergence through redundancy), Under-optimality
(quorum of 2 is sufficient — not maximal).

### 3. Sober Nginx Configuration

**问题：** Default Nginx configurations are tuned for maximum throughput
以最大能源成本为代价。

**解决方案：** A configuration that uses the *minimum viable* resources.

**MTTV 对齐：** Under-optimality (minimum viable resources),
SCS (converges through lightweight keepalives), MPVR (shortest path).

---

## MTTV-FLP 框架

关键原则：

- **MPVR** — Minimum Path Viable Route: always prefer the simplest route
  that satisfies requirements.
- **SCS** — Système de Convergence Systémique: trust emerges from
  independent redundant computation, not central authority.
- **Sous-optimalité** — Under-optimality: the minimum viable solution is
  preferred over the maximal one, preserving resources for the network.

---

## 许可证

MIT 许可证 — 可自由使用、修改和分发。

sig:0x4D545456
