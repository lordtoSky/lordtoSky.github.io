---
layout: post
title: "RTL 状态机重构：状态转移与寄存器所有权分离"
date: "2026-11-05 16:00:00"
description: "以 HDMI Link Manager 为例，说明适合综合、便于时序检查的 SystemVerilog 控制器编码风格。"
tags: [SystemVerilog, RTL, FSM, FPGA, HDMI, Coding-Style]
---

## 问题：为什么不应把所有事情塞进一个 `always_comb`

控制器初版常见的写法，是用一个组合块同时计算状态跳转、候选位图、计数器、当前模式和失败记录，再用一个很大的时序块统一把所有 `*_d` 写回 `*_q`。这种“两段式 FSM”在功能上没有错误，但当会话控制逐渐增加时会变得难以阅读：

- 状态跳转与数据更新交织，难以判断一个寄存器在哪个条件下真正改变；
- 一个状态新增分支时，容易遗漏某个 `*_d` 的保持默认值；
- 组合逻辑扇入越来越大，波形与时序报告也难以定位责任；
- 上游接口信号可能在事务进行中变化，若未锁存，后续 PLL 或配置动作会被意外改变。

HDMI 链路管理器正是这类控制器：它要依次处理 HPD、EDID、解析、模式选择、复位确认、PLL 配置、时序配置和核心启动，还要在 PLL 失败时从候选模式中降级。

本文采用的目标不是“每一个寄存器必须一个块”的机械规则，而是让**每个时序块有清晰、唯一的所有权**，让组合逻辑只承担适合组合计算的任务。

---

## 总体结构

```text
                    +-----------------------+
输入握手/状态 ------> | 状态转移组合逻辑       | ----> state_d
                    +-----------------------+
                                |
                                v
                           state_q 寄存器

状态与输入 ----------> 候选模式寄存器更新 ----> available_vic_q
状态与输入 ----------> 目标模式寄存器更新 ----> pll_target_vic
状态与输入 ----------> 活动模式寄存器更新 ----> active_vic
状态与输入 ----------> 失败记录寄存器更新 ----> last_failed_vic
状态与输入 ----------> PLL 计数器更新 --------> pll_count_q
状态与输入 ----------> 启动计数器更新 --------> startup_count_q

state_q -------------> Moore 输出译码 --------> start/req/enable
```

关键分工如下：

| 部分 | 职责 | 不应承担的职责 |
|---|---|---|
| `always_comb` 状态转移块 | 仅生成 `state_d` | 更新 VIC、位图或计数器 |
| `always_ff` 数据块 | 对单类状态数据作时序更新 | 推导整个控制流程 |
| 连续赋值/输出译码 | 由已寄存的 `state_q` 生成 Moore 输出 | 直接依赖不稳定的组合输入 |
| 小型组合辅助逻辑 | 边界检查、失败条件等纯组合判断 | 隐式保存历史状态 |

---

## 1. 接口：一条信号一行

端口声明不合并堆叠。这样在代码审查、波形搜索、接口增删和连接检查时，每个信号都更容易被独立定位。

```systemverilog
module hdmi_link_manager (
    input  logic         clk_sys,
    input  logic         rst_n,
    input  logic         hpd_connected,
    input  logic         mode_select_done,
    input  logic [7:0]   selected_vic,
    output logic         pll_reconfig_start,
    output logic [7:0]   pll_target_vic,
    output logic         tmds_enable
);
```

这不是综合约束，而是接口维护规则：端口变化通常牵涉顶层连线、testbench 和约束文件，清晰的声明能减少审查漏项。

---

## 2. 状态机：组合块只决定下一状态

状态机保留标准的 `state_q/state_d` 两段形式。`state_d` 的默认值保证未匹配的路径保持当前状态，`default` 则把非法编码导向受控错误状态。

```systemverilog
always_comb begin
    state_d = state_q;

    case (state_q)
        WAIT_SELECT: begin
            if (mode_select_done) begin
                if (mode_supported && selected_vic_available)
                    state_d = WAIT_QUIESCE;
                else
                    state_d = ERROR;
            end
        end

        WAIT_PLL: begin
            if (pll_reconfig_done && !pll_reconfig_error && pixel_pll_locked)
                state_d = ISSUE_CONFIG;
            else if (pll_attempt_failed)
                state_d = ISSUE_SELECT;
        end

        default: state_d = ERROR;
    endcase

    if (!hpd_connected)
        state_d = OFF;
end
```

这里 HPD 断开在末尾统一覆盖正常流程，语义直接：无论当前处于哪一步，断开设备都回到 `OFF`。但它只覆盖**状态**；会话数据如何清除由各自的时序块明确实现。

---

## 3. 寄存器所有权：一类数据，一个时序块

### 3.1 候选模式位图

候选位图属于一次 HPD 会话：EDID 解析成功后装载；PLL 失败或运行中失锁时清除当前 bit；HPD 断开时整体清零。

```systemverilog
always_ff @(posedge clk_sys or negedge rst_n) begin
    if (!rst_n || !hpd_connected) begin
        available_vic_q <= '0;
    end else if (state_q == LOAD_CANDIDATES) begin
        available_vic_q <= LOCAL_VIC_BITMAP & supported_vic_bitmap;
    end else if (state_q == WAIT_PLL && pll_attempt_failed) begin
        if (pll_target_vic >= 8'd1 && pll_target_vic <= 8'd128)
            available_vic_q[pll_target_vic - 1'b1] <= 1'b0;
    end
end
```

位图索引必须先做范围保护。VIC 采用 1 至 128 的外部编号，位图下标是 0 至 127；若不检查，`VIC=0` 或超范围值会造成错误下标和仿真 X。

### 3.2 锁存事务目标

选择器输出 `selected_vic` 是握手结果，不是长期稳定的配置寄存器。管理器在 `WAIT_SELECT` 接收成功结果时锁存 `pll_target_vic`：

```systemverilog
always_ff @(posedge clk_sys or negedge rst_n) begin
    if (!rst_n || !hpd_connected) begin
        pll_target_vic <= '0;
    end else if (state_q == LOAD_CANDIDATES) begin
        pll_target_vic <= '0;
    end else if (state_q == WAIT_SELECT && mode_select_done &&
                 mode_supported && selected_vic_available) begin
        pll_target_vic <= selected_vic;
    end
end
```

之后 PLL 配置、时序 profile 和活动模式更新都使用这个锁存值。这样选择器即使在后续候选选择时改变输出，也不会篡改正在执行的配置事务。

### 3.3 计数器只服务自己的状态

PLL 超时计数和 Core 启动计数分开实现。每个计数器只有“复位”“进入相关事务时清零”“相关等待状态时推进”三类行为。计数值不会在无关状态被意外保留或修改。

这也使超时条件成为可读的纯组合信号：

```systemverilog
assign pll_attempt_failed =
    (pll_reconfig_done && (pll_reconfig_error || !pixel_pll_locked)) ||
    (!pll_reconfig_done && pll_count_q >= PLL_LIMIT - 1'b1);
```

`done` 已到达时优先依据 `error/locked` 判定；`done` 未到达时才依据计数器判定超时。两条失败路径在时序上互斥，容易验证。

---

## 4. 输出：使用已寄存的状态生成 Moore 脉冲

命令型接口都由 `state_q` 直接译码：

```systemverilog
assign edid_read_start     = state_q == ISSUE_READ;
assign mode_select_start   = state_q == ISSUE_SELECT;
assign pll_reconfig_start = state_q == ISSUE_PLL;
assign timing_config_start = state_q == ISSUE_CONFIG;
assign tmds_enable         = state_q == RUNNING;
```

`ISSUE_* -> WAIT_*` 保证每次命令产生一个完整的时钟周期脉冲。等待方只需查看 `*_start`，完成方以 `*_done` 返回，避免把请求信号保持到完成而产生重复启动。

这也是为什么这里保留了看似成对的 `ISSUE`、`WAIT` 状态：它们不是冗余状态，而是明确的、无需额外脉冲寄存器的事务边界。

---

## 5. 综合与时序层面的实际收益

这种结构不会因为 `always` 块数量增加而“自动提升频率”。综合器仍会根据寄存器和逻辑依赖生成等价硬件。实际收益是：

- 数据寄存器的使能条件局部化，便于检查和优化；
- 状态跳转的组合锥不再混入宽位图、多个计数器和 VIC 数据更新；
- 每个跨状态数据的生命周期明确，减少后续改动带来的隐式耦合；
- 仿真波形可以按“状态 / 候选位图 / 目标模式 / 计数器”分别观察；
- 更容易为具体寄存器补充断言、覆盖率或形式验证属性。

代价是时序块数增加。因此不应把同一类强相关寄存器人为拆得过碎；以“可独立说明其更新规则”为边界，比以“一个变量必须一个块”为边界更合理。

---

## 6. 验证清单

本次重构不只检查常规成功路径，还特意覆盖“上游输出变化但当前事务不可改变”的场景：

1. 选择器首先返回 VIC 16；
2. 管理器锁存 `pll_target_vic=16`，但尚未收到 `reload_reset_ack`；
3. 测试平台把选择器可见输出改为 VIC 4；
4. 管理器仍必须对 VIC 16 发起首次 PLL 配置；
5. 第一次配置失败后，候选位图只清除 VIC 16；
6. 管理器重新选择 VIC 4，配置成功并最终使能 TMDS；
7. HPD 断开后，Core 回到 reset，TMDS 关闭，会话候选位图清零。

该用例证明目标模式的所有权已从选择器输出转移到 Link Manager 的事务寄存器，而不是仅仅验证“能走通一次状态机”。

---

## 结论

对带握手、超时、降级和复位覆盖的 RTL 控制器，推荐采用以下规则：

1. 状态跳转与数据寄存器更新分离；
2. 每类状态数据只由一个时序块拥有；
3. 事务输入在接受时锁存，后续流程只用锁存结果；
4. 请求由注册状态生成单周期 Moore 脉冲；
5. 异步会话终止（本例 HPD 断开）同时覆盖状态和对应会话数据；
6. 用专门测试验证失败、超时、降级与输入扰动，而非只验证成功路径。

这套风格尤其适用于 HDMI/显示链路管理、I2C/EDID 事务编排、PLL 重配置、DMA 命令调度以及其他以 `start/done/error` 为基本协议的控制路径。
