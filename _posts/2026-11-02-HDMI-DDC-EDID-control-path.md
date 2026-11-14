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
| 2026-11-02 12:18 | `0cd4069` | 实现 512×8 `edid_memory`、同步读有效标志和 testbench | 用可推断为 Block RAM 的数组实现原始 EDID 存储，明确 parser 的一拍读延迟接口 |

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
| `edid_memory_tb` | 512 B 地址空间的 Block 0~3 边界读写、同步读一拍延迟和 `rd_valid` 相位 |

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
| `edid_memory` | 已实现并验证 | 512×8 单时钟简单双端口同步 BRAM，读端使用 `rd_en/rd_valid` |
| `edid_parser` | 骨架 | 需校验 EDID 并解析 DTD/CTA VIC/音频能力 |
| `hdmi_mode_selector` | 骨架 | 需将本地目标模式与 sink 能力求交集 |
| `hdmi_link_manager` | 骨架 | 需串联 HPD、EDID、模式选择、PLL 和 TMDS 使能 |
| `hdmi_phy_xilinx` | 骨架 | 需替换为目标板卡的差分 I/O 与约束实现 |

下一阶段优先实现 `edid_parser`：先验证基础 EDID Header、版本和 checksum，再提取 Detailed Timing Descriptor；随后支持 CTA-861 扩展块中的 Video Data Block、音频能力与首选 VIC。完成后，`hdmi_mode_selector` 和 `hdmi_link_manager` 才能依据真实显示器能力安全地释放 HDMI Core 和 TMDS PHY。

---

## 11. 模块功能、设计细节与验证重点

这一节作为当前 RTL 的实现清单。重点不是重复模块名称，而是说明每个模块负责什么、哪些行为被刻意排除，以及测试真正检查了什么。

### 11.1 `core/*`：既有 HDMI 发送核心

| 项目 | 内容 |
|---|---|
| 功能 | 在 `clk_pixel` 域接收 `rgb`，内部生成视频/控制/data island 时序，编码为 TMDS，并在 `clk_pixel_x5` 域串行化 |
| 输入约束 | 正常可见区按每个 `clk_pixel` 提供一个 RGB 像素；消隐区无需提供特殊像素值 |
| 输出 | `tmds[2:0]`、`tmds_clock`、坐标 `cx/cy` 和帧/可见区尺寸 |
| 关键细节 | `packet_picker` 调度 HDMI 辅助数据包，不负责像素流；`packet_assembler` 负责组装数据包和相关保护字段 |
| 验证重点 | 原始 `top_tb`、音频与 SPD testbench 覆盖上游核心功能；本项目没有修改其算法实现 |

### 11.2 `hpd_filter`：连接稳定性判断

| 项目 | 内容 |
|---|---|
| 功能 | 把异步 HPD 转换为单一的同步电平条件 `hpd_connected` |
| 设计 | 两级同步器；高、低电平分别采用独立的连续周期阈值；反向电平立即清零计数 |
| 默认值 | 100 MHz 下高电平 10 ms 建立连接，低电平 1 ms 判定断开 |
| 接口取舍 | 删除 `hpd_rise/hpd_fall` 脉冲，避免下游漏采样并减少不必要连线 |
| 验证重点 | 短高脉冲拒绝、稳定高连接、短低脉冲拒绝、稳定低断开 |

### 11.3 `ddc_i2c_master`：DDC 位级与字节级引擎

| 项目 | 内容 |
|---|---|
| 功能 | 将字节命令转换为 DDC/I2C 的 SDA/SCL 波形 |
| 命令 | START、STOP、WRITE_BYTE、READ_BYTE_ACK、READ_BYTE_NAK、BUS_RECOVERY |
| 接口 | `cmd_valid/cmd_ready` 接收一条命令；`cmd_done` 表示完成；读操作用 `rx_valid/rx_data` 返回数据；写操作用 `ack_received` 返回 ACK 状态 |
| 电气约束 | SDA/SCL 只允许输出 `0` 或 `Z`，高电平由板级上拉提供；不可主动驱动 `1` |
| 健壮性 | 释放 SCL 后读取实际线路电平；支持 clock stretching、超时错误和 9 时钟恢复 |
| 验证重点 | START/STOP、写 ACK/NACK、重复 START、读操作的 ACK/NACK、有限延展、延展超时、恢复脉冲 |

### 11.4 `edid_reader`：EDID 事务与线性字节搬运

| 项目 | 内容 |
|---|---|
| 功能 | 发起 EDID 地址/偏移/重复 START/读数据/STOP 事务，并将每个返回字节写入 EDID RAM |
| 分层边界 | 不直接控制 SDA/SCL；不解释 VIC、DTD 或音频字段；这些分别由 `ddc_i2c_master` 和后续 `edid_parser` 负责 |
| 控制结构 | 5 个主状态 `IDLE/ISSUE/WAIT/COMPLETE/FAIL`，配合 `STEP_*` 枚举选择当前 DDC 命令 |
| 读取长度 | `MAX_EDID_BYTES` 当前限制为 1~256；先读基础块，在 `EDID[126]` 指示扩展块后再读取至配置上限 |
| 异常处理 | 地址 NACK、读命令错误或 HPD 掉线会中止正常步骤，并尝试发送 STOP |
| 验证重点 | 有扩展块时读取 256 B、无扩展块时读取 128 B、字节写地址/数据顺序、地址 NACK 异常退出 |

### 11.5 `edid_memory`：512×8 Block RAM 存储

| 项目 | 内容 |
|---|---|
| 功能 | 保存原始 EDID 字节，并向 parser 提供同步读端口 |
| 实现 | `logic [7:0] memory [0:511]` 数组，带 `(* ram_style = "block" *)` 属性，目标为 Xilinx 单时钟简单双端口 BRAM 推断 |
| 写端 | `wr_en/wr_addr/wr_data`，由 `edid_reader` 在 `clk_sys` 域写入 |
| 读端 | `rd_en/rd_addr` 请求；下一拍 `rd_valid=1` 且 `rd_data` 有效 |
| 复位策略 | 不复位 RAM 数组；HPD/读取状态有效性由上游逻辑管理，避免破坏 BRAM 推断 |
| 同址竞争 | 当前流程要求 reader 完成后 parser 才开始，因此不依赖 read-first/write-first/no-change 的器件相关语义 |
| 验证重点 | `0x000`、`0x07F`、`0x080`、`0x100`、`0x1FF` 地址读写；一拍读延迟和 `rd_valid` 相位 |

#### 512 B 地址边界与未来 E-DDC 溢出保护

RAM 端口是 9 bit，因此合法范围固定为：

```text
0x000 ~ 0x1FF
```

当前 testbench 验证了 `0x1FF` 最高合法地址，但无法在 RAM 模块内检测 `0x200`：第 10 位会在进入 9 bit 端口前丢失，最终表现为访问 `0x000`。当前 `edid_reader` 最大只写 256 B，即 `0x000~0x0FF`，不会触发该风险。

未来加入 E-DDC Segment Pointer、读取超过 256 B 时，地址生成器必须先使用更宽的逻辑地址比较：

```systemverilog
logic [9:0] logical_byte_index;

if (logical_byte_index < 10'd512)
    memory_wr_addr = logical_byte_index[8:0];
else
    read_error = 1'b1;
```

届时必须补充两项测试：`0x1FF` 可读写，`0x200` 被拒绝且不得覆盖 `0x000`。

### 11.6 尚未实现模块的设计前提

| 模块 | 进入实现前必须遵守的前提 |
|---|---|
| `edid_parser` | 必须按 `rd_en` 发地址、等待一拍 `rd_valid`，不能假定组合读；仅在 EDID 读取成功后运行 |
| `hdmi_mode_selector` | 必须以 parser 输出的 sink 能力为依据，并保留本地目标模式不可用时的失败/回退策略 |
| `hdmi_link_manager` | 必须在 HPD 掉线时取消 DDC/解析流程、保持 HDMI Core reset、关闭 TMDS PHY |
| `hdmi_phy_xilinx` | 必须由具体 FPGA、I/O Bank 电压和板级 HDMI 电路确定 OBUFDS/约束，不能将通用占位逻辑直接用于量产硬件 |

---

## 12. 2026-11-02：EDID Parser 完成第一版

`edid_parser` 已从接口骨架替换为同步 RAM 读取和能力解码实现。设计保持控制、存储器命令、EDID/CTA 字节解码三个组合逻辑块独立，并由单个 `always_ff` 保存状态和结果寄存器；避免把完整解析流程堆入一个时序块。

本版本的输入约束与输出语义如下：

- Parser 使用 `rd_en/rd_addr` 发起一次 BRAM 读取，并只在下一拍 `rd_valid` 有效时消耗 `rd_data`；因此不依赖 RAM 的组合读实现。
- `edid_reader` 额外输出 `edid_byte_count`。Parser 在收到少于 128 B 的基础块、或声明有扩展块却不足 256 B 时完成并置 `parse_error`，不会把旧 RAM 内容误解为有效 EDID。
- 校验基础块八字节 Header 和基础块/首个扩展块的 8 bit checksum；`done` 表示解析结束，`edid_valid` 与 `parse_error` 表示结果，二者不会因错误路径而让下游永久等待。
- 当首个扩展块为 CTA (`0x02`) 时，解析 Video Data Block，生成 128 bit VIC 位图，并以 native SVD 优先、首个 SVD 回退的规则给出 `preferred_vic`。
- 解析 Audio Data Block 中 LPCM、至少双声道的 SAD，输出 `lpcm_2ch_supported` 和 CTA 定义的 7 bit 采样率掩码。当前版本不从 DTD 反推 VIC，也不处理第二个及其后的扩展块；这些是后续扩展点，而非静默错误。

验证新增 `edid_parser_tb`：构造一个 Header/checksum 合法的 256 B EDID，包含 native VIC 4、VIC 16 和 LPCM 2ch 44.1/48 kHz CTA 数据块，检查全部并行输出；随后篡改 Header，确认模块拒绝数据并报告 `parse_error`。同时扩展 `edid_reader_tb`，验证成功读取时 `edid_byte_count` 分别为 256 和 128。

---

## 13. 2026-11-02：Link Manager 会话控制与 PLL 降级

`hdmi_link_manager` 已实现为 `clk_sys` 域的两段式会话状态机。它依次发起 EDID 读取、解析、候选模式装载、模式选择、PLL 重配置、核心启动和 TMDS 使能；HPD 失效在任意状态均覆盖正常流程，立即关闭 TMDS、保持核心复位并清空会话状态。

候选模式使用会话级 `available_vic_bitmap`。在 Parser 成功后装载为 `LOCAL_VIC_BITMAP & supported_vic_bitmap`；PLL 配置错误、锁定失败或超时会清除当前 `selected_vic` 对应 bit 并重新选择。该失败记录只在本次 HPD 会话有效，重新插拔并完成新的 EDID 解析后自动恢复。Manager 向未来 PLL 模块提供 `pll_reconfig_start/pll_target_vic`，并等待 `pll_reconfig_done/pll_reconfig_error/pixel_pll_locked`，不再把单独的 `locked` 电平误当成一次配置完成。

新增 `hdmi_link_manager_tb` 覆盖：VIC 16 首先被选择但 PLL 失败、其 bit 被清除、自动降级至 VIC 4 并进入 TMDS 输出；随后 HPD 失效，验证核心复位、TMDS 关闭和候选 bitmap 清零。ModelSim 编译全工程无 error（仅保留既有 core 的 SVCHK warning）。
