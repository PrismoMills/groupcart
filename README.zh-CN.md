<div align="center">

# GroupCart

### 一个购物车，多个商家，一次完成下单。

跨店选购，集中查看订单；<br>每个商家独立处理自己的商品和配送。

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20app-000000?logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8-4479A1?logo=mysql&logoColor=white)

[功能体验](#从挑选商品到确认收货) · [本地启动](#在本地试一试) · [实现与测试](#实现与测试) · [English](README.md)

</div>

---

## 从挑选商品到确认收货

在一家店选好商品，还可以继续逛另一家。结算时，GroupCart 把购物车中的商品按商家拆成独立订单，再放进同一个结算分组。你可以一起查看这次购买，也能分别跟踪各家店的发货进度。

| 顾客可以做什么 | 商家可以做什么 |
| :--- | :--- |
| 按商家、标签浏览商品，即时搜索 | 发布商品，搜索自己的商品目录 |
| 跨店加购，一次结算 | 查看、处理属于自己的订单 |
| 在同一购买分组下查看不同商家的订单 | 独立更新发货状态 |
| 取消符合条件的订单、发货前移除商品、确认收货 | 在同一个平台管理商品和履约 |

项目同时提供顾客注册、商家目录和商家目录管理功能。

### 一次购买，各自发货

```text
购物车
├── 商家 A · 两件商品 ──→ 商家订单 A · 备货中
└── 商家 B · 一件商品 ──→ 商家订单 B · 已发货
                          └── 同一个结算分组
```

结算时会读取 MySQL 中的当前价格、校验数量，并在同一事务中创建各商家订单。任何一部分失败，整次结算都会回滚。移除符合条件的商品时，订单金额也会重新计算。

## 在本地试一试

准备 **Python 3.10+**、**MySQL 8** 和浏览器。运行 JavaScript 检查时才需要 Node.js。

### 1. 安装依赖

在仓库根目录打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 导入演示数据库

在 MySQL Workbench 中打开并运行 `database/seed.sql`。脚本会创建 `ecommerceplatform` 数据库，导入商品、顾客、商家、标签和订单等演示数据。

> 脚本会删除并重建数据表。请用于全新的演示数据库；重复执行会覆盖已有数据。详见[数据库说明](docs/DATABASE.md)。

### 3. 配置数据库连接

```powershell
Copy-Item app/db_config.example.json app/db_config.json
```

在 `app/db_config.json` 中填写自己的 MySQL 用户名和密码，数据库名称保留为 `ecommerceplatform`。模板用户名需要自行替换，导入脚本不会创建 MySQL 用户。本地配置已加入 Git 忽略规则。

### 4. 启动

```powershell
.\.venv\Scripts\python.exe app/main.py
```

打开 **[http://localhost:5000](http://localhost:5000)**。前端使用 `localhost` 和浏览器本地状态，请始终使用同一主机名。页面和图片由 Flask 一起提供，无需单独启动前端服务。

macOS / Linux 下将 Python 路径换成 `.venv/bin/python`，复制命令使用 `cp`。

| 演示身份 | 账号 | 密码 |
| :--- | :--- | :--- |
| 顾客 | `C001` 或 `C002` | 与账号相同 |
| 商家 | `V001` 或 `V002` | 与账号相同 |

账号区分大小写。这些是网站演示账号，与 MySQL 的连接账号无关。

## 实现与测试

<details>
<summary><strong>目录结构</strong></summary>

```text
app/
├── main.py                 Flask 路由与结算逻辑
├── webpage/                HTML、CSS 和 JavaScript
├── static/images/          演示商品图片
└── db_config.example.json  本地数据库配置模板
database/seed.sql           数据表与演示数据
tests/                      后端、前端检查
docs/                       数据库、测试和项目背景说明
```

</details>

<details>
<summary><strong>运行检查</strong></summary>

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_fixes.py
node tests/test_cart.cjs
node tests/test_order_groups.cjs
node tests/test_tag_search.cjs
node tests/test_catalog.cjs
```

后端回归测试使用内存 SQLite 适配器，包含失败场景。真实 MySQL 环境下的检查方式见[测试说明](docs/TESTING.md)。

</details>

<details>
<summary><strong>历史订单如何分组</strong></summary>

新订单使用明确的结算 ID。缺少结算 ID 的历史订单，按顾客和精确到秒的时间合并展示；同一顾客在同一秒内完成的两次历史购买，可能会显示为一组。

</details>

## 使用真实账号之前

GroupCart 当前用于本地体验与评估，尚未实现支付、库存预留、物流集成和退款。演示密码以明文保存，接口通过客户端传入的账号 ID 识别身份，尚未建立服务端登录会话；商家目录创建功能也没有管理员权限控制。接入真实用户或资金之前，需要继续完善认证与授权。

项目起始于课程作业，随后补充了事务结算、订单分组和界面改进。项目背景及演示素材说明见[此处](docs/CREDITS.md)。
