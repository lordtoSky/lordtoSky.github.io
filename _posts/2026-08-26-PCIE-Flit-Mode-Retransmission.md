---
layout: post
title: "PCIe No Flit Mode重传机制"
date: "2026-08-26 00:00:00"
---

## 1. 重传的目的

重传的目的主要是为了保障单跳链路传输的数据完整性，在链路出现丢失或不可纠正错误的时候，重新发送受影响的数据，保证两个component之间可靠有序交付TLP

## 2. 什么情况下会触发重传

重传的触发有两种情况：一是数据完整性遭到破坏且无法恢复，二是长时间未能确定包是否被可靠传输导致超时。
第一种情况下，接收端通过LCRC/CRC校验确定该TLP出现异常，返回NAK，要求发送端进行数据重传。
第二种情况下，发送端内部的replay timer因为长时间未收到ack/nak导致溢出，进而进入replay状态

## 3. 重传是如何确定哪些数据需要传输的

不论哪种情况，最终重传的内容都来自replay buffer。replay buffer会通过ack来确认哪些缓存需要被释放，nak携带的序列号会通知replay从哪一个包开始(NAK_SEQ_NUM+1)。

## 4. 序列号规则

nfm下序列号为12bit，被置于TLP前，与TLP及LCRC构成framed TLP。序列号范围是0-4095，窗口则是2048。窗口存在的作用是为了区分有效反馈和过期反馈，避免过期反馈干扰传输的正常运行。比如过期和重复的nak会触发不必要的replay。
fm则为10bit，不再是每个TLP独立拥有，而是以Flit为单位分配，置于DLP字段。同时由于该字段随控制数据类型不同有不同的解释，因此不是所有Flit都携带当前序列号，需要接收端根据内部的隐性序列号计数器来计算当前的序号是否缺失。随之而来的是链路recovery之后需要先进行握手同步序列号
序列握手的触发条件：初始configuration完成进入L0 或 Recovery.idle进入L0

## 5. replay buffer内容

replay buffer内缓存的内容取决于nfm/fm，均不强制要求保存完整数据包，只要求保留足够数据用于重构数据包。nfm下缓存的是TLP prefix/header/payload/ecrc + TLP sequence number，fm下缓存的则为non-NOP TLP Bytes，Flit_status以及Flit sequence number。

## 6. 重传流程

replay被触发后：

- 首先是停止从TL接收新的TLP事务，或者说是停止发送新的TLP事务。
- 然后是根据nak或者replay timer的序列号来确定replay事务范围。
  - 若是standard nak，则会将nak序号及之前还在buffer的事务缓存释放，发送nak序号+1及之后的事务。
  - 若为selective nak，则会确定待发送的包，并只发送该包，并将该报之前的事物释放。
  - 若是replay timer超时触发，则不会释放buffer，而是从最老未确认事务开始重发
- 开始replay后，按从老到新的顺序重发范围内buffer事务，期间收到的ack和nak会按照序列号进行处理
  - 若ack序列号为已被replay，可以作为ack标志进行处理，从buffer内清除缓存
  - 若ack序列号在replay范围但未被replay，作为过时ack丢弃处理
  - 若nak序列号为已被replay，则在发送完当前包后从nak请求包开始replay
  - 若nak序列号在replay范围但违背replay，作为过时nak丢弃处理
- 完成replay发送后，恢复正常TLP发送，但replay_timer是在replay发送第一个TLP后启动，而不是replay后才启动，并在收到有效ack/nak后重启

## 7. ack/nak对序列号的影响

ack/nak本质上是对序列号窗口的推进，因此需要区分为有效和无效两种。有效的ack/nak会将窗口向前推进，而非延后。
可能的组合有：

ack/nak首先按照当前序列号窗口判断有效性。有效反馈会累计确认并释放序号N及之前的Flit；只有N位于ACKD_FLIT_SEQ_NUM之后时，确认边界才会推进。

- ack105在ack107后到达：属于旧反馈，忽略并记录Data Link Protocol Error，确认边界保持107。
- ack105在ack103后到达：如果105已经发送且位于有效窗口内，则推进确认边界至105。
- nak105在nak107后到达：属于旧反馈，忽略并记录Data Link Protocol Error。
- nak105在nak103后到达：如果位于有效窗口内，则累计确认并释放至105；Replay目标为106。Standard Nak要求从106开始执行Standard Replay，Selective Nak只请求Flit 106，具体是否调度还需满足Replay Scheduling规则。
- ack103在nak105后到达：属于旧反馈，忽略并记录Data Link Protocol Error。
- ack107在nak105后到达：如果位于有效窗口内，则确认并释放至107。若Replay尚未开始，可能取消已被覆盖的Replay请求；若Replay已经开始，Ack仍需处理，但不得中断当前Replay。

协议中规定，replay过程中的ack和nak必须要处理，但ack和nak不能中断重传

## 8. retry buffer深度计算及考虑因素

buffer的深度主要由在途延迟决定，较大的buffer可以有效提高链路带宽下限，但也会增加大量的面积和功耗。

影响buffer深度计算主要是ACK返回最大延迟 ACK最大延迟 = 正反向传播延迟 + 接收端schedule阻塞延迟 + 双方处理流水线延迟 + L0s退出延迟 + 物理层延迟 + 设计余量

但如果考虑因为链路原因导致ack丢失的话，还需要额外加入 replay_timer_limit + replay周期 + 前序ack排队阻塞

深度可以计算为 理想深度 = 最大延迟 x TL事务产生速率

## 9. replay对带宽和延迟的影响

replay过程中，无法发送新的TLP，只能发送旧TLP，因此相当于新数据带宽为0，仍然能够达到物理速率上限。

对于一端链路，总共发送m个事务，其中触发n次有效replay，每次replay平均传输z个事务后结束replay。那么实际带宽是理想带宽的m/(m+n*z)

随着retry buffer有效深度增加，重传对带宽和延迟的影响更大。在standard nak下，retry buffer的有效内容均要进行重发。最坏场景下，需要重发retry buffer深度N。此时造成的延迟为 replay启动周期 + N发送周期 + ordered set发送周期

## 10. NFM：replay_timer 及 replay_num机制

这两者为完整性保护提供了兜底，当ack/nak在链路传输过程中遗失的时候，若无处理机制可能导致buffer无法清除ackd数据/接收端无法获取有效数据而卡在等待。

replay_timer的限制在规范中由extended synch区分为两类，一类是未引入分析仪，采用24k~30k symbol times作为延迟；另一类是引入分析仪，需要考虑分析仪时钟同步的需求，采用80k~100k symbol times作为延迟。

实际设计过程中，PCIe速率在16GTs及以上时，必须要采用simplified replay_timer limits，也即上述两条。

replay_timer重置的触发条件主要有四条：

- 链路进入DL_Inactive
- 收到有效ack
- 未replay时收到nak（replay时收到nak并不会触发重置）
- 到达上限并进入replay
- 所有待确认事务均已确认

当链路处于recovery或configuration时，replay_timer暂停，在恢复后继续计时
