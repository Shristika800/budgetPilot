import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import api from "../services/api";
import type { TransactionSummary } from "../types/transaction";
import SummaryCards from "../components/dashboard/SummaryCards";
import SpendingDonut from "../components/dashboard/SpendingDonut";
import TrendChart from "../components/dashboard/TrendChart";

interface Props {
  refreshKey?: number;
}

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

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

  if (loading) return <p className="loading-text">Loading dashboard...</p>;
  if (error || !summary) return <p className="empty-state">Unable to load dashboard. Is the backend running?</p>;

  return (
    <motion.div className="dashboard" variants={container} initial="hidden" animate="show">
      <motion.div variants={item} className="section-header">
        <h2>Overview</h2>
        <p>Your financial snapshot</p>
      </motion.div>

      <motion.div variants={item}>
        <SummaryCards summary={summary} />
      </motion.div>

      <motion.div variants={item} className="dashboard-charts">
        <TrendChart refreshKey={refreshKey} />
        <SpendingDonut categories={summary.spending_by_category} />
      </motion.div>
    </motion.div>
  );
}

export default Dashboard;
