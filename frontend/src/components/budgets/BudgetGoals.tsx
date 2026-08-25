import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PlusCircle, Trash2 } from "lucide-react";
import api from "../../services/api";
import type { BudgetProgress } from "../../types/transaction";

const CATEGORIES = [
  "food", "groceries", "transport", "shopping", "utilities",
  "entertainment", "health", "education", "travel", "electronics",
  "personal_care", "housing", "other",
];

function BudgetGoals() {
  const [budgets, setBudgets] = useState<BudgetProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [limit, setLimit] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function fetchBudgets() {
    setLoading(true);
    api
      .get<BudgetProgress[]>("/budgets/")
      .then((r) => setBudgets(r.data))
      .catch(() => setBudgets([]))
      .finally(() => setLoading(false));
  }

  useEffect(() => { fetchBudgets(); }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    const val = parseFloat(limit);
    if (isNaN(val) || val <= 0) { setError("Enter a valid limit."); return; }
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/budgets/", { category, monthly_limit: val });
      setShowForm(false);
      setLimit("");
      fetchBudgets();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Failed to add budget.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    await api.delete(`/budgets/${id}`);
    fetchBudgets();
  }

  function barColor(pct: number) {
    if (pct >= 100) return "#dc2626";
    if (pct >= 80) return "#f97316";
    return "#6366f1";
  }

  return (
    <div className="budget-goals">
      <div className="section-header" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2>Budget Goals</h2>
          <p>Set monthly limits per category</p>
        </div>
        <button className="submit-btn" onClick={() => setShowForm((v) => !v)}>
          <PlusCircle size={16} />
          {showForm ? "Cancel" : "Add Budget"}
        </button>
      </div>

      {/* Add form */}
      <AnimatePresence>
        {showForm && (
          <motion.form
            className="add-transaction-form"
            onSubmit={handleAdd}
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
          >
            {error && <p className="form-error">{error}</p>}
            <div className="form-row">
              <div className="form-group">
                <label>Category</label>
                <select value={category} onChange={(e) => setCategory(e.target.value)}>
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div className="form-group form-group-sm">
                <label>Monthly Limit (₹)</label>
                <input
                  type="number" min="1" step="0.01"
                  placeholder="e.g. 3000"
                  value={limit}
                  onChange={(e) => setLimit(e.target.value)}
                />
              </div>
            </div>
            <button type="submit" className="submit-btn" disabled={submitting}>
              {submitting ? "Saving..." : "Save Budget"}
            </button>
          </motion.form>
        )}
      </AnimatePresence>

      {/* Budget list */}
      {loading ? (
        <p className="loading-text">Loading budgets...</p>
      ) : budgets.length === 0 ? (
        <p className="empty-state">No budgets set yet. Add one to start tracking.</p>
      ) : (
        <div className="budget-list">
          {budgets.map((b, i) => (
            <motion.div
              key={b.id}
              className="budget-card"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <div className="budget-card-header">
                <span className="budget-category">
                  {b.category.charAt(0).toUpperCase() + b.category.slice(1)}
                </span>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span className="budget-amounts">
                    <span style={{ color: barColor(b.percent_used), fontWeight: 700 }}>
                      ₹{Number(b.spent).toFixed(0)}
                    </span>
                    <span className="budget-limit"> / ₹{Number(b.monthly_limit).toFixed(0)}</span>
                  </span>
                  <button
                    className="icon-btn"
                    onClick={() => handleDelete(b.id)}
                    aria-label="Delete budget"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>

              <div className="budget-bar-track">
                <motion.div
                  className="budget-bar-fill"
                  style={{ background: barColor(b.percent_used) }}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(b.percent_used, 100)}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                />
              </div>

              <div className="budget-footer">
                <span className="budget-pct" style={{ color: barColor(b.percent_used) }}>
                  {b.percent_used.toFixed(1)}% used
                </span>
                {b.remaining >= 0 ? (
                  <span className="budget-remaining">₹{Number(b.remaining).toFixed(0)} left</span>
                ) : (
                  <span className="budget-over">₹{Math.abs(Number(b.remaining)).toFixed(0)} over budget!</span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

export default BudgetGoals;
