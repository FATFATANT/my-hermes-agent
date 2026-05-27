(function () {
  "use strict";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  if (!SDK) return;

  const { React } = SDK;
  const h = React.createElement;
  const { useEffect, useMemo, useState } = SDK.hooks;
  const { Button, Input, Badge } = SDK.components;

  const API = "/api/plugins/bank-credit-mvp";

  function api(path, options) {
    const opts = Object.assign({ headers: {} }, options || {});
    if (opts.body && !opts.headers["content-type"]) {
      opts.headers["content-type"] = "application/json";
    }
    if (SDK.fetchJSON) {
      return SDK.fetchJSON(API + path, opts);
    }
    const token = window.__HERMES_SESSION_TOKEN__ || "";
    if (token) opts.headers["X-Hermes-Session-Token"] = token;
    return fetch(API + path, opts).then(function (res) {
      if (!res.ok) {
        return res.text().then(function (text) {
          throw new Error(text || ("HTTP " + res.status));
        });
      }
      return res.json();
    });
  }

  function statusLabel(status) {
    return ({
      pending: "待处理",
      in_progress: "执行中",
      action_required: "需人工处理",
      completed: "已完成",
      skipped: "已跳过",
      blocked: "已阻塞",
    })[status] || status;
  }

  function statusClass(status) {
    return "bc-status bc-status-" + String(status || "pending").replace(/_/g, "-");
  }

  function kindLabel(kind) {
    return ({
      internal_api: "本系统接口",
      external_blocking: "外部系统，阻塞",
      external_optional: "外部系统，可选",
    })[kind] || kind;
  }

  function CaseList(props) {
    const cases = props.cases || [];
    return h("aside", { className: "bc-case-list" },
      h("div", { className: "bc-panel-head" },
        h("div", null,
          h("div", { className: "bc-eyebrow" }, "Loan cases"),
          h("h2", null, "信贷业务待办")
        ),
        h(Button, { size: "sm", onClick: props.onReset, title: "重置演示数据" }, "重置")
      ),
      h("div", { className: "bc-cases" },
        cases.map(function (c) {
          const active = props.selectedId === c.id;
          return h("button", {
            key: c.id,
            type: "button",
            className: active ? "bc-case bc-case-active" : "bc-case",
            onClick: function () { props.onSelect(c.id); },
          },
            h("div", { className: "bc-case-top" },
              h("strong", null, c.applicant_name),
              h("span", { className: statusClass(c.status) }, statusLabel(c.status))
            ),
            h("div", { className: "bc-case-meta" },
              h("span", null, c.id),
              h("span", null, "金额 " + Number(c.amount || 0).toLocaleString())
            ),
            h("div", { className: "bc-progress" },
              h("span", { style: { width: Math.max(4, Math.round((c.progress || 0) * 100)) + "%" } })
            )
          );
        })
      )
    );
  }

  function CreateCaseForm(props) {
    const [name, setName] = useState("杭州星河制造有限公司");
    const [amount, setAmount] = useState("800000");
    const [purpose, setPurpose] = useState("采购原材料");
    const [busy, setBusy] = useState(false);

    function submit() {
      setBusy(true);
      api("/cases", {
        method: "POST",
        body: JSON.stringify({
          applicant_name: name,
          amount: Number(amount || 0),
          purpose: purpose,
        }),
      }).then(function (data) {
        props.onCreated(data.case);
      }).finally(function () { setBusy(false); });
    }

    return h("div", { className: "bc-create" },
      h(Input, { value: name, onChange: function (e) { setName(e.target.value); }, "aria-label": "客户名称" }),
      h(Input, { value: amount, onChange: function (e) { setAmount(e.target.value); }, "aria-label": "授信金额" }),
      h(Input, { value: purpose, onChange: function (e) { setPurpose(e.target.value); }, "aria-label": "授信用途" }),
      h(Button, { size: "sm", disabled: busy, onClick: submit }, busy ? "创建中" : "新建业务")
    );
  }

  function StepCard(props) {
    const step = props.step;
    const actionRequired = step.status === "action_required";
    return h("div", { className: actionRequired ? "bc-step bc-step-action" : "bc-step" },
      h("div", { className: "bc-step-index" }, String(props.index + 1).padStart(2, "0")),
      h("div", { className: "bc-step-body" },
        h("div", { className: "bc-step-title" },
          h("strong", null, step.title),
          h("span", { className: statusClass(step.status) }, statusLabel(step.status))
        ),
        h("div", { className: "bc-step-kind" }, kindLabel(step.kind)),
        h("p", null, step.summary),
        step.external_url ? h("div", { className: "bc-step-actions" },
          h("a", {
            className: "bc-link",
            href: step.external_url,
            target: "_blank",
            rel: "noreferrer",
          }, "打开外部系统"),
          step.id === "open_customer_no" ? h(Button, {
            size: "sm",
            variant: "outline",
            onClick: props.onMockCustomer,
          }, "模拟已开客户号") : null,
          step.id === "sync_financial_data" ? h(Button, {
            size: "sm",
            variant: "outline",
            onClick: props.onMockFinancial,
          }, "模拟财报已维护") : null
        ) : null,
        step.missing_fields && step.missing_fields.length
          ? h("div", { className: "bc-warning" }, "缺少字段：" + step.missing_fields.join(", "))
          : null,
        step.last_checked_at ? h("div", { className: "bc-check" }, "上次检查 " + step.last_checked_at) : null
      )
    );
  }

  function ReportFields(props) {
    const c = props.caseData;
    const fields = c.report_fields || {};
    const [name, setName] = useState(fields.applicant_name || c.applicant_name || "");
    const [amount, setAmount] = useState(String(fields.amount || c.amount || ""));
    const [purpose, setPurpose] = useState(fields.purpose || c.purpose || "");

    useEffect(function () {
      setName(fields.applicant_name || c.applicant_name || "");
      setAmount(String(fields.amount || c.amount || ""));
      setPurpose(fields.purpose || c.purpose || "");
    }, [c.id, fields.applicant_name, fields.amount, fields.purpose]);

    function saveAndAdvance() {
      props.onAdvance({
        applicant_name: name,
        amount: Number(amount || 0),
        purpose: purpose,
      });
    }

    return h("section", { className: "bc-fields" },
      h("div", { className: "bc-section-head" },
        h("div", null,
          h("div", { className: "bc-eyebrow" }, "Report fields"),
          h("h3", null, "调查报告基础要素")
        ),
        h(Button, { size: "sm", onClick: saveAndAdvance }, "保存并推进")
      ),
      h("div", { className: "bc-field-grid" },
        h("label", null, h("span", null, "客户名称"), h(Input, { value: name, onChange: function (e) { setName(e.target.value); } })),
        h("label", null, h("span", null, "授信金额"), h(Input, { value: amount, onChange: function (e) { setAmount(e.target.value); } })),
        h("label", null, h("span", null, "授信用途"), h(Input, { value: purpose, onChange: function (e) { setPurpose(e.target.value); } })),
        h("label", null, h("span", null, "客户号"), h(Input, { value: fields.customer_no || "等待外部系统", readOnly: true }))
      )
    );
  }

  function CaseDetail(props) {
    const c = props.caseData;
    if (!c) {
      return h("main", { className: "bc-detail bc-empty" }, "选择或创建一笔信贷业务。");
    }
    const completed = (c.steps || []).filter(function (s) {
      return s.status === "completed" || s.status === "skipped";
    }).length;

    return h("main", { className: "bc-detail" },
      h("div", { className: "bc-hero" },
        h("div", null,
          h("div", { className: "bc-eyebrow" }, "Workflow instance"),
          h("h1", null, c.applicant_name),
          h("p", null, c.purpose + "，授信金额 " + Number(c.amount || 0).toLocaleString())
        ),
        h("div", { className: "bc-hero-side" },
          h(Badge, { className: statusClass(c.status) }, statusLabel(c.status)),
          h("strong", null, completed + " / " + (c.steps || []).length),
          h("span", null, "步骤完成")
        )
      ),
      h(ReportFields, { caseData: c, onAdvance: props.onAdvance }),
      h("section", { className: "bc-steps" },
        h("div", { className: "bc-section-head" },
          h("div", null,
            h("div", { className: "bc-eyebrow" }, "Execution plan"),
            h("h3", null, "执行计划")
          ),
          h("div", { className: "bc-head-actions" },
            h(Button, { size: "sm", variant: "outline", onClick: props.onPoll }, "轮询阻塞业务"),
            h(Button, { size: "sm", variant: "outline", onClick: function () { props.onAdvance({}); } }, "检查并推进")
          )
        ),
        (c.steps || []).map(function (step, index) {
          return h(StepCard, {
            key: step.id,
            step: step,
            index: index,
            onMockCustomer: props.onMockCustomer,
            onMockFinancial: props.onMockFinancial,
          });
        })
      ),
      h("section", { className: "bc-events" },
        h("div", { className: "bc-section-head" },
          h("div", null,
            h("div", { className: "bc-eyebrow" }, "Audit trail"),
            h("h3", null, "流程事件")
          )
        ),
        h("div", { className: "bc-event-list" },
          (c.events || []).slice().reverse().slice(0, 8).map(function (ev, i) {
            return h("div", { className: "bc-event", key: ev.at + i },
              h("span", null, ev.at),
              h("strong", null, ev.message)
            );
          })
        )
      )
    );
  }

  function CreditFlowPage() {
    const [cases, setCases] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [caseData, setCaseData] = useState(null);
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);

    const selectedSummary = useMemo(function () {
      return cases.find(function (c) { return c.id === selectedId; }) || null;
    }, [cases, selectedId]);

    function refreshList(nextSelected) {
      return api("/cases").then(function (data) {
        const list = data.cases || [];
        setCases(list);
        const id = nextSelected || selectedId || (list[0] && list[0].id);
        if (id) setSelectedId(id);
        return id;
      });
    }

    function refreshCase(id) {
      if (!id) return Promise.resolve();
      return api("/cases/" + encodeURIComponent(id)).then(function (data) {
        setCaseData(data.case);
      });
    }

    function reload(id) {
      setError("");
      return refreshList(id).then(function (actualId) {
        return refreshCase(actualId);
      }).catch(function (err) {
        setError(err.message || String(err));
      });
    }

    useEffect(function () { reload(null); }, []);
    useEffect(function () {
      if (selectedId) refreshCase(selectedId).catch(function (err) { setError(err.message || String(err)); });
    }, [selectedId]);

    function mutate(fn) {
      if (!selectedId) return;
      setBusy(true);
      setError("");
      fn().then(function (data) {
        if (data && data.case) {
          setCaseData(data.case);
          return refreshList(data.case.id);
        }
        return refreshList(selectedId);
      }).catch(function (err) {
        setError(err.message || String(err));
      }).finally(function () {
        setBusy(false);
      });
    }

    return h("div", { className: "bc-shell" },
      h(CaseList, {
        cases: cases,
        selectedId: selectedId,
        onSelect: setSelectedId,
        onReset: function () {
          setBusy(true);
          api("/reset-demo", { method: "POST" })
            .then(function (data) { return reload(data.case.id); })
            .finally(function () { setBusy(false); });
        },
      }),
      h("div", { className: "bc-main" },
        h(CreateCaseForm, { onCreated: function (c) { reload(c.id); } }),
        error ? h("div", { className: "bc-error" }, error) : null,
        busy ? h("div", { className: "bc-busy" }, "处理中...") : null,
        h(CaseDetail, {
          caseData: caseData || selectedSummary,
          onAdvance: function (fields) {
            mutate(function () {
              return api("/cases/" + encodeURIComponent(selectedId) + "/advance", {
                method: "POST",
                body: JSON.stringify({ report_fields: fields || {} }),
              });
            });
          },
          onMockCustomer: function () {
            mutate(function () {
              return api("/cases/" + encodeURIComponent(selectedId) + "/mock/customer-created", {
                method: "POST",
                body: JSON.stringify({ customer_no: "" }),
              });
            });
          },
          onMockFinancial: function () {
            mutate(function () {
              return api("/cases/" + encodeURIComponent(selectedId) + "/mock/financial-ready", {
                method: "POST",
              });
            });
          },
          onPoll: function () {
            mutate(function () {
              return api("/poll", { method: "POST" }).then(function () {
                return api("/cases/" + encodeURIComponent(selectedId));
              });
            });
          },
        })
      )
    );
  }

  if (window.__HERMES_PLUGINS__ && typeof window.__HERMES_PLUGINS__.register === "function") {
    window.__HERMES_PLUGINS__.register("bank-credit-mvp", CreditFlowPage);
  }
})();
