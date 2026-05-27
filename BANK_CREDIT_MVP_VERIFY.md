# Bank Credit MVP Verification

这份步骤用于验证 `plugins/bank_credit_mvp` 信贷流程 MVP。

## 1. 激活虚拟环境

在仓库根目录执行：

```bash
cd /Users/chenzhiyu/WebstormProjects/2026/my-hermes-agent
source venv/bin/activate
```

如果你的 checkout 使用的是 `.venv`，则改用：

```bash
source .venv/bin/activate
```

## 2. 运行后端流程测试

```bash
scripts/run_tests.sh plugins/bank_credit_mvp/tests/test_workflow.py -q
```

期望结果：

```text
1 passed
```

这个测试验证核心状态机：

- 初次推进会停在“开立客户号”人工阻塞步骤。
- 模拟外部系统已开客户号后，流程会继续执行。
- 调查报告基础要素保存，财报同步作为可选步骤跳过，最后保存草稿。
- 轮询工具可以扫描未完成业务，并在外部条件满足后推进。

## 2.1 启用对话插件

如果你想在 Hermes 对话或 cron 里调用信贷流程工具，先启用插件：

```bash
hermes plugins enable bank-credit-mvp
```

启用后重新打开一个 Hermes 会话。插件工具集名是：

```text
bank_credit
```

可用工具包括：

```text
bank_credit_list_cases
bank_credit_get_case
bank_credit_advance_case
bank_credit_poll_cases
bank_credit_mock_customer_created
```

## 3. 启动 Hermes Dashboard

```bash
venv/bin/python ./hermes dashboard --host 127.0.0.1 --port 18084 --no-open --skip-build
```

如果你激活的是 `.venv`，可以改成：

```bash
.venv/bin/python ./hermes dashboard --host 127.0.0.1 --port 18084 --no-open --skip-build
```

期望看到类似输出：

```text
Hermes Web UI → http://127.0.0.1:18084
```

保持这个终端窗口运行。

## 4. 打开信贷流程页面

浏览器打开：

```text
http://127.0.0.1:18084/credit-flow
```

如果直接访问跳回 Sessions 页面，可以先打开：

```text
http://127.0.0.1:18084/sessions
```

然后点击左侧导航里的 `Credit Flow`。

## 5. 验证页面初始状态

页面应展示：

- 左侧：`信贷业务待办`
- 示例业务：`上海青禾贸易有限公司`
- 右侧执行计划：
  - `开立客户号`
  - `填写调查报告基础要素`
  - `同步财报数据`
  - `保存调查报告草稿`

初始状态下，步骤进度应为 `0 / 4`。

## 6. 验证阻塞步骤

点击右侧 `检查并推进`。

期望结果：

- `开立客户号` 变为 `需人工处理`
- 页面事件里出现类似：

```text
等待客户经理在外部系统开立客户号。
```

这对应真实业务中的“流程卡住，需要客户经理去外部系统操作”。

## 7. 模拟外部系统完成

点击 `开立客户号` 步骤里的：

```text
模拟已开客户号
```

期望结果：

- 客户号字段变成类似 `CUST-MO-001`
- `开立客户号` 变为 `已完成`
- `填写调查报告基础要素` 变为 `已完成`
- `同步财报数据` 变为 `已跳过`
- `保存调查报告草稿` 变为 `已完成`
- 总进度变为 `4 / 4`
- 业务状态变为 `已完成`

事件里应看到：

```text
已查询到客户号，流程继续。
调查报告基础要素已保存。
财报数据未就绪，按非阻塞步骤跳过。
调查报告草稿已保存。
```

## 8. 重置演示数据

如果想从头再跑一遍，点击左侧 `重置`。

## 9. 可选：验证轮询按钮

页面中的 `轮询阻塞业务` 对应 cron 后续会调用的轮询能力。

验证方式：

1. 点击 `重置`。
2. 点击 `检查并推进`，让业务停在 `开立客户号`。
3. 点击 `模拟已开客户号`。
4. 如果页面已自动完成，说明外部条件满足后推进正常。
5. 也可以在阻塞后点击 `轮询阻塞业务`，它会检查所有未完成业务；外部条件未满足时会保持阻塞。

## 10. 可选：创建新业务

页面顶部可以填写：

- 客户名称
- 授信金额
- 授信用途

然后点击 `新建业务`。

新业务会进入同样的执行计划。

## 11. 可选：创建 cron 轮询任务

先确保插件已启用，并打开新会话确认工具可用。

创建一个每 5 分钟检查一次的 cron job：

```bash
hermes cron create \
  "every 5m" \
  "检查所有未完成的银行信贷业务。调用 bank_credit_poll_cases。只汇报状态发生变化的业务，以及仍然阻塞且需要客户经理处理的业务。不要伪造外部系统完成结果。" \
  --name "Bank credit workflow poller" \
  --skill bank-credit-workflow
```

手动触发一次：

```bash
hermes cron run <job_id>
hermes cron tick
```

查看任务：

```bash
hermes cron list
```

## 12. 可选：验证插件被 Dashboard 发现

```bash
curl -s http://127.0.0.1:18084/api/dashboard/plugins
```

返回结果里应包含：

```json
"name":"bank-credit-mvp"
```

注意：业务接口 `/api/plugins/bank-credit-mvp/...` 有 dashboard 会话鉴权，直接 `curl` 不带 token 会返回 `Unauthorized`，这是正常的。页面内访问会自动带 token。

## 13. 当前实现边界

这个 MVP 目前使用 mock 外部系统状态：

- `模拟已开客户号` 代替真实“客户信息系统查询接口”
- `模拟财报已维护` 代替真实“财报系统查询接口”

后续接真实银行系统时，主要替换 `plugins/bank_credit_mvp/workflow.py` 中的外部状态查询和本系统保存逻辑即可。
