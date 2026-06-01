# Bank Credit MVP Verification

这份步骤用于验证 `plugins/bank_credit_mvp` 信贷流程 MVP。当前形态是：

- `/chat` 是主入口：左侧仍是 Hermes 对话，右侧会显示信贷执行计划。
- `/credit-flow` 仍保留为完整调试页，方便重置演示数据和查看全量事件。
- 模拟银行内部系统由 `/Users/chenzhiyu/IdeaProjects/my-hermes-agent-from-scratch` 提供；信贷业务订单和流程状态以该系统为准，Hermes 只是客户端。

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
4 passed
```

这个测试验证 Hermes 插件的客户端行为：

- 查询信贷业务订单会调用外部银行系统 `/api/bank/credit-cases`。
- 推进、删除、轮询都会委托给外部银行系统。
- 插件会把外部系统返回的相对操作入口补全为可点击链接。

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
bank_credit_create_case
bank_credit_get_case
bank_credit_advance_case
bank_credit_delete_case
bank_credit_poll_cases
```

## 3. 启动外部银行系统

另开一个终端，启动外部系统后端：

```bash
cd /Users/chenzhiyu/IdeaProjects/my-hermes-agent-from-scratch/backend
mvn spring-boot:run
```

期望后端监听：

```text
http://127.0.0.1:8080
```

再另开一个终端，启动外部系统前端：

```bash
cd /Users/chenzhiyu/IdeaProjects/my-hermes-agent-from-scratch/internal-systems-frontend
npm run dev
```

期望前端监听：

```text
http://127.0.0.1:5174
```

可以直接打开下面地址确认订单台账存在：

```text
http://127.0.0.1:5174/
```

也可以打开任一步骤入口：

```text
http://127.0.0.1:5174/customer/open?caseId=loan-demo-001&customerName=上海青禾贸易有限公司
http://127.0.0.1:5174/credit/report?caseId=loan-demo-001&customerName=上海青禾贸易有限公司
http://127.0.0.1:5174/risk/admission?caseId=loan-demo-001&customerName=上海青禾贸易有限公司
http://127.0.0.1:5174/financials?caseId=loan-demo-001&customerName=上海青禾贸易有限公司
http://127.0.0.1:5174/collateral/confirm?caseId=loan-demo-001&customerName=上海青禾贸易有限公司
http://127.0.0.1:5174/credit/save?caseId=loan-demo-001&customerName=上海青禾贸易有限公司
```

## 4. 启动 Hermes Dashboard

```bash
cd /Users/chenzhiyu/WebstormProjects/2026/my-hermes-agent
venv/bin/python ./hermes dashboard --host 127.0.0.1 --port 18084 --no-open --skip-build --tui
```

如果你激活的是 `.venv`，可以改成：

```bash
.venv/bin/python ./hermes dashboard --host 127.0.0.1 --port 18084 --no-open --skip-build --tui
```

期望看到类似输出：

```text
Hermes Web UI → http://127.0.0.1:18084
```

保持这个终端窗口运行。

如果之前已经启动过 18084，可以先关闭：

```bash
venv/bin/python ./hermes dashboard --stop
```

## 5. 打开聊天页验证合并效果

浏览器打开：

```text
http://127.0.0.1:18084/chat
```

页面应是一个合并后的银行信贷平台助手：

- 中间/左侧：Hermes TUI 对话框，可以正常问答。
- 右侧：模型与工具侧栏；新对话默认不显示任何信贷流程。
- 当本轮对话调用 `bank_credit_create_case`、`bank_credit_get_case` 或 `bank_credit_advance_case` 后，才会显示该会话关联的信贷流程。
- 重新打开历史对话时，会按该对话的 sessionId 查询已关联订单。
- 一个订单可以关联多个 sessionId；`/credit-flow` 仍显示全量订单。

可以在对话框中输入：

```text
我要办理一笔上海青禾贸易有限公司的流动资金贷款，授信金额50万元。请帮我推进信贷调查报告流程。
```

如果模型识别到要办信贷业务，会调用 `bank_credit_*` 工具推进流程；即使没有立刻调用，你也可以用右侧执行计划按钮验证业务状态机。

新建订单的对话工具是：

```text
bank_credit_create_case
```

它需要客户名称、授信金额和资金用途。新建成功后，订单会自动绑定到当前 Hermes 会话。

## 6. 打开完整信贷流程调试页

浏览器打开：

```text
http://127.0.0.1:18084/credit-flow
```

如果直接访问跳回 Sessions 页面，可以先打开：

```text
http://127.0.0.1:18084/sessions
```

然后点击左侧导航里的 `Credit Flow`。

## 7. 验证页面初始状态

页面应展示：

- 左侧：`信贷业务待办`
- 示例业务：`上海青禾贸易有限公司`
- 右侧执行计划：
  - `开立客户号`
  - `填写调查报告基础要素`
  - `风险准入复核`
  - `同步财报数据`
  - `担保/抵押落实确认`
  - `保存调查报告草稿`

初始状态下，步骤进度应为 `0 / 6`。如果外部系统链接仍然是旧的 `https://credit-demo.bank.local/...`，点击左侧 `重置`，重新生成演示业务即可。

## 8. 验证阻塞步骤

点击右侧 `检查并推进`。

期望结果：

- `开立客户号` 变为 `需人工处理`
- 页面事件里出现类似：

```text
等待客户经理在外部系统开立客户号。
```

这对应真实业务中的“流程卡住，需要客户经理去外部系统操作”。

## 9. 验证外部系统跳转和自动检测

点击 `开立客户号` 步骤里的：

```text
打开外部系统
```

浏览器会打开：

```text
http://127.0.0.1:5174/customer/open?caseId=...&customerName=...
```

在外部系统页面点击：

```text
确认开立客户号
```

客户号按客户主数据维护，不再绑定某一个信贷业务编号。页面上的信贷业务编号只是用于把本次操作回写到当前业务并方便刷新流程。

完成后回到 Hermes Dashboard，点击 `轮询阻塞业务`，或者等待 `/chat` 右侧执行计划自动轮询。

期望结果：

- 客户号字段变成类似 `CUST-MO-001`
- `开立客户号` 变为 `已完成`
- `填写调查报告基础要素` 变为 `已完成`
- `风险准入复核` 需要到风险准入页确认。
- `同步财报数据` 变为 `已跳过`
- `担保/抵押落实确认` 需要到担保确认页确认。
- `保存调查报告草稿` 变为 `已完成`
- 总进度变为 `6 / 6`
- 业务状态变为 `已完成`

事件里应看到：

```text
已查询到客户号，流程继续。
调查报告基础要素已保存。
财报数据未就绪，按非阻塞步骤跳过。
调查报告草稿已保存。
```

## 10. 外部阻塞步骤不要由模型模拟

模型不应该自己模拟客户号开立、风险准入或担保落实。遇到外部阻塞步骤时，它应该给出外部系统链接，并等待用户完成后再通过 `bank_credit_advance_case` 或 `bank_credit_poll_cases` 观察状态变化。

## 11. 重置演示数据

如果想从头再跑一遍，点击左侧 `重置`。

## 12. 可选：验证轮询按钮

页面中的 `轮询阻塞业务` 对应 cron 后续会调用的轮询能力。

验证方式：

1. 点击 `重置`。
2. 点击 `检查并推进`，让业务停在 `开立客户号`。
3. 打开外部系统并点击 `确认开立客户号`。
4. 回到 Hermes 点击 `轮询阻塞业务`。
5. 如果页面推进到完成，说明外部条件满足后推进正常；外部条件未满足时会保持阻塞。

## 13. 可选：创建新业务

页面顶部可以填写：

- 客户名称
- 授信金额
- 授信用途

然后点击 `新建业务`。

新业务会进入同样的执行计划。

## 14. 可选：创建 cron 轮询任务

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

## 15. 可选：验证插件被 Dashboard 发现

```bash
curl -s http://127.0.0.1:18084/api/dashboard/plugins
```

返回结果里应包含：

```json
"name":"bank-credit-mvp"
```

注意：业务接口 `/api/plugins/bank-credit-mvp/...` 有 dashboard 会话鉴权，直接 `curl` 不带 token 会返回 `Unauthorized`，这是正常的。页面内访问会自动带 token。

## 16. 当前实现边界

这个 MVP 已经把信贷业务订单放到模拟银行内部系统中管理。Hermes 插件通过下面接口查询或变更数据：

- 订单列表：`GET http://127.0.0.1:8080/api/bank/credit-cases`
- 订单推进：`POST http://127.0.0.1:8080/api/bank/credit-cases/{caseId}/advance`
- 订单删除：`DELETE http://127.0.0.1:8080/api/bank/credit-cases/{caseId}`
- 外部后端查询：`GET http://127.0.0.1:8080/api/bank/customer-number/status`
- 外部后端办理：`POST http://127.0.0.1:8080/api/bank/customer-number/open`

风险准入、财报同步、担保确认仍是模拟页面，但它们已经是银行内部系统中的独立流程入口，状态也会写回同一笔信贷订单。
其中客户号和财报数据按客户维护；风险准入、担保落实、报告保存按本笔信贷业务维护。
