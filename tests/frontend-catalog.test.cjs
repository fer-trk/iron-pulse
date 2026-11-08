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
  const context = vm.createContext({ document, console, Date,
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
