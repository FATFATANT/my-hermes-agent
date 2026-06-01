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
          ,
          step.id === "risk_admission_review" ? h(Button, {
            size: "sm",
            variant: "outline",
            onClick: function () { props.onMockExternalTask("risk_admission"); },
          }, "模拟风险复核通过") : null,
          step.id === "collateral_confirmation" ? h(Button, {
            size: "sm",
            variant: "outline",
            onClick: function () { props.onMockExternalTask("collateral_confirmation"); },
          }, "模拟担保落实") : null
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
            onMockExternalTask: props.onMockExternalTask,
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

  function SidebarPlan() {
    function currentSessionId() {
      return window.__HERMES_CHAT_SESSION_ID__ || window.__HERMES_CHAT_RESUME_SESSION_ID__ || "";
    }
    const [sessionId, setSessionId] = useState(currentSessionId);
    const [cases, setCases] = useState([]);
    const [hiddenCases, setHiddenCases] = useState([]);
    const [recoverableCases, setRecoverableCases] = useState([]);
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);
    const [lastNoticeKey, setLastNoticeKey] = useState("");

    function askChat(text) {
      window.dispatchEvent(new CustomEvent("bank-credit-chat-prompt", { detail: { text: text } }));
    }

    function load(nextSessionId) {
      const sid = nextSessionId || sessionId || currentSessionId();
      if (!sid) {
        setCases([]);
        return Promise.resolve([]);
      }
      setSessionId(sid);
      const encodedSid = encodeURIComponent(sid);
      return Promise.all([
        api("/sessions/" + encodedSid + "/cases"),
        api("/sessions/" + encodedSid + "/hidden-cases").catch(function () { return { cases: [] }; }),
        api("/cases").catch(function () { return { cases: [] }; }),
      ]).then(function (results) {
        const present = results[0].cases || [];
        const hidden = results[1].cases || [];
        const presentIds = new Set(present.concat(hidden).map(function (c) { return c.id; }));
        const recoverable = (results[2].cases || []).filter(function (c) { return !presentIds.has(c.id); }).slice(0, 3);
        setCases(present);
        setHiddenCases(hidden);
        setRecoverableCases(recoverable);
        return present;
      }).catch(function (err) {
        setError(err.message || String(err));
        return [];
      });
    }

    function poll() {
      const sid = sessionId || currentSessionId();
      if (!sid || !cases.length) return Promise.resolve([]);
      setBusy(true);
      setError("");
      const before = new Map(cases.map(function (c) { return [c.id, c]; }));
      return api("/poll", { method: "POST" })
        .then(function () { return load(sid); })
        .then(function (updatedCases) {
          updatedCases.forEach(function (updated) {
            const previous = before.get(updated.id);
            const key = [updated.id, updated.status, updated.current_step || "done", updated.progress].join(":");
            const stepChanged = previous && previous.current_step !== updated.current_step;
            const finished = updated.status === "completed" && (!previous || previous.status !== "completed");
            if ((stepChanged || finished) && key !== lastNoticeKey) {
              setLastNoticeKey(key);
              askChat("我已经完成外部系统状态检查，请使用 bank_credit_get_case 查看 " + updated.id + " 的最新状态，并继续提示客户经理下一步。");
            }
          });
          return updatedCases;
        })
        .catch(function (err) { setError(err.message || String(err)); return []; })
        .finally(function () { setBusy(false); });
    }

    useEffect(function () {
      load(currentSessionId());
    }, []);

    useEffect(function () {
      function onSession(ev) {
        const sid = ev && ev.detail && ev.detail.sessionId;
        if (sid) load(sid);
      }
      window.addEventListener("bank-credit-chat-session", onSession);
      return function () { window.removeEventListener("bank-credit-chat-session", onSession); };
    }, [sessionId]);

    useEffect(function () {
      function onTool(ev) {
        const detail = ev && ev.detail || {};
        const sid = currentSessionId() || detail.sessionId || sessionId;
        const caseId = detail.caseId;
        if (sid && caseId) {
          api("/sessions/" + encodeURIComponent(sid) + "/cases/" + encodeURIComponent(caseId), { method: "POST" })
            .then(function () { return load(sid); })
            .catch(function () { return load(sid); });
          return;
        }
        load(sid);
      }
      window.addEventListener("bank-credit-chat-tool", onTool);
      return function () { window.removeEventListener("bank-credit-chat-tool", onTool); };
    }, [sessionId]);

    useEffect(function () {
      if (!sessionId || !cases.length) return;
      const timer = window.setInterval(poll, 5000);
      return function () { window.clearInterval(timer); };
    }, [sessionId, cases.map(function (c) { return c.id + ":" + c.status + ":" + c.current_step; }).join("|"), lastNoticeKey]);

    if (!cases.length && !hiddenCases.length && !recoverableCases.length && !error) {
      return null;
    }

    if (error) {
      return h("div", { className: "bc-side-card bc-side-error" }, error);
    }

    function hideCase(id) {
      const sid = sessionId || currentSessionId();
      if (sid) api("/sessions/" + encodeURIComponent(sid) + "/cases/" + encodeURIComponent(id), { method: "DELETE" }).catch(function () {});
      const nextCases = cases.filter(function (c) { return c.id !== id; });
      const hidden = cases.find(function (c) { return c.id === id; });
      setCases(nextCases);
      if (hidden) {
        setHiddenCases(hiddenCases.some(function (c) { return c.id === id; }) ? hiddenCases : hiddenCases.concat([hidden]));
      }
    }

    function restoreCase(id) {
      const sid = sessionId || currentSessionId();
      const hidden = hiddenCases.find(function (c) { return c.id === id; });
      const recoverable = recoverableCases.find(function (c) { return c.id === id; });
      if (sid) api("/sessions/" + encodeURIComponent(sid) + "/cases/" + encodeURIComponent(id), { method: "POST" }).catch(function () {});
      const restored = hidden || recoverable;
      if (restored && !cases.some(function (c) { return c.id === id; })) {
        setCases(cases.concat([restored]));
      }
      setHiddenCases(hiddenCases.filter(function (c) { return c.id !== id; }));
      setRecoverableCases(recoverableCases.filter(function (c) { return c.id !== id; }));
    }

    function restoreAllHidden() {
      const sid = sessionId || currentSessionId();
      if (sid) {
        hiddenCases.forEach(function (c) {
          api("/sessions/" + encodeURIComponent(sid) + "/cases/" + encodeURIComponent(c.id), { method: "POST" }).catch(function () {});
        });
      }
      const existing = new Set(cases.map(function (c) { return c.id; }));
      setCases(cases.concat(hiddenCases.filter(function (c) { return !existing.has(c.id); })));
      setHiddenCases([]);
    }

    function renderCase(caseData) {
      const current = (caseData.steps || []).find(function (s) { return s.id === caseData.current_step; });
      return h("div", { className: "bc-side-case", key: caseData.id },
        h("div", { className: "bc-side-head" },
          h("div", null,
            h("div", { className: "bc-eyebrow" }, "Bank credit workflow"),
            h("strong", null, caseData.applicant_name)
          ),
          h("span", { className: statusClass(caseData.status) }, statusLabel(caseData.status))
        ),
        current ? h("div", { className: "bc-side-current" },
          h("span", null, "当前步骤"),
          h("strong", null, current.title),
          h("em", null, statusLabel(current.status))
        ) : h("div", { className: "bc-side-current" },
          h("span", null, "当前步骤"),
          h("strong", null, "流程已完成"),
          h("em", null, "已完成")
        ),
        h("div", { className: "bc-side-steps" },
          (caseData.steps || []).map(function (step, index) {
            return h("div", {
              key: step.id,
              className: step.id === caseData.current_step ? "bc-side-step bc-side-step-active" : "bc-side-step",
            },
              h("span", null, String(index + 1)),
              h("div", null,
                h("strong", null, step.title),
                h("small", null, kindLabel(step.kind))
              ),
              h("em", { className: statusClass(step.status) }, statusLabel(step.status))
            );
          })
        ),
        h("div", { className: "bc-side-actions" },
          current && current.external_url ? h("a", {
            className: "bc-link",
            href: current.external_url,
            target: "_blank",
            rel: "noreferrer",
          }, "打开外部系统") : null,
          h(Button, {
            size: "sm",
            className: "bc-poll-button",
            onClick: poll,
            disabled: busy,
            "aria-busy": busy ? "true" : "false",
          }, "轮询检查"),
          h(Button, {
            size: "sm",
            variant: "outline",
            onClick: function () { askChat("请查看当前信贷业务 " + caseData.id + " 的执行计划，并告诉我现在卡在哪一步、我应该做什么。"); },
          }, "让模型说明下一步"),
          h(Button, { size: "sm", variant: "outline", onClick: function () { hideCase(caseData.id); } }, "隐藏")
        )
      );
    }

    return h("div", { className: "bc-side-card" },
      h("div", { className: "bc-side-head bc-side-card-head" },
        h("div", null,
          h("div", { className: "bc-eyebrow" }, "Current chat credit flows"),
          h("strong", null, "本轮对话信贷流程")
        ),
        h(Button, { size: "sm", variant: "outline", onClick: function () { load(currentSessionId()); } }, "刷新")
      ),
      cases.length ? cases.map(renderCase) : h("p", { className: "bc-side-hint" }, "正在等待本轮对话中的信贷工具调用。"),
      hiddenCases.length ? h("div", { className: "bc-hidden-flows" },
        h("div", { className: "bc-hidden-head" },
          h("span", null, "已隐藏 " + hiddenCases.length + " 个信贷流程"),
          h(Button, { size: "sm", variant: "outline", onClick: restoreAllHidden }, "全部显示")
        ),
        hiddenCases.map(function (caseData) {
          return h("div", { className: "bc-hidden-flow", key: "hidden-" + caseData.id },
            h("span", null, caseData.id + " · " + caseData.applicant_name),
            h(Button, { size: "sm", variant: "outline", onClick: function () { restoreCase(caseData.id); } }, "显示")
          );
        })
      ) : !cases.length && recoverableCases.length ? h("div", { className: "bc-hidden-flows" },
        h("div", { className: "bc-hidden-head" },
          h("span", null, "当前会话没有显示的信贷流程")
        ),
        recoverableCases.map(function (caseData) {
          return h("div", { className: "bc-hidden-flow", key: "recoverable-" + caseData.id },
            h("span", null, caseData.id + " · " + caseData.applicant_name),
            h(Button, { size: "sm", variant: "outline", onClick: function () { restoreCase(caseData.id); } }, "显示")
          );
        })
      ) : null
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
    useEffect(function () {
      if (!selectedId) return;
      const timer = window.setInterval(function () {
        api("/poll", { method: "POST" }).then(function () {
          return reload(selectedId);
        }).catch(function (err) {
          setError(err.message || String(err));
        });
      }, 5000);
      return function () { window.clearInterval(timer); };
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
          onMockExternalTask: function (task) {
            mutate(function () {
              return api("/cases/" + encodeURIComponent(selectedId) + "/mock/external-task-done", {
                method: "POST",
                body: JSON.stringify({ task: task }),
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
    if (typeof window.__HERMES_PLUGINS__.registerSlot === "function") {
      window.__HERMES_PLUGINS__.registerSlot("bank-credit-mvp", "chat:sidebar", SidebarPlan);
    }
  }
})();
