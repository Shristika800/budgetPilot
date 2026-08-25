import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, AlertTriangle } from "lucide-react";
import api from "../../services/api";
import type { Transaction } from "../../types/transaction";

const CATEGORY_COLORS: Record<string, string> = {
  food: "#f97316", groceries: "#84cc16", transport: "#3b82f6",
  shopping: "#a855f7", utilities: "#06b6d4", entertainment: "#ec4899",
  health: "#10b981", education: "#f59e0b", travel: "#6366f1",
  electronics: "#64748b", personal_care: "#e11d48", housing: "#0ea5e9",
  income: "#16a34a", other: "#94a3b8", uncategorized: "#cbd5e1",
};

const PAGE_SIZE = 10;

interface Props {
  refreshKey?: number;
}

function TransactionList({ refreshKey = 0 }: Props) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => { setPage(0); }, [refreshKey]);

  useEffect(() => {
    setLoading(true);
    api
      .get<Transaction[]>("/transactions/", {
        params: { skip: page * PAGE_SIZE, limit: PAGE_SIZE },
      })
      .then((res) => {
        setTransactions(res.data);
        setHasMore(res.data.length === PAGE_SIZE);
      })
      .catch(() => setTransactions([]))
      .finally(() => setLoading(false));
  }, [page, refreshKey]);

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "numeric", month: "short", year: "numeric",
    });
  }

  return (
    <div className="transaction-list-wrapper">
      <div className="section-header"><h3>Transactions</h3></div>

      {loading ? (
        <p className="loading-text">Loading...</p>
      ) : transactions.length === 0 ? (
        <p className="empty-state">No transactions found.</p>
      ) : (
        <div className="transaction-table">
          <div className="transaction-table-head">
            <span>Date</span>
            <span>Description</span>
            <span>Category</span>
            <span>Type</span>
            <span className="align-right">Amount</span>
          </div>

          {transactions.map((t, i) => {
            const color = CATEGORY_COLORS[t.category ?? "uncategorized"] ?? CATEGORY_COLORS.other;
            return (
              <motion.div
                key={t.id}
                className={`transaction-row ${t.is_anomaly ? "transaction-row-anomaly" : ""}`}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                title={t.is_anomaly && t.anomaly_reason ? t.anomaly_reason : undefined}
              >
                <span className="tx-date">{formatDate(t.transaction_date)}</span>

                <span className="tx-desc">
                  {t.is_anomaly && (
                    <AlertTriangle size={13} className="anomaly-icon" title={t.anomaly_reason ?? ""} />
                  )}
                  {t.description}
                </span>

                <span>
                  {t.category ? (
                    <span className="category-badge" style={{ background: `${color}20`, color, border: `1px solid ${color}40` }}>
                      {t.category}
                    </span>
                  ) : (
                    <span className="category-badge uncategorized-badge">—</span>
                  )}
                </span>

                <span>
                  <span className={`type-badge ${t.transaction_type === "income" ? "type-income" : "type-expense"}`}>
                    {t.transaction_type}
                  </span>
                </span>

                <span className={`tx-amount align-right ${t.transaction_type === "income" ? "income" : "expense"}`}>
                  {t.transaction_type === "income" ? "+" : "-"}₹{Number(t.amount).toFixed(2)}
                </span>
              </motion.div>
            );
          })}
        </div>
      )}

      <div className="pagination">
        <button className="page-btn" onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0} aria-label="Previous page">
          <ChevronLeft size={16} />
        </button>
        <span className="page-label">Page {page + 1}</span>
        <button className="page-btn" onClick={() => setPage((p) => p + 1)} disabled={!hasMore} aria-label="Next page">
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

export default TransactionList;
