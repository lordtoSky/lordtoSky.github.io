---
layout: post
title: "Clocking Wizard 动态时钟的 AXI 重配置"
date: 2026-11-14
description: "用 AXI 覆写 Xilinx Clocking Wizard 的 DRP 参数实现动态改频：寄存器流程、状态机划分与延迟构成。"
tags: [AXI, FPGA, 时钟, RTL]
---

## 场景

Xilinx 的 Clocking Wizard 支持动态配置，可通过 AXI 或 DRP 覆写参数。

AXI 重配置 PLL 的基本流程为：

```text
1. W — address 0x304, data = new CLKOUT0 Register 1 DRP word.
2. W — address 0x308, data = new CLKOUT0 Register 2 DRP word.
3. R — address 0x004, check returned RDATA[0]=1 (currently locked).
4. W — address 0x35C, data 0x00000003 (start reconfiguration).
5. R — address 0x004, repeat until RDATA[0]=0.
6. R — address 0x004, repeat until RDATA[0]=1 (relocked).
```

其中地址和设置参数均需要参考对应 IP source 的 DRP 内容来设置。

## 实现思路

### 概述

- 外部输入单脉冲 recfg 请求，同时传入重配置后的时钟频率；
- 模块收到请求以及目的频率后，查表确认该频率对应的配置参数；
- 按照流程通过 AXI 写入配置并确认 PLL 状态；
- 确认 PLL 已锁定，返回 `pll_locked`，完成 recfg 流程。

### 细节

#### 1. 状态控制

整个重配置流程可以分为：请求 -> 查表 -> 写入 -> 查询 -> 结束 这五个主要状态。

需要一个 global state 来控制；写入部分同样需要一个子状态机 cfg state 来控制写入状态。

#### 2. 错误处理

写入部分可能出现 b-err。出现 err 后是立即重试，还是整体写完之后再重试，需要先明确策略。

#### 3. 配置延迟

实际上就是整个 recfg 的最短时间消耗，也就是从 hpd 生效后，到显示器可以显示图像的延迟。这段延迟主要的影响因素有：

```text
  ------------    ------------------    --------------     -----------
  |hpd检测延迟| -> |recfg参数查表延迟| -> |recfg写入延迟| -> |pll锁定延迟|
  ------------    ------------------    --------------     -----------
                                                                 |
                                          ------------     ------------
                                         |recfg退出延迟| <- |状态确认延迟|
                                          ------------     -------------
```

### 实现

#### global state

state stage：IDLE -> REQ -> LUT -> CFG -> CONFIRM -> DONE

状态内容：

| stage   | aim                                 |
| ------- | ----------------------------------- |
| IDLE    | idle                                |
| REQ     | chk recfg req and decode freq type1 |
| LUT     | look up target freq factors         |
| CFG     | wr reg through axi                  |
| CONFIRM | chk if pll locked                   |
| DONE    | return 0                            |

状态转换规则：

| stage           | conditions                           |
| --------------- | ------------------------------------ |
| IDLE -> REQ     | `recfg_req` active                   |
| REQ -> LUT      | 1 tap delay (to lock the recfg_freq) |
| LUT -> CFG      | `LUT_chk` active                     |
| CFG -> CONFIRM  | `CFG_wr_done` active                 |
| CFG -> CFG      | `b_err` active                       |
| CONFIRM -> DONE | `LOCKED` active                      |
| DONE -> IDLE    | `PLL_locked` active                  |

#### recfg state

state stage：IDLE -> WR_REG1 -> WR_REG2 -> RD_LOCKED -> WR_RECFG -> RD_UNLOCK -> RD_DONE

状态内容：

| stage     | R/W  | addr  | data             | usage     |
| --------- | ---- | ----- | ---------------- | --------- |
| IDLE      | None | None  | None             | idle      |
| WR_REG1   | W    | 0x304 | CLKOUT_REG1_DATA | factor    |
| WR_REG2   | W    | 0x308 | CLKOUT_REG2_DATA | factor    |
| RD_LOCKED | R    | 0x004 | pll locked state | ip state  |
| WR_RECFG  | W    | 0x35C | 0x00000003       | start pll |
| RD_UNLOCK | R    | 0x004 | pll locked state | ip state  |
| RD_DONE   | R    | 0x004 | pll locked state | ip state  |

状态转换规则：

| stage                  | operation            |
| ---------------------- | -------------------- |
| IDLE      -> WR_REG1   | `recfg_req` active   |
| WR_REG1   -> WR_REG2   | aw&w handshake done  |
| WR_REG2   -> RD_LOCKED | aw&w handshake done  |
| RD_LOCKED -> WR_RECFG  | `pll_locked` active  |
| WR_RECFG  -> RD_UNLOCK | 1 cycle delay        |
| RD_UNLOCK -> RD_DONE   | `pll_locked` active  |
| RD_DONE   -> IDLE      | 1 cycle delay        |

**AW & W 握手判断**：采用直接顺序写的方式完成，即顺序写入后读取状态，当读取结果满足时完成操作，不做多通道共同握手判断。

握手的判断则主要由 AXI 从机的 `awready` / `wready` 与写响应 `bresp` 决定：AW、W 各自握手成功后写入才会被接受，收到正常 `bresp` 才认为该寄存器写入完成，随后推进到下一个状态。
