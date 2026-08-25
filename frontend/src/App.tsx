import { useState } from "react";
import { LayoutDashboard, List, MessageCircle } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import TransactionList from "./components/transactions/TransactionList";
import AddTransactionForm from "./components/transactions/AddTransactionForm";
import ChatPanel from "./components/chat/ChatPanel";
import "./App.css";

type View = "dashboard" | "transactions" | "chat";

const NAV_ITEMS: { id: View; label: string; icon: React.ReactNode }[] = [
  { id: "dashboard", label: "Dashboard", icon: <LayoutDashboard size={18} /> },
  { id: "transactions", label: "Transactions", icon: <List size={18} /> },
  { id: "chat", label: "Chat", icon: <MessageCircle size={18} /> },
];

function App() {
  const [view, setView] = useState<View>("dashboard");
  // Incrementing this tells Dashboard and TransactionList to refetch
  const [refreshKey, setRefreshKey] = useState(0);

  function handleTransactionAdded() {
    setRefreshKey((k) => k + 1);
  }

  return (
    <div className="app">
      {/* Sidebar */}
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
      </aside>

      {/* Main content */}
      <main className="main">
        {view === "dashboard" && (
          <Dashboard refreshKey={refreshKey} />
        )}

        {view === "transactions" && (
          <div className="transactions-view">
            <div className="section-header">
              <h2>Transactions</h2>
              <p>Manage and review your transactions</p>
            </div>

            <AddTransactionForm onAdded={handleTransactionAdded} />
            <TransactionList refreshKey={refreshKey} />
          </div>
        )}

        {view === "chat" && (
          <div className="chat-view">
            <div className="section-header">
              <h2>Chat</h2>
              <p>Ask anything about your finances</p>
            </div>

            <ChatPanel />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
