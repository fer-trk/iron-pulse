const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const vm = require("node:vm");

function environment(file) {
  const elements = new Map();
  const document = {
    addEventListener() {},
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, {
        value: "", innerHTML: "", options: [], selectedIndex: 0,
        classList: { add() {}, remove() {} },
        replaceChildren(...options) { this.options = options; },
        add(option) { this.options.push(option); },
      });
      return elements.get(id);
    },
  };
  const context = vm.createContext({ document, console, Date, escapeHtml: value => String(value),
    Option: function(text, value) { this.text = text; this.value = value; this.dataset = {}; },
    bootstrap: { Modal: class { show() {} } },
    getData: async path => {
      assert.ok(path.startsWith("/plans/"));
      return [{ id: 42, name: "Actual custom plan", price: "49.99", duration_days: 45 }];
    },
    getAllData: async path => path.startsWith("/memberships/")
      ? [{ id: 9, member_id: 17, plan_id: 42, status: "pending" }]
      : [{ id: 17, first_name: "Ana", last_name: "Test", is_active: true }],
  });
  vm.runInContext(readFileSync(file, "utf8"), context);
  return { context, document };
}

test("membership selector uses actual plan IDs, price and duration", async () => {
  const { context, document } = environment("Frontend/js/memberships.js");
  await vm.runInContext("openAddModal()", context);
  const options = document.getElementById("membershipPlanId").options;
  assert.equal(options.length, 2);
  assert.equal(options[1].value, 42);
  assert.equal(options[1].dataset.price, "49.99");
  assert.equal(options[1].dataset.duration, 45);
});

test("payment selector uses custom catalog instead of invented prices", async () => {
  const { context, document } = environment("Frontend/js/payments.js");
  await vm.runInContext("openAddModal()", context);
  const html = document.getElementById("paymentMembershipId").innerHTML;
  assert.match(html, /Actual custom plan/);
  assert.match(html, /49.99/);
  assert.doesNotMatch(html, /Mensual|Semestral|Anual/);
});


test("apostrophes and HTML in member names do not break edit actions", () => {
  const { context, document } = environment("Frontend/js/members.js");
  context.escapeHtml = value => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll("'", "&#39;");
  vm.runInContext(`renderMembersTable([{id:17,first_name:"Ana",last_name:"O'Brien <x>",email:"ana@example.com",phone:"",is_active:true}])`, context);
  const html = document.getElementById("members-table-container").innerHTML;
  assert.match(html, /O&#39;Brien &lt;x&gt;/);
  assert.match(html, /editRenderedRecord\(17\)/);
  vm.runInContext("editRenderedRecord(17)", context);
  assert.equal(document.getElementById("editMemberLastName").value, "O'Brien <x>");
});

test("login preserves password spaces and uses a single token key", async () => {
  const { context, document } = environment("Frontend/js/auth.js");
  const stored = new Map(); let submitted;
  context.API_BASE_URL = "/api/v1";
  context.URLSearchParams = URLSearchParams;
  context.window = {location:{pathname:"/login.html",href:""}};
  context.localStorage = {setItem:(key,value)=>stored.set(key,value)};
  context.fetch = async (url, options) => { submitted = options.body; return {ok:true,json:async()=>({access_token:"test-token",token_type:"bearer"})}; };
  document.getElementById("username").value = "admin";
  document.getElementById("password").value = "  password-with-spaces  ";
  await vm.runInContext("handleLogin({preventDefault(){}})", context);
  assert.equal(submitted.get("password"), "  password-with-spaces  ");
  assert.equal(stored.get("access_token"), "test-token");
  assert.equal(stored.has("ironPulseToken"), false);
});
