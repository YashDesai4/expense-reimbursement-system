import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function App() {
  const [token, setToken] = useState(localStorage.getItem("expense-token"));
  const [user, setUser] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [progress, setProgress] = useState({});
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  async function refresh() {
    const [me, list, counts] = await Promise.all([
      fetch(`${API}/api/me`, { headers }).then((r) => r.json()),
      fetch(`${API}/api/expenses`, { headers }).then((r) => r.json()),
      fetch(`${API}/api/progress`, { headers }).then((r) => r.json())
    ]);
    setUser(me); setExpenses(list); setProgress(counts);
  }
  useEffect(() => { if (token) refresh().catch(() => setToken(null)); }, [token]);

  async function login(event) {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(event.currentTarget));
    const response = await fetch(`${API}/api/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await response.json();
    if (data.access_token) { localStorage.setItem("expense-token", data.access_token); setToken(data.access_token); }
  }
  async function submit(event) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    values.total = Number(values.total);
    await fetch(`${API}/api/expenses`, { method: "POST", headers, body: JSON.stringify(values) });
    event.currentTarget.reset(); refresh();
  }
  async function uploadReceipt(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${API}/api/expenses/from-receipt`, {
      method: "POST", headers: { Authorization: `Bearer ${token}` }, body: form
    });
    if (!response.ok) {
      const error = await response.json();
      return alert(error.detail ?? "Receipt extraction failed");
    }
    event.currentTarget.reset(); refresh();
  }
  async function decide(id, decision) {
    await fetch(`${API}/api/expenses/${id}/decision`, { method: "PATCH", headers, body: JSON.stringify({ decision, note: `${decision} in dashboard` }) });
    refresh();
  }

  if (!token) return <div className="login"><form onSubmit={login}><div className="logo">ReimburseFlow</div><h1>Expense workspace</h1><input name="email" defaultValue="employee@example.com"/><input name="password" type="password" defaultValue="employee123"/><button>Sign in</button><small>Use manager@example.com / manager123 for approvals.</small></form></div>;
  if (!user) return <div className="login">Loading…</div>;
  return <div className="shell"><aside><div className="logo">ReimburseFlow</div><p>{user.name}</p><span>{user.role}</span><button className="ghost" onClick={() => { localStorage.removeItem("expense-token"); setToken(null); }}>Sign out</button></aside><main>
    <header><div><small>EXPENSE OPERATIONS</small><h1>{user.role === "manager" ? "Approval queue" : "My reimbursements"}</h1></div></header>
    <section className="progress">{["draft","submitted","approved","rejected"].map((state) => <div key={state}><span>{state}</span><b>{progress[state] ?? 0}</b></div>)}</section>
    {user.role === "employee" && <><form className="new" onSubmit={submit}><h2>Submit an expense</h2><input name="vendor" placeholder="Vendor" required/><input name="expense_date" type="date" required/><input name="total" type="number" min="0.01" step="0.01" placeholder="Total" required/><input name="description" placeholder="Description (used for smart category)"/><button>Submit</button></form><form className="receipt" onSubmit={uploadReceipt}><b>Or extract a receipt with DONUT</b><input name="receipt" type="file" accept="image/png,image/jpeg" required/><input name="description" placeholder="Optional description"/><button>Extract & submit</button></form></>}
    <section className="table"><div className="row heading"><span>Vendor</span><span>Date</span><span>Category</span><span>Total</span><span>Status</span><span>Action</span></div>{expenses.map((expense) => <div className="row" key={expense.id}><b>{expense.vendor}</b><span>{expense.expense_date}</span><span>{expense.category}</span><span>${expense.total.toFixed(2)}</span><span className={`status ${expense.status}`}>{expense.status}</span><span>{user.role === "manager" && expense.status === "submitted" ? <><button onClick={() => decide(expense.id,"approved")}>Approve</button><button className="reject" onClick={() => decide(expense.id,"rejected")}>Reject</button></> : "—"}</span></div>)}</section>
  </main></div>;
}

createRoot(document.getElementById("root")).render(<App/>);
