import { useEffect, useState } from "react";
import api from "../services/api";
import type { TransactionSummary } from "../types/transaction";

function Dashboard() {
  const [summary, setSummary] = useState<TransactionSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSummary() {
      try {
        const response = await api.get<TransactionSummary>(
          "/transactions/summary"
        );

        setSummary(response.data);
      } catch (error) {
        console.error("Failed to fetch summary:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchSummary();
  }, []);

  if (loading) {
    return <div>Loading dashboard...</div>;
  }

  if (!summary) {
    return <div>Unable to load dashboard.</div>;
  }

  return (
    <main>
      <h1>BudgetPilot</h1>

      <section>
        <div>
          <h2>Income</h2>
          <p>₹{summary.total_income.toFixed(2)}</p>
        </div>

        <div>
          <h2>Expenses</h2>
          <p>₹{summary.total_expenses.toFixed(2)}</p>
        </div>

        <div>
          <h2>Balance</h2>
          <p>₹{summary.balance.toFixed(2)}</p>
        </div>
      </section>

      <section>
        <h2>Spending by Category</h2>

        {summary.spending_by_category.map((item) => (
          <div key={item.category}>
            <span>{item.category}</span>
            <span>₹{item.amount.toFixed(2)}</span>
          </div>
        ))}
      </section>
    </main>
  );
}

export default Dashboard;