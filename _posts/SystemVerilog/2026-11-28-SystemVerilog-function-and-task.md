---
layout: post
title: "SystemVerilog 中的 function 与 task"
date: 2026-11-28
description: "从返回值、时间控制、调用关系与 automatic/static 四方面说明 function 与 task 的区别，并给出模块与 UVM 类中的写法示例。"
tags: [SystemVerilog, function, task]
---

`function` 和 `task` 都是 SystemVerilog 里封装行为的子程序，但约束和适用场景不同。最核心的一条是：**function 必须零时间返回，task 可以消耗时间**。

## 一眼看懂区别

| 特性 | `function` | `task` |
|---|---|---|
| 返回值 | 有（或声明为 `void`） | 无 |
| 时间控制（`#`、`@`、`wait`、`fork`） | ❌ 不允许 | ✅ 允许 |
| 执行时长 | 零时间返回 | 可跨多个时钟周期 |
| 能调用什么 | 只能调用 `function` | `function` 和 `task` 都可以 |
| 能否用在表达式里 | 可以 | 不可以 |
| 典型用途 | 纯计算、编解码、断言辅助、getter | 驱动激励、等待握手、打印日志、序列步骤 |

## function：只能做“零时间”的计算

`function` 进入后必须立即返回，因此不能写任何可能消耗仿真时间的语句：

```systemverilog
function automatic logic [7:0] reverse_bits(input logic [7:0] v);
    for (int i = 0; i < 8; i++) begin
        reverse_bits[i] = v[7 - i];
    end
endfunction
```

- 可以声明返回值类型；无返回值时写 `void`，例如 `function void print_cfg(...)`；
- SystemVerilog 允许 `input` / `output` / `inout` / `ref` 参数（Verilog-2001 时代只允许 `input`）；
- 可以在 `assign`、`if`、`$display` 等表达式位置直接调用；
- **不能**调用 `task`，因为 task 可能消耗时间。

## task：可以等待、可以跨周期

`task` 没有返回值，但可以包含时间控制，适合描述“按顺序发生”的行为：

```systemverilog
task automatic send_byte(input logic [7:0] data);
    @(posedge clk);
    valid    <= 1'b1;
    data_bus <= data;
    while (!ready) @(posedge clk);
    valid    <= 1'b0;
endtask
```

- 返回值靠 `output` / `inout` / `ref` 参数带出，例如 `task get_status(output logic [7:0] st);`
- 可以调用其他 `task` / `function`，也可以使用循环、`fork...join` 等耗时结构；
- 不能出现在表达式里，只能作为语句调用。

## automatic 与 static

模块 / interface 里的子程序**默认是 static 存储**：同一个 function/task 被多处并发调用时共用内部变量，重入时容易互相踩数据。需要可重入时加 `automatic`：

```systemverilog
module m;
    logic       clk;
    logic       valid, ready;
    logic [7:0] data_bus;

    function automatic int next_pow2(input int v);
        int r = 1;
        while (r < v) r <<= 1;
        return r;
    endfunction

    task automatic wait_cycles(input int n);
        repeat (n) @(posedge clk);
    endtask
endmodule
```

类里的方法默认是实例方法，方法内局部变量每次调用独立分配（可重入）；只有声明为 `static` 的方法才共享类级存储。类方法同样遵循“function 不能等时间、task 可以”的规则。

## 在类与 UVM 中的写法

```systemverilog
class driver extends uvm_driver #(bus_item);
    `uvm_component_utils(driver)

    virtual bus_if vif;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    // 纯计算：适合 function
    function int unsigned byte_count(int unsigned bits);
        return (bits + 7) / 8;
    endfunction

    // 需要等待：必须用 task
    virtual task run_phase(uvm_phase phase);
        forever begin
            seq_item_port.get_next_item(req);
            send_byte(req.data);
            seq_item_port.item_done();
        end
    endtask

    task send_byte(input logic [7:0] data);
        @(posedge vif.clk);
        vif.valid <= 1'b1;
        vif.data  <= data;
        do @(posedge vif.clk); while (!vif.ready);
        vif.valid <= 1'b0;
    endtask
endclass
```

要点：

- 需要被子类覆盖的方法加 `virtual`；只定义契约则用 `pure virtual function` / `pure virtual task`（只能在 `virtual class` 里）；
- UVM 的 `run_phase`、`write`、`get_next_item` 都是 task，因为要等待；
- `get_type_name()`、`get_name()`、比较函数等纯计算接口是 function；
- 类里的 function 也可以加 `virtual`，用于多态。

## 常见坑

| 现象 | 原因 | 处理 |
|---|---|---|
| 编译报 function 内不允许时间控制 | 在 function 里写了 `#` / `@` / `wait` | 改成 task，或把等待移到调用处 |
| 并发调用时结果互相污染 | 模块级 task/function 默认 static | 声明为 `automatic` |
| 想直接把 task 结果写进表达式 | task 没有返回值 | 用 `output` / `ref` 参数带出，或拆成 function |
| 子类覆盖后没有生效 | 父类方法没声明 `virtual` | 父类方法加 `virtual` |

## 小结

- **要不要等时间**：要等就用 `task`，纯计算就用 `function`；
- **要不要返回值**：要返回值用 `function`；task 用 `output` / `ref` 带出；
- **能不能进表达式**：只有 `function` 可以；
- **并发与重入**：模块级子程序按需加 `automatic`，类方法注意 `static` 与实例方法的区别。
