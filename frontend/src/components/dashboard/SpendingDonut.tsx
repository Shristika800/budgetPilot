import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { SpendingCategory } from "../../types/transaction";

interface Props {
  categories: SpendingCategory[];
}

const COLORS = [
  "#6366f1", "#f97316", "#10b981", "#3b82f6", "#ec4899",
  "#f59e0b", "#84cc16", "#06b6d4", "#a855f7", "#64748b",
  "#e11d48", "#0ea5e9",
];

function SpendingDonut({ categories }: Props) {
  if (categories.length === 0) {
    return (
      <div className="card">
        <p className="card-label">Spending Breakdown</p>
        <p className="empty-state">No expense data yet.</p>
      </div>
    );
  }

  const data = categories.map((c) => ({
    name: c.category.charAt(0).toUpperCase() + c.category.slice(1),
    value: Number(c.amount),
  }));

  return (
    <div className="card donut-card">
      <p className="card-label">Spending Breakdown</p>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={65}
            outerRadius={95}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => [`₹${value.toFixed(2)}`]}
            contentStyle={{
              background: "var(--card-bg)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 13,
            }}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 13 }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export default SpendingDonut;
