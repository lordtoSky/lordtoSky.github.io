---
layout: post
title: "TLP + DMA 的实现"
date: "2026-09-28 00:00:00"
description: "TLP 与 DMA 实现笔记"
tags: [PCIe, TLP, DMA]
---

## 问题建模

采用 Xilinx 7 Series Integrated Block for PCI Express IP。该硬核实现 PCIe 物理层、数据链路层及部分事务层功能，并通过 AXI4-Stream 向用户逻辑提供 TLP 接口；设计重点是如何解析、生成和调度 TLP 数据流。

开发底板为 XC7Z100。采用 7 Series Integrated Block for PCI Express，链路工作在 PCIe Gen2，单 Lane 速率为 5.0 GT/s。

## PCIe 与 AXI4-Stream 设计参数

本设计固定采用 **PCIe Gen2 ×4、128-bit AXI4-Stream、125 MHz**。PCIe 链路与用户接口的理论有效带宽相等：

```text
PCIe：5.0 GT/s × 4 Lane × 8/10 = 16 Gbit/s = 2 GB/s
AXIS：128 bit × 125 MHz          = 16 Gbit/s = 2 GB/s
```

PCIe 为全双工链路，因此发送和接收方向各自具有 2 GB/s 的理论带宽，不能将其理解为两个方向共享 2 GB/s。

| 参数 | 配置值 | 说明 |
|---|---:|---|
| FPGA | XC7Z100 | Zynq-7000 系列 |
| PCIe IP | 7 Series Integrated Block for PCI Express | PG054 对应的 Gen2 PCIe Hard Block |
| PCIe 角色 | Endpoint | 由主机作为 Root Complex 枚举 |
| PCIe 代际 | Gen2 | 兼容 PCI Express Base Specification 2.1 |
| Lane 数量 | ×4 | 板级设计需要连接连续的4条 GTX Lane |
| 单 Lane 速率 | 5.0 GT/s | Gen2 使用 8b/10b 编码 |
| 链路理论有效带宽 | 2 GB/s/方向 | 已扣除 8b/10b 编码开销，未扣除 TLP/DLLP 等协议开销 |
| AXI4-Stream 数据宽度 | 128 bit | 每个有效 Beat 传输16字节 |
| AXI4-Stream 时钟 | 125 MHz | 使用 IP 输出的 `user_clk_out` |
| AXIS 理论带宽 | 2 GB/s/方向 | 与 Gen2 ×4 链路有效带宽匹配 |
| TX 接口 | `s_axis_tx_*` | DMA/TLP生成逻辑向 PCIe 核发送完整 TLP |
| RX 接口 | `m_axis_rx_*` | PCIe 核向 DMA/TLP解析逻辑输出完整 TLP |
| TX `tdata` | `s_axis_tx_tdata[127:0]` | TLP Header 与 Payload 共用同一数据流 |
| TX `tkeep` | `s_axis_tx_tkeep[15:0]` | 非末拍为 `16'hFFFF`；末拍按有效 DWORD 取 `000F/00FF/0FFF/FFFF` |
| TX `tuser` | `s_axis_tx_tuser[3:0]` | 依次承载 ECRC、错误转发、Streaming 和 Discontinue 控制 |
| RX `tdata` | `m_axis_rx_tdata[127:0]` | 可能在同一个 Beat 中包含两个不同 TLP 的片段 |
| RX `tuser` | `m_axis_rx_tuser[21:0]` | 包含 BAR Hit、错误状态以及 SOF/EOF 位置 |
| RX SOF | `m_axis_rx_tuser[14:10]` | 指示新 TLP 从 Byte 0 或 Byte 8 开始 |
| RX EOF | `m_axis_rx_tuser[21:17]` | 指示 TLP 结束于 Byte 3、7、11 或15 |
| RX `tlast` | 不使用 | 128-bit RX 模式下固定为低，包边界由 `tuser` 表示 |
| RX Straddle | 必须支持 | 一个 Beat 可同时包含前一 TLP 的结尾和后一 TLP 的开头 |
| 时钟域 | `user_clk_out` | DMA存储侧若使用其他时钟，需要通过异步 FIFO 跨时钟域 |
| 复位 | `user_reset_out` | 用户侧 AXIS 与 TLP处理逻辑采用该同步复位 |

### DMA初始性能参数

以下参数作为第一版实现目标，后续根据主机能力、BAR空间和存储带宽调整：

| 参数 | 初始值/目标 | 设计考虑 |
|---|---:|---|
| Maximum Payload Size（MPS） | 256 Byte | 兼顾传输效率与主机兼容性，以实际协商结果为准 |
| Maximum Read Request Size（MRRS） | 512 Byte | 减少大块DMA读的请求数量，以主机配置结果为准 |
| 并发 Memory Read | 16～32个 | 使用 Tag 表跟踪乱序返回的 Completion |
| 内部数据通路 | 128 bit | 避免在PCIe核与DMA之间重复变宽/变窄 |
| RX入口缓冲 | 至少容纳若干个最大TLP | 吸收DDR或后级逻辑产生的短时背压 |
| TX发送方式 | Store-and-forward 优先 | 第一版关闭 `tx_str`，降低连续供数和异常中止处理难度 |
| 单向持续DMA目标 | ≥ 1.6 GB/s | 理论上限为2 GB/s，实际受协议开销和存储系统限制 |

128-bit RX 必须先经过 Straddle 拆分，再送入单 TLP 解析器：

```text
m_axis_rx
    │
    ▼
Straddle 拆分与包边界恢复
    │
    ▼
TLP Header 解析
    ├── Completion/CplD ──> DMA Read 返回与 Tag 回收
    ├── Memory Write    ──> BAR/本地存储写入
    └── Memory Read     ──> Completion 生成
```

## TLP Payload 写入 PS DDR

PCIe RX 输出的是完整 TLP，但写入 DDR 的通常不是包含 Header 的原始 TLP。TLP 解析器先提取类型、地址、长度、Tag 和 Byte Enable 等控制信息，再把有效 Payload 交给 DMA 写引擎。没有 Payload 的 Memory Read Request 不能直接产生 AXI 写事务。

```text
PCIe Gen2 ×4
      │
      ▼
128-bit RX AXIS @ 125 MHz
      │
      ▼
Straddle 拆分与 TLP Header 解析
      │
      ├── MWr Payload
      └── CplD Payload + Tag匹配
                 │
                 ▼
        DMA写地址与长度生成
                 │
                 ▼
       Payload FIFO / Burst合并
                 │
          ┌──────┴──────┐
          ▼             ▼
   AXI HP0，64-bit  AXI HP2，64-bit
          │             │
          └──────┬──────┘
                 ▼
          PS DDR Controller
                 │
                 ▼
               DDR
```

### PS DDR写通路参数

| 参数 | 配置值 | 说明 |
|---|---:|---|
| PS接口类型 | `S_AXI_HP` | PL侧DMA作为AXI Master，PS HP口作为AXI Slave |
| HP端口选择 | HP0 + HP2 | 两者分别连接不同的DDRC内部端口，避免选择共享同一DDRC端口的HP0+HP1 |
| HP端口数量 | 2 | 单个HP口不足以持续承接2 GB/s的PCIe理论有效带宽 |
| 单个HP数据宽度 | 64 bit | Zynq-7000 HP口支持32/64-bit，选择64-bit |
| 单个HP时钟 | 150 MHz目标 | 使用独立的 `S_AXI_HP0_ACLK` 和 `S_AXI_HP2_ACLK` |
| 单个HP理论带宽 | 1.2 GB/s | `64 bit × 150 MHz ÷ 8` |
| 两个HP理论聚合带宽 | 2.4 GB/s | 仅为接口上限，最终仍受PS DDR控制器和其他DDR访问者限制 |
| PCIe侧输入 | 128 bit @ 125 MHz | 理论2 GB/s |
| 时钟域转换 | 125 MHz → 150 MHz | 在PCIe解析器与HP写引擎之间使用异步Payload FIFO |
| 位宽转换 | 128 bit → 64 bit | 每个选中的HP通道独立完成降宽，调度器按完整数据块在HP0/HP2之间分流 |
| PS端协议 | AXI3 | 若DMA内部使用AXI4，由AXI Interconnect/协议转换器适配HP端口 |
| AXI写类型 | INCR Burst | 避免逐Beat独立写事务 |
| 单次Burst目标 | 16 Beat/128 Byte | 64-bit AXI3端口每Beat为8字节，长数据拆成连续Burst |
| AXI地址对齐 | 至少16 Byte | DMA缓冲区和传输起始地址优先按Cache Line或更大边界对齐 |
| 写响应 | 必须检查 `BRESP` | 只有写响应完成后才能确认对应DDR写事务成功 |
| 缓存一致性 | 非一致 | HP口不维护Cortex-A9 Cache一致性，软件必须使用DMA安全缓冲区或执行Cache同步 |

Zynq-7000 提供4个64-bit AXI HP端口。每个端口在150 MHz下的理论单向带宽为1.2 GB/s，因此单个HP端口会成为 Gen2 ×4 数据通路的上限。HP0与HP1共享一个DDRC内部端口，HP2与HP3共享另一个；本设计优先使用 **HP0 + HP2**，使两个DMA写通道分布到不同的DDRC入口。

双HP口不能简单地把相邻的每个64-bit数据拍交替发送。DMA写调度器应以完整、可独立提交的数据块为单位进行分流，例如按描述符、4 KiB页面或固定大小Chunk选择HP0/HP2，并保证每个AXI ID内部的写事务和写响应顺序可追踪。

### AXI写引擎职责

DMA写引擎至少需要完成：

1. 根据DMA描述符或BAR Offset生成PS DDR物理地址。
2. 根据TLP Length、First BE和Last BE计算真正有效的Payload字节。
3. 将可能跨TLP到达的数据合并为连续AXI Burst。
4. 将128-bit PCIe Payload转换为64-bit HP写数据，并生成正确的 `WSTRB`。
5. 处理4 KiB边界，任何一个AXI Burst都不能跨越4 KiB地址边界。
6. 同时维护多个Outstanding Write，利用HP口内部FIFO隐藏DDR访问延迟。
7. 收集并检查 `BRESP`，发生 `SLVERR` 或 `DECERR` 时停止对应描述符并上报错误。
8. 在描述符完成前，确保所有相关AXI写响应已经返回，避免软件过早读取尚未完成的数据。

### PS软件与Cache一致性

`S_AXI_HP` 是非缓存一致接口。PL DMA写入DDR后，Cortex-A9 Cache中可能仍保存同一地址的旧数据。软件侧应采用以下方式之一：

- Linux驱动使用DMA API分配和映射缓冲区，例如一致性缓冲区或正确配对的流式DMA映射与同步接口；
- 裸机软件在CPU读取DMA缓冲区前执行对应范围的D-Cache Invalidate；
- 将DMA缓冲区映射为非缓存区域，但需要接受CPU访问性能下降。

不得只依赖 `volatile`，因为它不能解决CPU Cache与PL DMA之间的数据一致性问题。

参考资料：

- [7 Series FPGAs Integrated Block for PCI Express Product Guide (PG054)](https://docs.amd.com/r/en-US/pg054-7series-pcie)
- [AXI Interface Frequency](https://docs.amd.com/r/en-US/pg054-7series-pcie/AXI-Interface-Frequency)
- [Transmit Interface](https://docs.amd.com/r/en-US/pg054-7series-pcie/Transmit-Interface)
- [Receive Interface](https://docs.amd.com/r/en-US/pg054-7series-pcie/Receive-Interface)
- [Zynq-7000 PL DMA via AXI High-Performance Interface](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/PL-DMA-via-AXI-High-Performance-HP-Interface)
- [Zynq-7000 AXI HP Interfaces](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/AXI_HP-Interfaces)
- [Zynq-7000 Theoretical Bandwidth](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Theoretical-Bandwidth)
