import { useEffect, useState } from "react";
import api from "../services/api";
import type { TransactionSummary } from "../types/transaction";
import SummaryCards from "../components/dashboard/SummaryCards";
import CategoryBreakdown from "../components/dashboard/CategoryBreakdown";

interface Props {
  /** Incremented when a transaction is added elsewhere (e.g. from Transactions view) */
  refreshKey?: number;
}

function Dashboard({ refreshKey = 0 }: Props) {
  const [summary, setSummary] = useState<TransactionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(false);

    api
      .get<TransactionSummary>("/transactions/summary")
      .then((res) => setSummary(res.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [refreshKey]);

  if (loading) {
    return <p className="loading-text">Loading dashboard...</p>;
  }

  if (error || !summary) {
    return <p className="empty-state">Unable to load dashboard. Is the backend running?</p>;
  }

  return (
    <div className="dashboard">
      <div className="section-header">
        <h2>Overview</h2>
        <p>Your financial snapshot</p>
      </div>

      <SummaryCards summary={summary} />

      <div className="dashboard-bottom">
        <CategoryBreakdown categories={summary.spending_by_category} />
      </div>
    </div>
  );
}

export default Dashboard;
