---
layout: post
title: "SystemVerilog 中的 virtual：虚方法、虚类与虚接口"
date: 2026-11-28 16:00:00 +0800
description: "区分 virtual function、virtual class 与 virtual interface 三种用法，说明动态派发、抽象基类契约与 DUT 接口引用的适用场景。"
tags: [SystemVerilog, UVM, OOP, Verification]
---

SystemVerilog 里的 `virtual` 有三种常见写法，作用完全不同：修饰方法、修饰类、修饰接口变量。本文按“是什么 / 为什么 / 怎么用”的顺序整理它们的区别与使用场景。

## 三种用法一览

| 写法 | 作用 |
|---|---|
| `virtual function f()` | 调用时根据对象的实际类型选择覆盖实现（动态派发） |
| `virtual class` | 定义不能直接实例化的抽象类，用来放流程骨架和接口契约 |
| `virtual interface` | 声明引用某个 interface 实例的变量，本身不创建接口 |

对类方法而言，`virtual` 控制的是方法调用时的动态派发；它并不规定模拟器必须用某种“地址表”来实现。

## 为什么需要 virtual

在 SV 的类继承中，子类可以覆盖父类方法。若想通过**父类句柄**调用到子类的覆盖实现，父类方法必须声明为 `virtual`：

```systemverilog
class Base;
    virtual function void f(); $display("Base"); endfunction
endclass

class Derived extends Base;
    function void f(); $display("Derived"); endfunction
endclass

module tb;
    initial begin
        Base b;
        Derived d;
        d = new;
        b = d;
        b.f(); // 调用 Derived::f
    end
endmodule
```

`b` 的声明类型是 `Base`，实际引用的是 `Derived` 对象，于是调用结果有两种可能：

- **非 virtual**：通过 `Base` 句柄调用，执行 `Base::f`。
- **virtual**：根据实际对象类型，执行 `Derived::f`。

一个接收 `Base` 句柄的方法，可能被传入不同子类对象；虚方法调用按**每次传入对象的实际类型**选择实现，这就是动态派发。

UVM 工厂在运行时决定创建哪个子类，那是**对象创建**机制；虚方法决定调用时执行哪个实现——两者是不同层面的事：

```systemverilog
drv = my_driver::type_id::create("drv", this); // UVM 工厂创建子组件，this 为 parent
```

父类方法声明 `virtual` 后，子类覆盖时可以省略该关键字（虚方法“一旦虚拟，永远虚拟”）；重复写出来更利于阅读。

## 怎么用

### 1. virtual function

标记方法的调用要**动态绑定**：由运行时对象的实际类型决定执行哪个实现。子类覆盖父类虚方法后，通过父类句柄调用会落到实际对象对应的实现上。

### 2. virtual class

`virtual class` 定义功能骨架：父类写公共流程，具体步骤留给子类实现；它不能直接实例化，只能被继承。骨架里可以混合“必须实现”的契约和“可覆盖”的默认实现：

```systemverilog
virtual class base_test;
    virtual function void execute();            // ① 流程骨架
        configure();                            //    ← 子类决定
        build_env();                            //    ← 父类公共
        check();                                //    ← 子类决定
    endfunction

    pure virtual function void configure();     // ② 契约
    pure virtual function void check();

    virtual function void build_env();          // ③ 公共默认实现
        $display("build_env");
    endfunction
endclass
```

其中 `pure virtual` 放“必须由子类决定的行为”，普通 `virtual` 放“有默认行为、子类可改可不改的行为”。

| 判据 | 例子 |
|---|---|
| 这个类型不该有自己的实例，“只有具体子类才有意义” | 交通工具、驱动器规范、事务基类 |
| 需要强制具体子类实现某些方法 | `pure virtual function void drive();` |
| 需要一份接口契约供多人/多处实现 | 参考模型基类、scoreboard 比较器基类、`base_test` |
| 父类只定义契约或部分实现，不应直接实例化 | 抽象的测试或驱动器基类 |

### 3. virtual interface

`virtual interface` 是**引用已有 interface 实例的变量**，常用于让类中的验证代码访问 DUT 接口信号，也可以作为 task/function 的参数。它不会创建 interface 实例，也不负责虚方法派发。

```systemverilog
interface bus_if;
    logic clk;
    logic valid;
    logic ready;
endinterface

class driver;
    virtual bus_if vif;   // 引用外部已经存在的 interface 实例

    function new(virtual bus_if vif);
        this.vif = vif;
    endfunction

    task drive();
        @(posedge vif.clk);
        vif.valid <= 1'b1;
    endtask
endclass
```

## 小结

| 关键字 | 回答的问题 | 注意 |
|---|---|---|
| `virtual function` | 这次调用执行哪个实现？ | 子类覆盖时可不写 `virtual`，但函数签名要保持一致 |
| `virtual class` | 这个类型能否实例化？ | 不能单独 `new`，只能通过具体子类使用 |
| `virtual interface` | 类如何访问 DUT 接口？ | 只是引用，不会创建 interface 实例 |
