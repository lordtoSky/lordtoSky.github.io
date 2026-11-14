## 场景

xilinx的clocking wizzard具备动态配置功能，通过axi或drp实现覆写

基本流程为：

```text
1. W — address 0x304, data = new CLKOUT0 Register 1 DRP word.
2. W — address 0x308, data = new CLKOUT0 Register 2 DRP word.
3. R — address 0x004, check returned RDATA[0]=1 (currently locked).
4. W — address 0x35C, data 0x00000003 (start reconfiguration).
5. R — address 0x004, repeat until RDATA[0]=0.
6. R — address 0x004, repeat until RDATA[0]=1 (relocked).
```

其中地址和设置参数均需要参考对应ip source的drp内容来设置

## 实现思路

### 概述

- 外部输入单脉冲recfg请求，同时传入重配置时钟频率
- 模块收到请求以及目的频率后，查表确认该频率对应配置参数
- 按照流程通过axi写入配置并确认pll状态
- 确认pll已锁定，返回pll_locked，完成recfg流程

### 细节

#### 1. 状态控制

整个重配置流程可以分为：请求->查表->写入->查询->结束 这五个主要状态

需要一个global_state来进行控制，在写入部分同样需要一个子状态机cfg_state来控制写入状态

#### 2. 错误处理

其中写入部分可能出现b-err，如果出现err该如何处理，立即重试或整体写完后再重试？

#### 3. 配置延迟

实际上就是整个recfg的最短时间消耗，也就是从hpd生效后，到显示器可以显示图像的延迟
这段延迟主要的影响因素有：

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

state stage: IDLE -> REQ -> LUT -> CFG -> CONFIRM -> DONE

各阶段的触发条件分别为：

| stage | conditions |
|---|---|
| IDLE -> REQ | `recfg_req` active |
| REQ -> LUT | 1 tap delay (to lock the recfg_freq) |
| LUT -> CFG | `LUT_chk` active |
| CFG -> CONFIRM | `CFG_wr_done` active |
| CFG -> CFG | `b_err` active |
| CONFIRM -> DONE | `LOCKED` active |
| DONE -> IDLE | `PLL_locked` active |

#### recfg state
