---
layout: post
title: "PCIe 7.0 重传机制：Retry Buffer、Ack/Nak 与 Replay Timer"
date: "2026-08-21 00:00:00"
description: "以PCIe 7.0 Base Specification第3.6节为主线，说明Non-Flit与Flit Mode下的数据链路重放机制"
tags: [Protocol, PCIe, Data Link Layer, Replay]
---

## 1 为什么PCIe需要重传机制

PCIe的数据链路重传称为**Replay**。它用于恢复单条Link上的瞬态传输错误，例如TLP或Flit损坏、Ack/Nak反馈丢失等。Replay完全由相邻两个Port的数据链路层完成，不要求事务层或软件重新提交事务。

PCIe 7.0 Base Specification于2025年6月发布，最高数据速率为128.0 GT/s。PCIe 7.0继续使用PCIe 6.0引入的PAM4与Flit Mode，同时保留与旧设备和Non-Flit Mode互操作的能力。本文以PCIe 7.0 Base Specification的§3.6为主线，重点解释以下问题：

1. 为什么发送完成后仍然需要保存TLP或Flit？
2. Ack、Nak和Replay Timer分别解决什么问题？
3. 收到Nak和发生Replay Timeout时，发送端如何确定重传起点？
4. Non-Flit Mode与Flit Mode的重传粒度有何不同？

> Replay是逐跳（Link-local）可靠性机制。TLP经过Switch后，会在下一条Link上重新建立独立的序号、确认和Replay状态。

## 2 重传机制的基本闭环

无论采用哪种传输模式，重传机制都可以抽象为以下闭环：

```text
发送数据并分配序号
        ↓
将副本保存到Transmit Retry Buffer
        ↓
通过物理链路发送
        ↓
接收端执行完整性与顺序检查
        ↓
   ┌────┴────┐
   │         │
接收成功    检测到错误
   │         │
Ack反馈     Nak反馈
   │         │
释放副本    启动Replay
   │         │
   └────┬────┘
        │
若Ack/Nak长时间均未返回
        ↓
REPLAY_TIMER超时并启动Replay
```

这里存在三个相互配合的核心机制：

- **Transmit Retry Buffer**：保存尚未得到确认的数据副本，保证发送端具有可重放的数据。
- **Ack/Nak**：接收端向发送端反馈已正确接收的边界，或者要求发送端执行Replay。
- **REPLAY_TIMER**：处理Ack/Nak本身丢失的情况，避免发送端永久等待。

## 3 Non-Flit Mode的发送端状态

### 3.1 Sequence Number

Non-Flit Mode为需要可靠传输的TLP分配Data Link Layer Sequence Number。序号使接收端能够判断：

- 当前TLP是否正好是下一个期望的TLP；
- 中间是否缺失了TLP；
- 当前TLP是否是Replay产生的重复副本。

Sequence Number描述的是本条Link上的发送顺序，不是事务层的Tag，也不是全局事务编号。当TLP经过Switch转发到下一条Link时，会使用下一条Link的数据链路序号。

### 3.2 Transmit Retry Buffer

发送端将TLP交给物理层时，不能立即删除本地副本，而是必须将其保存在Transmit Retry Buffer中，直到收到能够确认该TLP的Ack。

```text
Transaction Layer
        │
        ▼
分配Sequence Number并生成LCRC
        │
        ├──────────────► Physical Layer
        │
        └──► Transmit Retry Buffer
                     │
                     └── 收到Ack后释放
```

Ack采用累计确认语义。收到确认边界后，发送端可以释放截至该边界的所有已确认TLP，而不是只释放一个TLP。没有得到确认的TLP必须继续保留。

### 3.3 REPLAY_TIMER与REPLAY_NUM

发送端还需要维护Replay相关状态：

- `REPLAY_TIMER`：监视发送端是否长时间没有获得有效的确认进展。
- `REPLAY_NUM`：记录连续Replay行为，用于识别链路是否反复重放仍无法恢复。

`REPLAY_TIMER`不是在TLP写入Transmit Retry Buffer时启动，而是在任意TLP发送或重传的最后一个Symbol发出时启动，前提是Timer尚未运行。Timer一旦开始运行，随后继续发送普通新TLP不会反复将其清零，否则持续发送新TLP可能无限延长最早未确认TLP的等待时间。

```text
TLP写入Transmit Retry Buffer
        │
        │ Timer尚未启动
        ▼
通过物理链路发送TLP
        │
        ▼
发出该TLP的最后一个Symbol
        │
        └─ REPLAY_TIMER尚未运行时，从此处开始计时
```

运行过程中，`REPLAY_TIMER`按照以下规则更新：

- **收到带来确认进展的Ack**：如果该Ack确认了Retry Buffer中的一个或多个新TLP，并且仍有其他未确认TLP，Timer清零并重新启动。
- **收到没有确认进展的重复Ack**：Timer不重新启动。该规则防止重复Ack掩盖链路长期没有取得进展的问题。
- **收到Nak**：除正在Replay的情况外，Timer清零并保持停止，等待Replay过程提供新的启动点。
- **开始一次Replay**：发送第一个重传TLP的最后一个Symbol时，Timer清零并重新启动。
- **全部TLP均已确认**：Timer清零并保持停止，直到之后再次满足启动条件。
- **链路正在重新训练**：LTSSM处于Recovery或Configuration时，Timer保持当前值，不继续计数。
- **Timer到期**：Timer清零并保持停止，同时触发Replay；随后在第一个重传TLP的最后一个Symbol发出时重新启动。

例如发送端连续发送Seq 10、11和12时，Timer在Seq 10的最后一个Symbol发出后启动，发送Seq 11和12不会刷新它。如果随后收到确认至Seq 10的Ack，由于确认边界取得进展但仍有Seq 11和12未确认，Timer重新启动；再次收到确认至Seq 10的重复Ack则不会重新启动。收到确认至Seq 12的Ack后，Retry Buffer不再包含未确认TLP，Timer停止。

因此，`REPLAY_TIMER`不是为每个TLP分别配置的计时器，也不是简单测量某一个TLP在Buffer中停留的时间。它用于限制发送端在存在未确认数据时，能够容忍的最长“无确认进展”时间。

单次Replay Timer Timeout并不等价于Link立即进入`DL_Inactive`。PCI-SIG的FAQ明确说明：Timer到期后应重传Transmit Retry Buffer中的TLP，同时报告Replay Timer Timeout错误。

## 4 接收端如何产生Ack和Nak

接收端收到Non-Flit TLP后，需要检查至少两类信息：

1. **完整性**：LCRC是否正确。
2. **顺序**：Sequence Number是否符合当前期望值。

处理结果可以简化为：

| 接收结果 | 接收端动作 | 发送端后续动作 |
| --- | --- | --- |
| LCRC正确且序号符合预期 | 接收TLP并更新确认边界 | 收到Ack后释放已确认副本 |
| LCRC错误或检测到序号缺口 | 不向事务层交付错误TLP | 收到Nak后从未确认边界开始Replay |
| 收到已经正确接收过的Replay副本 | 不重复交付事务层 | 重新反馈当前确认边界 |

Ack只表示数据已经可靠通过当前Link，它不代表事务已经在最终Completer执行完成。例如Memory Read Request的Ack与随后返回的Completion是两个不同层次的事件。

## 5 触发Replay的两条主要路径

### 5.1 收到Nak

Nak表示接收端已经发现错误或序号不连续。发送端根据Nak携带的确认边界，找到Transmit Retry Buffer中最早仍未确认的TLP，并从该位置开始Replay。

这种方式反应最快，因为发送端不需要等待Timer到期：

```text
Tx发送：Seq 100、101、102、103
Rx确认：正确收到至Seq 101
Rx发现：Seq 102损坏
Rx发送：Nak，确认边界停留在101
Tx动作：从Seq 102开始Replay
```

### 5.2 REPLAY_TIMER超时

如果Transmit Retry Buffer中仍然存在未确认TLP，并且在超过适用的`REPLAY_TIMER Limit`后仍未收到任何Ack或Nak，发送端必须启动Replay。

这个规则解决的是“反馈丢失”问题：原始TLP可能已经到达，但Ack在返回过程中损坏；也可能原始TLP和Nak均未成功到达发送端。发送端无法区分这些情况，因此只能保留副本并在超时后重新发送。

## 6 PCIe 7.0规定的Simplified REPLAY_TIMER Limit

PCIe 7.0在Non-Flit Mode下给出了Simplified REPLAY_TIMER Limit：

| Extended Synch | REPLAY_TIMER Limit |
| --- | ---: |
| Clear | 24,000～31,000 Symbol Times |
| Set | 80,000～100,000 Symbol Times |

上下限均包含在允许范围内，`-0%/+0%`表示实现选择的Limit不能在该范围之外增加额外容差。

### 6.1 Extended Synch为什么会改变Limit

`Extended Synch`主要用于测试场景。设置该位会延长部分物理层同步过程，因此允许更长的Ack/Nak返回等待时间，Replay Timer范围也随之增大。

如果存在未确认TLP时Extended Synch发生变化，实现可以选择：

- 在该位变化时立即调整`REPLAY_TIMER Limit`；或者
- 等待下一次`REPLAY_TIMER`复位时再使用新的Limit。

### 6.2 不同速率实现的要求

- **支持16.0 GT/s或更高速率的实现**：在Non-Flit Mode下，所有实际运行速率都必须使用Simplified REPLAY_TIMER Limit。
- **最高仅支持低于16.0 GT/s速率的实现**：强烈建议在所有速率使用Simplified Limit，但允许继续使用PCIe 3.1定义的传统Limit。

这里判断的是实现的最高能力，而不是当前协商速率。例如一个支持16.0 GT/s的Port当前降速到8.0 GT/s运行，仍属于必须使用Simplified Limit的实现。

> Symbol Time是规范定义的链路时间单位。分析Timer时应按照当前模式和编码规则换算，不能直接把Symbol Times当作固定数量的软件时钟周期。

## 7 一次完整的Non-Flit Replay示例

假设发送端依次发送四个TLP：

```text
Transmit Retry Buffer：

Seq 200 | Seq 201 | Seq 202 | Seq 203
```

处理过程如下：

1. 发送端为四个TLP分配序号并保存副本。
2. 接收端正确收到Seq 200和Seq 201。
3. Seq 202发生LCRC错误，接收端不将其交付事务层。
4. 接收端发送Nak，确认边界停留在Seq 201。
5. 发送端释放Seq 200和Seq 201的副本。
6. 发送端从Seq 202开始重放Seq 202和Seq 203。
7. 接收端正确接收重放数据并返回Ack。
8. 发送端释放剩余Retry Buffer空间，Replay结束。

如果第4步的Nak丢失，`REPLAY_TIMER`最终会代替Nak触发相同的重放动作。

## 8 Flit Mode下重传粒度发生了什么变化

PCIe 7.0的Flit组织方式与PCIe 6.0相同。每个Flit固定为256 Byte，其中包含：

| 区域 | 大小 | 用途 |
| --- | ---: | --- |
| TLP区域 | 236 Byte | 承载一个或多个TLP，TLP也可以跨Flit |
| DLP区域 | 6 Byte | 承载Ack/Nak、Replay等数据链路控制信息 |
| CRC | 8 Byte | 对TLP区域和DLP区域进行强错误检测 |
| FEC | 6 Byte | 对整个Flit提供低延迟纠错 |

接收端首先执行FEC纠错，再执行CRC检查。无法由FEC纠正且被CRC检测出的错误，会进入Flit级Replay流程。

这带来了几个重要差异：

- Replay Buffer保存的是需要重放的Payload Flit，而不再是带独立LCRC的Non-Flit TLP。
- 一个Flit可以包含多个TLP，一个TLP也可能跨越多个Flit，因此重放粒度不再等于事务层TLP边界。
- Ack/Nak等信息位于每个Flit固定的DLP区域，不需要等待独立DLLP插入链路。
- NOP Flit不消耗Payload Flit序号，不进入Tx Replay Buffer，也不需要Replay。

PCIe 7.0官方资料还区分了两种Nak策略：

- **Selective Nak**：在接收端能够确定具体受损Payload Flit时，尽量缩小需要重放的范围。
- **Standard Nak**：当接收状态不足以安全地选择局部范围时，回到更保守的确认边界执行重放。

Replay开始时，发送端通过Replay Command和显式发送序号重新建立接收端对重放序列的理解。这里的目标不是消除所有Replay，而是在保证可靠性的前提下减少不必要的重复数据和带宽损失。

## 9 Non-Flit与Flit Mode重传对比

| 对比项 | Non-Flit Mode | Flit Mode |
| --- | --- | --- |
| 基本保护和Replay单元 | TLP | 256 Byte Flit |
| 错误检测 | 每个TLP的LCRC | Flit级64-bit CRC |
| 错误纠正 | 无FEC | 3路交织的轻量FEC |
| 确认信息 | Ack/Nak DLLP | Flit中的DLP区域 |
| Retry Buffer内容 | 未确认TLP副本 | 未确认Payload Flit |
| 空闲传输单元 | 不适用 | NOP Flit不进入Replay Buffer |
| 典型重放方式 | 从未确认TLP边界回退 | Selective Nak或Standard Nak控制Flit重放 |

二者虽然重传粒度不同，但可靠性闭环相同：**保存副本、检测错误、反馈确认、必要时Replay、确认后释放缓存**。

## 10 Replay Timeout是否意味着链路失效

不是。Replay Timer Timeout首先触发的是数据链路Replay，并可以作为Replay Timer Timeout错误上报；它不会仅因为一次Timeout就直接要求链路退出`DL_Active`。

需要区分：

- **一次Replay Timeout**：可能只是Ack/Nak丢失，重新发送后仍可恢复。
- **连续Replay失败**：会涉及`REPLAY_NUM`及其Rollover规则，并产生进一步的错误报告或恢复动作。
- **Physical LinkUp变为0**：属于链路已经失效，数据链路状态机需要退出`DL_Active`。

因此，Replay负责处理“链路仍在工作但某次传输不可靠”的情况；`DL_Inactive`处理的是“数据链路已经不具备正常工作条件”的情况。

## 11 常见理解错误

### 11.1 Ack等于事务完成

错误。Ack只确认TLP或Flit已经可靠通过当前Link，不代表请求已经由最终Completer执行。

### 11.2 收到Nak只重发一个TLP

不一定。发送端必须按照确认边界和当前模式的Replay规则重放相应范围。Non-Flit通常从最早未确认TLP开始；Flit Mode还需要考虑Selective Nak、Standard Nak与显式序号。

### 11.3 Retry Buffer可以在发送后立即释放

错误。在能够确认数据已被对端可靠接收以前，发送端必须保存副本，否则收到Nak或发生Timeout时将没有数据可供重放。

### 11.4 ECRC错误会直接触发本Link Replay

错误。ECRC用于端到端完整性检查，而Non-Flit链路重放主要由LCRC和Data Link Sequence Number驱动。Flit Mode则由Flit级FEC、CRC和DLP反馈共同完成链路可靠性处理。

### 11.5 Retimer也维护Retry Buffer

错误。Retimer属于物理层，不终止数据链路协议，也不维护TLP/Flit Replay Buffer。Replay状态存在于Link两端的Port中；如果一个组件终止并重新建立数据链路状态，它的角色更接近Switch而不是Retimer。

## 12 总结

PCIe重传机制的核心不是“发现错误后再发一次”这么简单，而是一套完整的链路可靠性协议：

1. 发送端为数据建立顺序，并在Retry Buffer中保存副本。
2. 接收端检查完整性与顺序，通过Ack/Nak反馈确认边界。
3. Nak负责快速触发Replay，`REPLAY_TIMER`负责处理反馈丢失。
4. Ack采用累计确认，使发送端能够安全释放Retry Buffer。
5. Non-Flit Mode以TLP为主要重放对象，Flit Mode以固定大小Flit为保护和重放单位。
6. Replay只处理单条Link上的瞬态错误，不替代事务层Completion、软件错误恢复或链路重新训练。

理解§3.6时，最重要的是始终追踪三个状态：**最早未确认数据在哪里、Retry Buffer中还保存了什么、什么事件会推进或回退确认边界**。

## 参考资料

- [PCI Express Base Specification Revision 7.0](https://pcisig.com/PCIExpress/Spec/Base/_7.0)
- [PCIe 7.0 Specification Webinar Q&A](https://pcisig.com/blog/pcie-70-specification-next-generation-performance-meet-needs-advanced-ai-applications-webinar)
- [PCIe 6.0 Flit Mode、PAM4与FEC说明](https://pcisig.com/blog/evolution-pci-express-specification-its-sixth-generation-third-decade-and-still-going-strong)
- [PCIe 6.0 Flit Mode Webinar Q&A](https://pcisig.com/blog/pcie%C2%AE-60-specification-webinar-qa-deeper-dive-flit-mode-pam4-and-forward-error-correction-fec)
- [PCI-SIG FAQ：Replay Timer到期后的行为](https://pcisig.com/section-3521-if-you-can-receive-tlps-and-flow-control-dllps-normally-do-not-receive-any-ack-or-nak)
