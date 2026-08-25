import type { SpendingCategory } from "../../types/transaction";

interface Props {
  categories: SpendingCategory[];
}

const CATEGORY_COLORS: Record<string, string> = {
  food: "#f97316",
  groceries: "#84cc16",
  transport: "#3b82f6",
  shopping: "#a855f7",
  utilities: "#06b6d4",
  entertainment: "#ec4899",
  health: "#10b981",
  education: "#f59e0b",
  travel: "#6366f1",
  electronics: "#64748b",
  personal_care: "#e11d48",
  housing: "#0ea5e9",
  other: "#94a3b8",
  uncategorized: "#cbd5e1",
};

function CategoryBreakdown({ categories }: Props) {
  if (categories.length === 0) {
    return (
      <div className="card">
        <p className="card-label">Spending by Category</p>
        <p className="empty-state">No expense data yet.</p>
      </div>
    );
  }

  const max = Math.max(...categories.map((c) => Number(c.amount)));

  return (
    <div className="card category-breakdown">
      <p className="card-label">Spending by Category</p>

      <div className="category-list">
        {categories.map((item) => {
          const pct = max > 0 ? (Number(item.amount) / max) * 100 : 0;
          const color = CATEGORY_COLORS[item.category] ?? CATEGORY_COLORS.other;

          return (
            <div key={item.category} className="category-row">
              <div className="category-meta">
                <span className="category-dot" style={{ background: color }} />
                <span className="category-name">{item.category}</span>
                <span className="category-amount">₹{Number(item.amount).toFixed(2)}</span>
              </div>
              <div className="category-bar-track">
                <div
                  className="category-bar-fill"
                  style={{ width: `${pct}%`, background: color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default CategoryBreakdown;
