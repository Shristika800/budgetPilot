import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  LayoutDashboard, List, MessageCircle,
  Target, Sun, Moon,
} from "lucide-react";
import Dashboard from "./pages/Dashboard";
import TransactionList from "./components/transactions/TransactionList";
import AddTransactionForm from "./components/transactions/AddTransactionForm";
import ImportCSV from "./components/transactions/ImportCSV";
import ChatPanel from "./components/chat/ChatPanel";
import BudgetGoals from "./components/budgets/BudgetGoals";
import "./App.css";

type View = "dashboard" | "transactions" | "chat" | "budgets";

const NAV_ITEMS: { id: View; label: string; icon: React.ReactNode }[] = [
  { id: "dashboard",    label: "Dashboard",    icon: <LayoutDashboard size={18} /> },
  { id: "transactions", label: "Transactions", icon: <List size={18} /> },
  { id: "budgets",      label: "Budgets",      icon: <Target size={18} /> },
  { id: "chat",         label: "Chat",         icon: <MessageCircle size={18} /> },
];

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.25 } },
  exit:    { opacity: 0, y: -8,  transition: { duration: 0.15 } },
};

function App() {
  const [view, setView]           = useState<View>("dashboard");
  const [refreshKey, setRefreshKey] = useState(0);
  const [dark, setDark]           = useState(() => {
    return localStorage.getItem("bp-theme") === "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    localStorage.setItem("bp-theme", dark ? "dark" : "light");
  }, [dark]);

  function handleTransactionAdded() {
    setRefreshKey((k) => k + 1);
  }

  return (
    <div className="app">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="logo">
          <h1>Budget<span>Pilot</span></h1>
        </div>

        <nav className="nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${view === item.id ? "active" : ""}`}
              onClick={() => setView(item.id)}
              aria-current={view === item.id ? "page" : undefined}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <button
          className="theme-toggle"
          onClick={() => setDark((d) => !d)}
          aria-label="Toggle dark mode"
        >
          {dark ? <Sun size={16} /> : <Moon size={16} />}
          {dark ? "Light mode" : "Dark mode"}
        </button>
      </aside>

      {/* ── Main ── */}
      <main className="main">
        <AnimatePresence mode="wait">
          {view === "dashboard" && (
            <motion.div key="dashboard" {...pageVariants}>
              <Dashboard refreshKey={refreshKey} />
            </motion.div>
          )}

          {view === "transactions" && (
            <motion.div key="transactions" {...pageVariants} className="transactions-view">
              <div className="section-header">
                <h2>Transactions</h2>
                <p>Manage and review your transactions</p>
              </div>
              <AddTransactionForm onAdded={handleTransactionAdded} />
              <ImportCSV onImported={handleTransactionAdded} />
              <TransactionList refreshKey={refreshKey} />
            </motion.div>
          )}

          {view === "budgets" && (
            <motion.div key="budgets" {...pageVariants}>
              <BudgetGoals />
            </motion.div>
          )}

          {view === "chat" && (
            <motion.div key="chat" {...pageVariants} className="chat-view">
              <div className="section-header">
                <h2>Chat</h2>
                <p>Ask anything about your finances</p>
              </div>
              <ChatPanel />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
