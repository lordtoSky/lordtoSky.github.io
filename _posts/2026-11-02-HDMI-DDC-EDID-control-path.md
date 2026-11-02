---
layout: post
title: "HDMI_20261101 项目日志：从原始 TMDS 发送到显示器发现"
date: "2026-11-02 11:00:00"
description: "HDMI_20261101 从项目创建到 HPD、DDC、EDID 控制路径的完整设计与变更记录"
tags: [HDMI, FPGA, SystemVerilog, TMDS, DDC, I2C, EDID]
---

## 1. 项目起点、目标与范围

`HDMI_20261101` 是从上游 [hdl-util/hdmi](https://github.com/hdl-util/hdmi) 的 SystemVerilog HDMI 发送实现独立出来的开发仓库。原始核心已经能把像素、音频和 HDMI 辅助数据组织为 TMDS 串行比特流，但并不处理显示器是否连接、显示器支持什么模式、以及 DDC/EDID 读取。

本项目的目标不是重写 TMDS 编码器，而是在保留既有 HDMI Core 的基础上，补齐一个实际显示链路需要的控制路径：

```text
检测显示器连接
        ↓
读取显示器 EDID
        ↓
解析显示器能力
        ↓
选择可用视频模式
        ↓
等待像素 PLL 稳定
        ↓
启动既有 HDMI/TMDS 发送核心
```

当前仓库地址为 `https://github.com/lordtoSky/HDMI_20261101`。项目创建后所有改动均在该独立仓库进行，不修改原始 `HDMI_mod`。

---

## 2. 原始 HDMI Core：项目开始时已经具备什么

初始导入的核心实现 HDMI 1.4b 发送端最关键的实时数据路径：视频时序、TMDS 编码、HDMI data island、音频相关数据包和串行化。

### 2.1 图像输入不是 AXI-Stream

核心的像素接口是同步并行接口：

```systemverilog
input  logic              clk_pixel;
input  logic [23:0]       rgb;
output logic [..:0]       cx;
output logic [..:0]       cy;
```

正常显示区内，用户在每个 `clk_pixel` 周期提供一个 24 bit RGB 像素。`cx/cy` 由 HDMI Core 产生，用于标识当前像素坐标；它们不是外部输入，也不是 IP 返回的 AXI-Stream sideband。

```text
clk_pixel 上升沿
   ↓
HDMI Core 更新 cx/cy
   ↓
用户逻辑根据上一拍/当前拍约定生成 rgb
   ↓
HDMI Core 在像素时钟域采样 rgb
```

消隐区、同步区和 data island 的控制由 HDMI Core 内部根据 VIC 时序生成。用户无需在消隐区向 `rgb` 传入特殊值；此时 `rgb` 对 TMDS 视频数据没有实际作用。用户可以保持旧值或写零，通常写零便于波形观察。

### 2.2 原始视频/音频/TMDS 数据路径

```text
rgb + cx/cy + 时序参数
          ↓
     HDMI video period
          ↓
  TMDS channel encoder × 3
          ↓
packet_picker
          ↓
packet_assembler
          ↓
serializer @ clk_pixel_x5
          ↓
tmds[2:0] + tmds_clock
```

`packet_picker` 的职责不是组织像素流，而是在 data island 时段选择当前应该发送的 HDMI 数据包，例如 AVI InfoFrame、SPD InfoFrame、Audio Clock Regeneration、Audio InfoFrame、Audio Sample Packet 或 Null Packet。`packet_assembler` 再负责形成带 BCH/ECC 等字段的发送单元。

`clk_pixel_x5` 是像素时钟的 5 倍，用于 DDR 串行化；因此等效串行速率为像素时钟的 10 倍。顶层需要自行通过 PLL/MMCM 提供 `clk_pixel`、`clk_pixel_x5`，以及音频时钟 `clk_audio`。

### 2.3 核心与 HDMI 物理链路的边界

原始 `hdmi.sv` 输出的是 FPGA 内部的单端 TMDS 串行逻辑信号，不直接等价于 HDMI 接口引脚。最终仍需目标 FPGA 专用差分输出封装：

```text
hdmi.sv
  → tmds_serial / tmds_clock_serial
  → hdmi_phy_xilinx
  → OBUFDS / FPGA 差分 I/O
  → HDMI Data[2:0] / Clock 差分对
```

当前 `hdmi_phy_xilinx` 仍是安全的占位模块：在链路未真正就绪时保持物理输出关闭。具体 OBUFDS、管脚约束、TMDS/LVDS 电气标准与板级 AC 耦合策略必须按目标 FPGA/开发板确定。

---

## 3. 完整变更时间线

以下时间线按 Git 历史顺序记录截至 2026-11-02 的全部项目提交。

| 时间 | 提交 | 变更 | 原因与影响 |
|---|---|---|---|
| 2026-11-01 15:16 | `319a8d9` | 创建独立仓库；导入上游 HDMI Core、原始顶层、Manifest、README、已有音频/顶层仿真和隐式状态机图资产 | 建立可运行的基线，并保留 MIT/Apache-2.0 许可与上游归属 |
| 2026-11-01 15:30 | `b900e8b` | 将原始核心移动到 `src/core/`；建立 `control/`、`ddc/`、`phy/` 层；新增 `hdmi_system_top.sv` 和安全占位模块 | 先锁定工程边界与顶层接口，避免在既有核心中直接插入 DDC/EDID 控制逻辑 |
| 2026-11-01 15:45 | `90dfca3` | 实现可配置 `hpd_filter`，新增定向 testbench；修正原测试工作流中的音频时钟路径 | 先让后续 DDC 读取拥有可靠的“显示器已稳定连接”条件 |
| 2026-11-01 15:47 | `9d15fe9` | 升级 GitHub Actions 的 `checkout`、`setup-python`、`cache` 版本 | 修复 `actions/cache@v2` 已废弃导致的 CI 失败 |
| 2026-11-01 15:50 | `8726156` | 删除 GitHub Actions 仿真工作流，并将 `.github/workflows/` 加入 `.gitignore` | 项目策略改为只上传代码和测试文件，不在 GitHub 自动下载 ModelSim 或运行仿真 |
| 2026-11-01 16:18 | `88beafb` | 实现 `ddc_i2c_master` 和自检查 testbench | 提供可复用的 DDC/I2C 字节命令引擎，隔离 SDA/SCL 微时序 |
| 2026-11-02 10:42 | `70e7853` | 实现可配置 `edid_reader` 和 testbench；顶层暴露 `MAX_EDID_BYTES` | 将 EDID 事务、字节计数、扩展块判断与 I2C 位时序分离 |
| 2026-11-02 10:57 | `88bf32e` | 将 `edid_reader` 拆分为命令译码、控制状态和数据路径 | 避免一个过大的组合块同时承担所有职责，便于后续时序收敛和维护 |

---

## 4. 目录结构演进

初始上游工程中，大部分 RTL 都直接位于 `src/`。随着控制路径加入，工程被整理为：

```text
src/
├── core/       # 原始 HDMI 发送核心：TMDS、包选择、包组装、串行化
├── control/    # HPD、链路管理、模式选择
├── ddc/        # DDC I2C、EDID读取、EDID存储和解析
├── phy/        # FPGA相关差分输出封装
└── hdmi_system_top.sv
```

这不是为了把文件机械分目录，而是定义稳定的抽象边界：

```text
core    : 生成 HDMI 协议和串行数据
control : 决定什么时候允许 core 工作
ddc     : 获取显示器能力
phy     : 将内部串行数据连接到实际 HDMI 电气接口
```

---

## 5. HPD：从异步插拔信号到稳定连接条件

### 5.1 问题

HPD 是显示器侧产生的异步信号。它可能因插拔、电平建立或线缆接触而短暂抖动，不能直接作为 DDC 或 TMDS 使能条件。

### 5.2 实现

`hpd_filter` 使用两级同步器，并分别统计连续高、低电平：

```text
连续高 >= HIGH_STABLE_CYCLES  → hpd_connected = 1
连续低 >= LOW_STABLE_CYCLES   → hpd_connected = 0
中途反向                       → 当前计数清零
```

默认在 100 MHz `clk_sys` 下：

| 参数 | 默认值 | 含义 |
|---|---:|---|
| `HPD_HIGH_STABLE_CYCLES` | 1,000,000 | 高电平持续 10 ms 后认为已连接 |
| `HPD_LOW_STABLE_CYCLES` | 100,000 | 低电平持续 1 ms 后认为已断开 |

接口最终只保留 `hpd_connected`，没有单周期 `hpd_rise/hpd_fall`。

原因是下游需要的是条件而不是事件：

```text
hpd_connected == 1  → 可以开始 DDC
hpd_connected == 0  → 立即停止正在进行的链路流程
```

单周期脉冲会增加布线，而且可能被复位、忙碌或跨时钟的下游模块漏采样。

---

## 6. DDC I2C Master：把物理时序封装成字节命令

DDC 使用 I2C 风格的 SDA/SCL 总线。`ddc_i2c_master` 是唯一直接操作这两根线的模块。

### 6.1 上层命令接口

```text
edid_reader
   │ cmd_valid / cmd / tx_data
   ▼
ddc_i2c_master
   │ cmd_done / ack_received / rx_valid / rx_data / error
   ▼
edid_reader
```

已实现的命令：

```text
START
STOP
WRITE_BYTE
READ_BYTE_ACK
READ_BYTE_NAK
BUS_RECOVERY
```

这是逐命令握手接口，不是 AXI-Stream。上层发出一条命令后必须等待 `cmd_done`，再继续下一条命令。

### 6.2 位级时序和开漏输出

该模块内部使用细粒度状态机产生 I2C 标准模式时序：SCL 低电平设置数据、释放 SCL、等待实际 SCL 变高、维持高电平并采样数据。相比 `edid_reader`，这里的细状态是必要的，因为它直接定义微秒级 SDA/SCL 波形。

SDA/SCL 均按开漏方式工作：

```systemverilog
assign ddc_scl = scl_drive_low ? 1'b0 : 1'bz;
assign ddc_sda = sda_drive_low ? 1'b0 : 1'bz;
```

模块只能拉低或释放，不会主动驱动高电平。板级设计仍需确认 DDC 上拉电压、双向电平转换和 FPGA 引脚容限。

### 6.3 健壮性措施

- SCL 释放后读取实际线路电平；
- 支持从机 clock stretching；
- SCL 长时间为低时产生超时错误；
- 支持发送 9 个 SCL 脉冲进行总线恢复；
- START、STOP、读写和 ACK/NACK 均有定向测试。

---

## 7. EDID Reader：事务编排、字节计数和存储写入

`edid_reader` 不直接碰 SDA/SCL，也不解析显示器模式。它只负责按 EDID 协议组织命令，并把返回字节搬运到 `edid_memory`：

```text
START
  → WRITE 0xA0        # EDID 设备地址，写
  → WRITE 0x00        # EDID 内部偏移
  → REPEATED START
  → WRITE 0xA1        # EDID 设备地址，读
  → READ byte 0 ... byte N
  → STOP
```

### 7.1 可配置读取上限

顶层暴露：

```systemverilog
parameter int unsigned MAX_EDID_BYTES = 256;
```

当前支持 1 到 256 字节：

1. 首先读取基础 EDID 块，默认目标是 128 字节。
2. `EDID[126]` 是扩展块数量。
3. 若 `EDID[126] != 0` 且 `MAX_EDID_BYTES > 128`，继续读取到配置上限。
4. 最后一个字节使用 `READ_BYTE_NAK`，然后发送 STOP。

这样，无扩展块的显示器在第 128 字节后停止；有扩展块时默认读取首个扩展块。超过 256 字节需要 E-DDC Segment Pointer（地址 `0x30`），本版尚未实现。

### 7.2 为什么压缩状态机

初版按每条命令展开为 `ISSUE_x → WAIT_x`，便于最初调试，但事务层会因此出现不必要的重复。现版本改为：

```text
主状态：IDLE → ISSUE → WAIT → COMPLETE / FAIL

事务步骤：
START → DEVICE_WRITE → OFFSET → RESTART
      → DEVICE_READ → READ（循环）→ STOP
```

`STEP_*` 选择当前 DDC 命令；`STATE_ISSUE/STATE_WAIT` 对所有命令复用。字节循环仅由 `byte_count` 推进，不会为每一个字节再增加状态。

### 7.3 控制与数据路径拆分

当前 `edid_reader` 的组织方式：

```text
always_ff   : 状态、步骤、计数器和寄存器输出
always_comb : STEP → I2C 命令译码
always_comb : 握手、状态转移、错误与 HPD 中断
always_comb : EDID 数据写入、字节计数、扩展块判断
```

这种拆分避免单个大型组合块同时完成命令译码、状态控制和数据写入。综合器会优化组合逻辑，因此“拆成多个 always 块”本身并不会神奇地减少 FPGA 布线；它的直接价值是减小逻辑耦合，并在需要时为接口寄存器或流水化留下明确边界。

---

## 8. 当前系统顶层与隐式状态机

`hdmi_system_top.sv` 已将以下模块连通：

```text
hdmi_hpd → hpd_filter → display_connected
                        ↓
                  edid_reader ↔ ddc_i2c_master ↔ HDMI DDC pins
                        ↓
                    edid_memory

现有 HDMI core → hdmi_phy_xilinx → HDMI 差分输出
```

但完整链路管理还未开启。当前安全默认行为是：

```text
HDMI core 保持 reset
TMDS PHY 保持关闭/高阻
```

原始 HDMI Core 的内部“隐式状态机”图、PCIe 风格重绘图、SVG/PNG/VSDX 和生成脚本均在 `diagrams/` 中保留。它们描述的是视频期、控制期、前导码和 data island 的发送切换；新控制链路则负责决定这个核心何时可以离开 reset。

---

## 9. 验证历史

项目保留本地 ModelSim 定向仿真，不再使用 GitHub Actions 自动安装 ModelSim。

| Testbench | 覆盖内容 |
|---|---|
| 原始 `top_tb` / `audio_*_tb` / `spd_tb` | 既有 HDMI Core、音频参数、信息包等上游功能 |
| `hpd_filter_tb` | 高/低去抖、短脉冲拒绝、稳定连接和稳定断开 |
| `ddc_i2c_master_tb` | START/STOP、写 ACK/NACK、重复 START、读 ACK/NACK、clock stretching、超时、9 时钟恢复 |
| `edid_reader_tb` | 有扩展块时读取 256 字节、无扩展块时读取 128 字节、内存地址/数据顺序、地址 NACK 异常退出 |

近期验证结果：

- 三个新增模块的自检查 testbench 均通过；
- 全工程 SystemVerilog/ModelSim 编译为 0 error；
- 轻量 lint 为 0 error。该脚本对 SystemVerilog `enum` 和嵌套 `case/default` 有已知误报，最终以 ModelSim 实际编译/仿真结果为准。

---

## 10. 当前状态与尚未完成的工作

| 模块 | 状态 | 说明 |
|---|---|---|
| `core/*` | 已有实现 | 上游 HDMI 视频、音频、TMDS 和串行化核心 |
| `hpd_filter` | 已实现并验证 | 异步同步与非对称高低去抖 |
| `ddc_i2c_master` | 已实现并验证 | 100 kHz 参数化字节命令 I2C/DDC 引擎 |
| `edid_reader` | 已实现并验证 | 基础块与首个扩展块的可配置读取 |
| `edid_memory` | 骨架 | 需最终确定存储实现和读延迟语义 |
| `edid_parser` | 骨架 | 需校验 EDID 并解析 DTD/CTA VIC/音频能力 |
| `hdmi_mode_selector` | 骨架 | 需将本地目标模式与 sink 能力求交集 |
| `hdmi_link_manager` | 骨架 | 需串联 HPD、EDID、模式选择、PLL 和 TMDS 使能 |
| `hdmi_phy_xilinx` | 骨架 | 需替换为目标板卡的差分 I/O 与约束实现 |

下一阶段优先实现 `edid_parser`：先验证基础 EDID Header、版本和 checksum，再提取 Detailed Timing Descriptor；随后支持 CTA-861 扩展块中的 Video Data Block、音频能力与首选 VIC。完成后，`hdmi_mode_selector` 和 `hdmi_link_manager` 才能依据真实显示器能力安全地释放 HDMI Core 和 TMDS PHY。
