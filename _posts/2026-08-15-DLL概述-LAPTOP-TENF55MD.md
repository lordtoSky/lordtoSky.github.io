# DLL

DLL（Data Link Layer，数据链路层）位于事务层（Transaction Layer）和物理层（Physical Layer）之间，是 PCIe 分层架构中负责可靠链路传输的一层。它不关心事务请求的具体语义，也不直接处理电气信号，而是将事务层产生的 TLP（Transaction Layer Packet）可靠地交付给对端的数据链路层。

![PCIe 数据链路层分层示意图](/assets/images/PCIE/pcie-dll-layering-diagram.png)

*图：PCIe 分层结构中数据链路层的位置。虚线可理解为每个端口内部的 RX/TX 边界；数据通过物理层在两个端口之间传输，而 DLL 在本端事务层与物理层之间完成可靠交付。图中的 ①至④表示两个方向上 TLP 在事务层与 DLL 之间的上下行路径。*

## DLL 的功能和职责

- **可靠交付**：在传统 Non-Flit 传输中，DLL 为 TLP 编号、保存尚未确认的发送副本，并利用接收序号检测缺失或重复的 TLP。它解决的是单条链路上的瞬态传输错误，不改变 TLP 的事务语义。
- **确认与重放**：接收端以 ACK/NAK DLLP（Data Link Layer Packet）确认接收结果。发送端仅在收到 ACK 后释放对应的重放缓冲区；收到 NAK 或重放计时器到期时，从要求的位置重新发送。
- **数据完整性保护**：传统 Non-Flit 模式下，DLL 为传输的 TLP 生成 LCRC（Link CRC），接收端先校验 LCRC，再决定确认、拒绝或交付。LCRC 保护的是一跳链路上的传输内容，不应与端到端保护用的 ECRC 混为一谈。
- **信用式流量控制**：接收端通过 DLLP 公告可用缓冲空间，发送端按已获信用发送 Posted、Non-Posted 和 Completion 三类 TLP 的 Header/Data 内容，防止接收端缓冲溢出。
- **链路与电源管理报文**：DLLP 除 ACK/NAK 和流控信息外，也承载与链路状态、电源管理及厂商特定功能相关的链路级消息。
- **层间边界**：向下交给物理层的是可在该链路发送的编码单元；向上只交付已通过链路级检查的 TLP。因此，事务层不需要为普通瞬态链路错误自行实现重传。

> DLL 的可靠性范围仅限于一跳 PCIe 链路。TLP 每经过一个 PCIe Switch 端口，都会在该链路上重新进行序列号、LCRC、ACK/NAK 与重放处理。

## DLL 状态机

DLL 并非在链路上电后立即允许事务流量通过。它遵循数据链路控制与管理状态机（Data Link Control and Management State Machine），依次完成可选功能协商与流控初始化；只有进入 `DL_Active` 后，链路才处于可正常传输 TLP/DLLP 的工作状态。

![Data Link Control and Management State Machine](/assets/images/PCIE/pcie-dll-control-management-state-machine.png)

*图：数据链路控制与管理状态机。图中的回退路径表示链路不再满足数据链路工作条件时，DLL 需要退出当前初始化或活动阶段，并返回非活动状态重新建立。*

> DL_Inactive
>    ↓
> DL_Feature
>    │
>    └─ Data Link Feature DLLP
>    ↓
> DL_Init
>    │
>    ├─ InitFC1 DLLP
>    └─ InitFC2 DLLP
>    ↓
> DL_Active
>    │
>    ├─ UpdateFC DLLP
>    ├─ ACK / NAK DLLP
>    └─ PM DLLP

### DL_Inactive

`DL_Inactive` 是 Reset 后的初始或非活动状态。此时 DLL 不提供已建立的数据链路服务，不能进行正常的事务传输。链路需要先满足物理层和链路状态机的前提条件，才能进入后续的数据链路建立流程。

rules：

- 作为状态机中的初始化状态，一般伴随着pcie hot、warm及cold reset，但并不会收FLR的影响

| 类型 | 是否断电 | 常见触发方式 | 影响 |
| --- | --- | --- | --- |
| **Cold Reset**（冷复位） | 是 | 上电、断电后重新供电、热插拔重新上电 | 最彻底；设备、链路和配置状态从上电初始条件重新建立 |
| **Warm Reset**（温复位） | 否 | `PERST#` 等平台复位信号 | 不移除设备电源，但设备需重新初始化，PCIe 链路重新训练 |
| **Hot Reset**（热复位） | 否 | 已建立链路上的带 Hot Reset 标志 TS1 Ordered Set | 带内重置一条下游 PCIe 链路；不需要拉低 `PERST#` 或重新供电 |

>**question：为什么DLL不会因为FLR进入DL_Inactive？**
>
>主要原因是FLR本质上是为了复位function，一个设备可以有多个function。如果一个function的逻辑复位会导致DLL进入inactive状态，那么整个DLL负责的link都会被重置，重新进入训练对齐的初始化步骤。很明显，这会导致其余function也被迫进入重置状态，这是违背了function的设计初衷的。

- 进入DL_Activate状态后，会将所有dll状态信息重置为默认值；若端口支持可选的Data Link Feature Exchange（DLFE），则清除Remote Data Link Feature Supported字段和Remote Data Link Feature Supported Valid位；同时将retry buffer清空。
- 在DL_Activate状态时，该端口的数据链路层会恢复到链路初始化前的状态
  - 会向事务层报告当前处于DL_DOWN状态，同时也会对其他DLL部分报告。这会使事务层丢弃未完成的事务，并在内部终止发送TLP的尝试。
  - 会将TLP数据从TL和PL中移除，恢复至默认值
  - 不再接收或生成DLLP，也即该端口从链路交互中移除了，链路不可达

>**question：如果switch进入DL_Inactive状态，对上流和下流分别产生什么影响？**
>
>对于上流端口（upstream port），Link进入DL_Down按照复位处理，等价于hot reset；如果该端口属于switch，switch还会向其关联的Downstream Port传播hot reset。对于下流端口（downstream port），Link进入DL_Down等价于其下游设备或子树被hot-remove。
>但要注意，对于switch而言，存在多个Downstream port，每个dsp都是独立的。若仅某个dsp自身的Link进入DL_Down，其他Downstream Port不会因此进入hot reset；但如果switch的Upstream Port进入DL_Down，则会向关联的Downstream Port传播hot reset

- 退出DL_Inactive状态并进入DL_Feature状态需要满足以下所有条件：
  - 端口支持DLFE协议
  - 若端口实现Data Link Feature Extended Capability，其Data Link Feature Exchange Enable位需为Set；若未实现该Capability，则不需要检查该位
  - 事务层指示该Link未被软件禁用，即PCIe Capability中的Link Control.Link Disable位未被Set
  - 物理层报告Physical LinkUp = 1b：意味着物理链路已建立，但此时DLFE和流控初始化尚未完成

> **notes：Data Link Feature Extended Capability**
>
> Data Link Feature Extended Capability位于PCIe Extended Configuration Space中，用于描述本地端口支持的Data Link Feature、保存从对端获取的Feature信息，并为软件提供DLFE的使能开关。支持16.0 GT/s及更高速率的Port必须支持DLFE协议；其他Port可选支持。实现DLFE的Downstream Port必须实现该Capability，而Upstream Port允许支持DLFE协议但不实现该Capability。
>
> - Data Link Feature Capabilities Register（Offset 04h）
>   - Local Data Link Feature Supported：表示本地Port支持的Data Link Feature。
>   - Data Link Feature Exchange Enable：软件可写的DLFE使能位。Set时允许DLCMSM进入DL_Feature；Clear时跳过DL_Feature并进入DL_Init。
> - Data Link Feature Status Register（Offset 08h）
>   - Remote Data Link Feature Supported：保存通过Data Link Feature DLLP获得的对端Feature支持信息。
>   - Remote Data Link Feature Supported Valid：表示Remote Data Link Feature Supported字段已经包含有效数据。
>
> 软件通过扫描PCIe Extended Capability链表找到该Capability，然后设置或清除Data Link Feature Exchange Enable位来控制DLFE。该位在Link从DL_Inactive离开时决定是否进入DL_Feature，不会在Link已经处于DL_Active时立即发起新的Feature Exchange。如果Upstream Port支持DLFE但未实现该Capability，则没有Enable位可供软件禁用，在其他转换条件满足时仍会进入DL_Feature。

- 退出DL_Inactive状态并直接进入DL_Init状态，需要满足以下两组条件之一，共同点是端口的DLFE功能无效：
  - 端口不支持可选的DLFE协议、事务层指示Link未被软件禁用，并且物理层报告Physical LinkUp = 1b
  - 端口支持DLFE协议，但Data Link Feature Exchange Enable位为Clear，同时事务层指示Link未被软件禁用，并且物理层报告Physical LinkUp = 1b

> **question: 为什么从DL_Inactive直接进入DL_Init需要DLFE无效？**
>
> 首要原因是DL_Feature是专门用来处理feature交换的状态，如果端口支持Feature Exchange，需要首先进入DL_Feature再进入DL_Init。只有Feature Exchange不支持或禁用的情况下才会从DL_Inactive直接进入DL_Init。
> 由此带来的一个新问题：
>
> **question：如果使能了DLFE但从DL_Inactive直接进入DL_Init会发生什么**
>
> 这就需要从DL_Feature本身的职责来出发思考。DL_Feature是为链路两个节点之间确认支持的DL扩展功能有哪些而存在的。如果双方不协商，直接采用自身支持的特性，对端可能存在不支持该功能的情况，直接导致的结果就是:
>
> - 对端忽略不认识的字段或 DLLP，功能实际失效。
> - 双方对同一字段产生不同解释，引发协议错误。
> - 流控、确认或状态机无法推进，链路卡在初始化阶段。
> - 触发 Data Link Protocol Error、Replay、Recovery 或重新训练。
> - 严重时链路反复训练，始终无法进入 DL_Active。

### DL_Feature

`DL_Feature` 用于交换和处理 Data Link Feature DLLP，以完成适用的数据链路功能协商。并非所有链路都会在此状态长时间停留；若没有需要协商的功能，状态机会按规范条件快速推进至 `DL_Init`。在该阶段，普通 TLP 事务传输仍不可用。

rules：

- 处于DL_Feature状态时：
  - 按照Data Link Feature Exchange协议执行链路特性交换。
  - 向事务层及数据链路层的其他部分报告DL_Down状态。
  - 处于DL_Down状态的Port，其Data Link Layer允许丢弃任何收到的TLP，前提是未通过发送一个或多个Ack DLLP对这些TLP进行确认。

> **question：链路特性交换包含哪些内容？**
>
> - 本端支持的特性：发送己端特性
> - 对端支持的特性：接收对端特性后保存
> - 接收有效标志：成功记录对端特性后，设置标志位，表示对端特性信息已确认
> - 接受确认（握手）：通过Feature Ack确认对端接收到己端特性信息
> - 激活特性：只有双方都声明支持的特性才会被激活

![Data Link Feature Exchange数据流图](/assets/images/PCIE/pcie-data-link-feature-exchange-flow.svg)

*图：双方通过Data Link Feature DLLP交换本地能力，记录对端能力并置位Remote Valid，再以Feature Ack完成确认。*

> **question：两端谁先发送己端特性？**
>
> 这个问题很有意思，如果是从TCP的角度出发，握手必须是由cliet发起的。但在PCIE这里，两个端点的DL状态机是独立的，因此两端分别在各自DL进入DL_Feature时通过DLLP传输自己的Feature信息。因此谁先发送取决于两端的DL状态机谁先进入DL_Feature。
>
> 但这个问题可以衍生出下一个问题：
>
> **question：有端口a和b进入链路初始化，如果a不支持DLFE，直接从Inactive进入Init状态。而b支持DLFE，在Feature等待a的Feature数据。但a明显不会发送Feature DLLP，这是否会导致死锁，协议是如何解决的？**
>
> 这个问题的核心在于b如何知道a不支持DLFE，所以问题的核心就是a如何告诉b它不支持DLFE且进入了Init。协议的解决方法很简单，a进入Init后通过initFC1信息告诉b它不支持DLFE且已经进入Init，这样子就解决了死锁问题。

> **question：这一阶段会交换哪些Feature？**
>
> | Feature 类别| 用途|
> | ---------------------------------| ----------------------------------------------------------|
> | **Scaled Flow Control Supported**| 表示本端是否支持扩展的 Flow Control Credit 编码范围，用于高带宽链路提高可用 Credit 数量|
> | **Reserved Feature Bits**| 预留给未来 Data Link Layer 新特性扩展，目前没有实际功能定义|
> | **Feature Ack**| 不是 Feature 本身，而是握手状态，表示“我已经收到你的 Feature Supported 信息”|
> 
> 可以看出来，DL_Feature的核心目标是确认链路流控信息，主要检查流控扩展能力

- 满足以下任一条件时，退出DL_Feature并进入DL_Init：
  - Data Link Feature Exchange成功完成，且物理层持续报告Physical LinkUp = 1b。
  - Data Link Feature Exchange确定对端Data Link Layer不支持可选的Data Link Feature Exchange协议，且物理层持续报告Physical LinkUp = 1b。

- 若物理层报告Physical LinkUp = 0b，则终止Data Link Feature Exchange协议，退出DL_Feature并返回DL_Inactive。

### DL_Init

`DL_Init` 用于建立数据链路的运行条件，重点是双方流控信息的初始化。该状态的关键产出是：双方都拥有可信的接收缓冲信用视图。在此之前，即使物理链路已经建立，也不能按正常运行方式发送事务流量。

### DL_Active

`DL_Active` 表示数据链路已可用。此时可以正常传输 TLP 和 DLLP，TLP 的可靠交付、ACK/NAK、Replay Buffer 重放以及运行期流控更新均在该状态下工作。

图中从 `DL_Feature`、`DL_Init` 和 `DL_Active` 返回 `DL_Inactive` 的弧线尤其重要：它说明 DLL 的“可用”依赖于底层链路状态。链路训练重启、复位或其他使数据链路条件失效的事件发生时，原有的确认、重放和信用状态不能继续沿用，必须重新建立。

## 传统 Non-Flit 模式的数据路径

以下过程描述传统 TLP/DLLP 传输；它是理解 DLL 重放机制最直接的模型。

1. **事务层提交 TLP**：DLL 先检查该 TLP 类型所需的流控信用是否足够。信用不足时，TLP 必须继续留在发送侧。
2. **DLL 封装并保存副本**：对需要可靠交付的 TLP，发送端分配序列号、生成 LCRC，并将可重放的副本放入 Replay Buffer，然后交由物理层发送。
3. **接收端检查顺序和 LCRC**：接收端仅接受期望序列号的有效 TLP；发现 LCRC 错误、缺失或不符合期望的序列号时，不向事务层交付该 TLP。
4. **通过 DLLP 反馈结果**：成功接收时返回 ACK；需要发送端回退重传时返回 NAK。ACK 同时允许发送端回收已确认的 Replay Buffer 空间。
5. **有序交付事务层**：只有通过链路级检查且顺序正确的 TLP 才向上传递。重放在本链路内完成，对上层透明。

这里的“重放”不是软件重试：它由硬件链路逻辑在有限的重放缓冲区和计时器约束下完成。若错误无法在规定条件内恢复，链路会进入恢复或错误处理路径，而不是无限重传。

## 流量控制：为什么 DLL 需要信用

PCIe 是接收端驱动的信用式流控。每个接收端根据自身缓冲能力公布信用，发送端将信用视作发送许可。

- 信用按 **Posted（P）**、**Non-Posted（NP）** 和 **Completion（Cpl）** 三类请求/响应流量分别维护；每类又区分 Header 与 Data 信用。
- 链路初始化期间，双方通过初始化流控 DLLP 建立彼此的初始信用视图；运行期间则以流控更新 DLLP 报告新增的可用空间。
- 发送端必须同时满足所需的 Header 和 Data 信用，才可发送相应 TLP。已发送的信用在接收端释放缓冲后，随更新消息返还。

信用控制解决的是“接收端是否有地方存放 TLP”，而 ACK/NAK 解决的是“已发送的 TLP 是否可靠到达”。两者彼此独立，但都由 DLL 协同完成。

## DLLP、TLP 与 LCRC 的关系

| 项目 | 用途 | 与可靠性的关系 |
| --- | --- | --- |
| TLP | 携带 Memory、Configuration、Message、Completion 等事务语义 | 传统模式下由 DLL 编号、保护并在必要时重放 |
| DLLP | 传递 ACK/NAK、流控以及链路级控制信息 | 是确认、重放和信用更新的控制通道 |
| LCRC | 单链路 CRC 校验 | 用于发现链路传输损坏；校验失败的 TLP 不向事务层交付 |
| ECRC | 可选的端到端完整性检查 | 跨越多个链路，不能替代每一跳的 LCRC 和 DLL 重放 |

> ACK、NAK 和流控更新本身也是链路级协议的一部分。分析抓包时，不能只看 TLP；缺少 DLLP 往往无法解释“为什么未继续发送”或“为什么发生重放”。

## Flit Mode 下的差异

PCIe 6.0 及后续规范引入 Flit Mode。此时链路以固定大小的 FLIT 为传输和可靠性处理单位，DLL 的职责仍是可靠交付、流控和链路级控制，但封装、完整性校验以及重放的具体格式不再等同于传统 Non-Flit TLP 的“序列号 + LCRC”模型。

阅读或实现时应先确认链路工作模式：

- **Non-Flit Mode**：以传统 TLP/DLLP 规则理解序列号、LCRC、ACK/NAK 与 Replay Buffer。
- **Flit Mode**：以 FLIT、Data Link Protocol（DLP）和该模式定义的 CRC/FEC、确认及重放规则为准。

因此，不应将 Non-Flit 的字段布局、计时器或重放细节直接套用到 Flit Mode。两种模式共享 DLL 的目标，但报文组织和具体状态机要求不同。

## 与 LTSSM 和错误恢复的边界

DLL 只在数据链路可用时提供服务；链路训练、速率/宽度协商和电气状态转换由物理层及 LTSSM（Link Training and Status State Machine）主导。当 DLL 检测到无法由正常重放恢复的异常时，需要与链路状态机的恢复流程配合。

实践上可以这样划分：

- **可由 ACK/NAK 与 Replay Buffer 修复的瞬态错误**：由 DLL 在当前链路内处理。
- **训练、均衡、失锁、严重协议异常或重复恢复失败**：进入 LTSSM 相关的恢复、重新训练或错误报告路径。
- **跨设备、跨交换端口的事务结果**：由事务层、软件和平台错误处理机制关注，DLL 不提供端到端投递保证。
