---
layout: post
title: "PCIe Non-Flit Mode重传机制技术面试题"
date: "2026-08-26 00:00:00"
---

## 1. 基本概念与可靠性边界

Q001. Non-Flit Mode的数据链路层Replay要解决哪些错误，哪些错误不属于它的处理范围？
Q002. 为什么PCIe将Replay设计成逐Link、逐跳的可靠性机制，而不是端到端机制？
Q003. NFM的完整性保护和重传单位是什么，为什么不是DLLP或Transaction？
Q004. NFM Replay与Transaction Layer重新发起一次Request有什么本质区别？
Q005. 为什么NFM采用Go-Back-N，而没有提供Selective Replay？
Q006. Replay期间为什么不能为重传TLP重新分配Sequence Number？
Q007. Replay期间为什么不重新消耗Flow Control Credit？
Q008. Nullified TLP为什么不进入Retry Buffer，也不推进`NEXT_TRANSMIT_SEQ`？

## 2. 初始化与状态变量

Q009. 进入`DL_Inactive`时，`NEXT_TRANSMIT_SEQ`、`ACKD_SEQ`和`NEXT_RCV_SEQ`分别初始化为什么值？
Q010. 为什么`ACKD_SEQ`初始化为`FFFh`，而第一条新TLP使用`000h`？
Q011. `NEXT_TRANSMIT_SEQ`、`ACKD_SEQ`和Retry Buffer最老条目之间应保持什么关系？
Q012. `NEXT_RCV_SEQ`表示最后正确接收的序号，还是下一条期望接收的序号？
Q013. `NAK_SCHEDULED`解决什么问题，在哪些状态或事件下置位和清除？
Q014. `REPLAY_NUM`统计链路生命周期内的Replay总次数，还是连续无确认进展的Replay次数？
Q015. Physical LinkUp在Recovery过程中保持为1与变为0，对Retry Buffer和序号状态分别有什么影响？

## 3. TLP发送、序号与LCRC

Q016. 12-bit TLP Sequence Number在线路Framed TLP中的位置在哪里，是否属于Transaction Layer TLP内容？
Q017. LCRC的计算覆盖哪些字段，为什么必须覆盖TLP Sequence Number？
Q018. LCRC计算是否包含32-bit LCRC字段本身、Framing Symbol和物理层编码开销？
Q019. `NEXT_TRANSMIT_SEQ`在TLP被Transaction Layer提交、写入Retry Buffer还是完成线路发送时递增？
Q020. 发送端应在什么时点保证TLP已经具备完整的Replay副本？
Q021. Retry Buffer至少需要保存哪些信息，规范是否强制保存完整的线路编码形式？
Q022. 一个TLP正在发送时发生Replay触发，为什么不能从TLP中间终止当前传输？
Q023. 12-bit序号从`FFFh`回卷到`000h`时，如何保证新旧TLP不会产生歧义？
Q024. 为什么发送端Outstanding TLP序号范围不能达到或超过2048？

## 4. TLP接收检查

Q025. 接收端处理一个NFM TLP时，Receiver Error、Nullified、LCRC和Sequence Number检查的先后关系是什么？
Q026. LCRC错误时为什么不能使用收到的TLP Sequence Number更新`NEXT_RCV_SEQ`？
Q027. 收到LCRC正确且序号等于`NEXT_RCV_SEQ`的TLP后，接收端依次执行哪些状态更新？
Q028. 收到LCRC错误的期望TLP时，`NEXT_RCV_SEQ`、`NAK_SCHEDULED`和待发送Nak序号如何变化？
Q029. 收到序号不等于`NEXT_RCV_SEQ`的TLP时，为什么必须先丢弃而不能暂存等待缺失TLP？
Q030. 如何使用`(NEXT_RCV_SEQ - Received_Seq) mod 4096 <= 2048`区分重复TLP和序号缺口？
Q031. 当`NEXT_RCV_SEQ=001h`而收到`FFFh`时，接收端为什么将其判断为重复TLP？
Q032. 收到重复TLP时为什么调度Ack而不是Nak，Ack中应填写什么序号？
Q033. 收到超前TLP并检测到序号缺口时，Nak中应填写缺失TLP序号还是最后正确接收序号？
Q034. 正确Nullified TLP与LCRC错误TLP在错误报告、Nak调度和序号推进方面有什么区别？
Q035. 为什么只有TLP被转交给Receive Transaction Layer后，Receiver Flow Control才对其进行记账？

## 5. Ack/Nak生成与Ack延迟

Q036. NFM的Ack/Nak DLLP为什么采用累计确认，而不是逐TLP确认？
Q037. 为什么Ack和Nak的`AckNak_Seq_Num`都填写`NEXT_RCV_SEQ - 1`？
Q038. `AckNak_LATENCY_TIMER`的监视对象是什么，它与发送端`REPLAY_TIMER`有什么区别？
Q039. 从没有待确认TLP变为收到第一条合法TLP时，`AckNak_LATENCY_TIMER`从哪个事件开始计时？
Q040. 后续合法TLP持续到达时，为什么不能为每条TLP重新启动`AckNak_LATENCY_TIMER`？
Q041. 达到Ack Latency Limit时，调度Ack还必须满足哪些链路状态、发送状态和`NAK_SCHEDULED`条件？
Q042. 为什么规范允许比Ack Latency Limit更频繁地发送Ack？
Q043. 当Ack返回方向正在发送一个长TLP时，Ack应如何调度，合规测试如何处理这段阻塞时间？
Q044. L0s退出延迟和Extended Synch为什么会影响Ack实际到达发送端的时间？
Q045. 为什么实现不要求根据L0s退出延迟或Extended Synch动态调整Ack调度算法？

## 6. 发送端接收Ack/Nak

Q046. 在DLLP CRC和Type检查通过后，协议如何判断`AckNak_Seq_Num`是否合法？
Q047. Figure 3-21中的两个模4096窗口公式分别排除哪一类非法反馈？
Q048. `AckNak_Seq_Num == ACKD_SEQ`时，Ack为什么合法但不产生确认进展？
Q049. Retry Buffer为空时收到Ack，在哪种条件下不是Data Link Protocol Error？
Q050. Ack序号既不等于`ACKD_SEQ`也不对应未确认TLP时，发送端必须执行哪些动作？
Q051. 收到推进确认边界的Ack后，应按什么顺序释放Retry Buffer、更新`ACKD_SEQ`并处理两个Replay相关计时状态？
Q052. 收到`Nak N`时，为什么首先累计释放至N，然后才从新的最老未确认TLP启动Replay？
Q053. `Nak N`表示“N需要重传”还是“N及以前已确认”，第一个待重传序号如何确定？
Q054. 为什么不能用普通整数大小比较判断Ack/Nak新旧，而必须使用模4096关系和当前Outstanding窗口？

## 7. Replay触发与执行

Q055. NFM Replay的两种触发源分别是什么，它们如何确定Replay起点？
Q056. Nak触发Replay与`REPLAY_TIMER`超时触发Replay，在Retry Buffer释放行为上有什么不同？
Q057. Replay开始前为什么必须阻止接受新的Transmit Transaction Layer TLP？
Q058. Standard Replay应从哪个Retry Buffer条目开始，并按照什么顺序发送？
Q059. Replay过程中收到Ack/Nak时为什么仍然必须处理，协议允许如何折叠这些反馈？
Q060. Replay过程中收到推进确认边界的Ack后，发送端可以如何处理尚未开始重发但已经确认的TLP？
Q061. 为什么已经开始重发的TLP即使同时被Ack确认也必须完成发送？
Q062. Replay期间先收到`Nak 102`、随后收到`Ack 105`时，为什么后者可以覆盖前者？
Q063. 一轮Replay完成的判据是什么，它与Retry Buffer最终变空是否是同一个事件？
Q064. Replay退出正常发送后，仍未收到Ack的Replay TLP为什么必须继续保留在Retry Buffer中？
Q065. 多次Replay仍没有确认进展时，`REPLAY_NUM`如何使链路进入进一步恢复流程？

## 8. REPLAY_TIMER

Q066. `REPLAY_TIMER`为什么是整个发送方向共享的确认进展Timer，而不是每个TLP一个Timer？
Q067. Timer未运行时，发送或重传TLP的哪个线路事件会启动它？
Q068. Timer已经运行时继续发送新的普通TLP，为什么不能反复清零Timer？
Q069. 什么样的Ack能够清零并重新启动`REPLAY_TIMER`，重复Ack为什么不能？
Q070. 收到Nak、Timer到期以及Retry Buffer变空时，`REPLAY_TIMER`分别进入什么状态？
Q071. 每轮Replay中，为什么在第一个重传TLP的最后一个Symbol处清零并重新启动Timer？
Q072. LTSSM进入Recovery或Configuration时，`REPLAY_TIMER`是清零、继续计数还是保持当前值暂停？
Q073. Simplified `REPLAY_TIMER` Limit为什么以Symbol Times表示，如何换算成实际时间？
Q074. Extended Synch置位为什么允许更大的Simplified `REPLAY_TIMER` Limit？
Q075. 为什么Replay Timer Timeout只是Replay触发和错误报告条件，而不等于立即进入`DL_Inactive`？

## 9. Retry Buffer容量与性能

Q076. Retry Buffer容量为什么近似等于最大数据产生速率乘以最坏Ack确认往返延迟？
Q077. Ack Latency、反向链路阻塞、传播延迟、Retimer、SRIS、L0s和本地流水线分别如何影响Buffer尺寸？
Q078. 按Byte组织与按TLP Entry组织Retry Buffer时，最坏流量模型为什么不同？
Q079. Retry Buffer满时发送端应如何节流，这会影响协议正确性还是主要影响吞吐率？
Q080. 更大的Retry Buffer为什么既能降低正常流量被节流的概率，又可能放大Go-Back-N的最坏Replay开销？

## 10. RTL设计与验证场景

Q081. 如何设计Retry Buffer的写指针、累计释放指针、Replay读指针和本轮Replay结束指针？
Q082. Ack处理、正常发送和Replay读取同时访问Retry Buffer时，需要保证哪些原子性和指针顺序关系？
Q083. 如何证明Retry Buffer中有效条目的序号始终构成连续的模4096窗口？
Q084. 如何验证重复Ack不能推进`ACKD_SEQ`或重新启动`REPLAY_TIMER`？
Q085. 如何验证旧Ack、未来Ack和回卷附近的Ack均被Figure 3-21窗口逻辑正确分类？
Q086. 如何构造“原Ack丢失、Timer超时、重复TLP到达、接收端再次Ack”的端到端测试？
Q087. 如何构造Replay过程中Ack推进确认边界并跳过尚未开始重发TLP的测试？
Q088. 如何验证Replay过程中当前TLP绝不会因新Ack/Nak到达而被截断？
Q089. 如何验证Nak丢失、Ack丢失和TLP丢失三种场景最终都能由`REPLAY_TIMER`恢复？
Q090. 哪些断言可以保证Replay不重复消耗Flow Control Credit、不改变原TLP内容且不分配新Sequence Number？
