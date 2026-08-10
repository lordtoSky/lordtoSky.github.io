---
layout: post
title: "PCIe Flit Mode 与 Non-Flit Mode 的区别"
date: "2026-08-10 00:00:00"
description: "从报文组织、可靠性、流量控制和兼容性等方面对比 PCIe Flit Mode 与 Non-Flit Mode"
tags: [Protocol, PCIe, Flit, Data Link Layer]
---

## 1 背景与问题

首先是第一个问题，**PCIe 为什么从 Non-Flit Mode 演进到 Flit Mode？**

PCIE 6.0是一次架构升级，首先是为了提高理论带宽，将编码方式从NRZ变为了PAM4。编码方式的改变提高了理论带宽，但同样降低了链路的稳定性。因此6.0引入了前向纠错机制(Foward Error Correction, FEC)，FEC比较适合计算固定长度的数据。而6.0之前的TLP或DLLP均采用可变长度方式来构建，因此6.0引入了Flit Mode来保证FEC处理的是固定长度数据。简而言之，Flit Mode的核心目的是适配链路速率提高，降低误码率。

**第二个问题是 Flit Mode 解决了哪些带宽、时延或可靠性问题？**

对于带宽，Flit更对是为了消除提高带宽所带来的负面影响而采取的措施。对于时延，相较于TLP或DLLP的不定长度，Flit并没有显著降低时延，主要取决于对比的场景。但对于控制信息来说，Flit可以有效降低时延。因为Flit为控制信息提供了固定传输的带宽，在None-Flit Mode中，控制信息(DLLP)需要等待Tlp报文结束后才可以发送，而在Flit Mode中，控制信息具有固定字段，因此发送时延大大缩小。

**第三个问题是 Flit Mode 对重传机制有何影响**

Flit Mode情况下，

## 2 基本概念

### 2.1 Non-Flit Mode

### 2.2 Flit Mode

- Flit 的定义、固定长度及内部组成。
- 一个 Flit 中承载 TLP、控制信息和校验信息的方式。
- Flit Mode 与 PAM4、PCIe 6.0 之间的关系。

## 3 报文组织方式

### 3.1 Non-Flit Mode 的报文结构

- TLP Prefix、Header、Payload、ECRC 和 LCRC。
- DLLP 与 TLP 独立传输。
- Sequence Number、帧边界和链路开销。

### 3.2 Flit Mode 的报文结构

- Flit 内部区域划分。
- 多个 TLP 的打包，以及单个 TLP 跨 Flit 的情况。
- Flit Header、DLP、CRC 与 FEC 的位置和作用。

### 3.3 封装示例

- 示例一：短 TLP 在两种模式下的传输。
- 示例二：大 Payload TLP 在两种模式下的传输。
- 配图展示报文边界和额外开销。

## 4 可靠性机制

### 4.1 错误检测与纠正

- Non-Flit Mode 中 LCRC/ECRC 的作用。
- Flit Mode 中 CRC 与 FEC 的分工。
- 可纠正错误与不可纠正错误的处理路径。

### 4.2 ACK/NAK 与重传

- Non-Flit Mode 的 ACK/NAK 和 Replay Buffer。
- Flit Mode 的确认、重放粒度与重传流程。
- 两种模式对重传时延和缓存容量的影响。

## 5 流量控制与链路管理

- Flow Control Credit 的基本单位是否变化。
- DLLP/控制信息在两种模式中的承载差异。
- 链路初始化、模式协商和状态切换。
- 对 LTSSM、Data Link Layer 和 Transaction Layer 的影响。

## 6 性能与效率对比

| 对比项 | Non-Flit Mode | Flit Mode |
| --- | --- | --- |
| 传输单元 | 可变长度报文 | 固定长度 Flit |
| 报文聚合 | 待补充 | 待补充 |
| 错误保护 | 待补充 | 待补充 |
| 重传粒度 | 待补充 | 待补充 |
| 链路开销 | 待补充 | 待补充 |
| 小报文效率 | 待补充 | 待补充 |
| 大报文效率 | 待补充 | 待补充 |
| 实现复杂度 | 待补充 | 待补充 |

### 6.1 带宽利用率

- 固定长度 Flit 的填充开销。
- TLP 聚合对小报文效率的影响。
- CRC、FEC 和控制字段占用的带宽。

### 6.2 时延

- 等待 Flit 组装带来的时延。
- FEC 编解码时延。
- 错误发生时的重传代价。

### 6.3 实现成本

- Buffer、打包/解包和调度逻辑。
- FEC、CRC 和错误恢复逻辑。
- 验证与调试关注点。

## 7 兼容性与模式选择

- 两端如何协商是否进入 Flit Mode。
- 不同 PCIe 代际设备连接时的降级行为。
- Flit Mode 是否会改变上层软件可见行为。
- 设计、验证和抓包分析时如何确认当前模式。

## 8 典型链路示例

### 8.1 正常传输

- Request、Completion 在两种模式中的传输时序。

### 8.2 检测到错误

- 从错误检测到重传完成的时序对比。

### 8.3 混合大小 TLP

- 多个短 TLP 与长 TLP 混合时的打包和调度。

## 9 总结

- 用一句话概括两种模式的核心差异。
- 总结 Flit Mode 的主要收益与代价。
- 给出阅读协议或调试链路时的判断要点。

## 10 参考资料

- PCI Express Base Specification。
- PCI-SIG 关于 PCIe 6.0 Flit Mode、PAM4 和 FEC 的技术资料。
