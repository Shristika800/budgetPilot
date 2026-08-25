import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import api from "../../services/api";
import type { TrendPoint } from "../../types/transaction";

interface Props {
  days?: number;
  refreshKey?: number;
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function TrendChart({ days = 30, refreshKey = 0 }: Props) {
  const [data, setData] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<TrendPoint[]>("/transactions/trends", { params: { days } })
      .then((res) => setData(res.data))
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [days, refreshKey]);

  if (loading) return <p className="loading-text">Loading chart...</p>;

  if (data.length === 0) {
    return (
      <div className="card">
        <p className="card-label">Spending Trend ({days} days)</p>
        <p className="empty-state">No expense data in this period yet.</p>
      </div>
    );
  }

  const formatted = data.map((d) => ({ ...d, label: formatDate(d.date) }));

  return (
    <div className="card trend-chart-card">
      <p className="card-label">Spending Trend — last {days} days</p>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={formatted} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 12, fill: "var(--text-muted)" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "var(--text-muted)" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `₹${v}`}
          />
          <Tooltip
            formatter={(value: number) => [`₹${value.toFixed(2)}`, "Spent"]}
            contentStyle={{
              background: "var(--card-bg)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 13,
            }}
          />
          <Line
            type="monotone"
            dataKey="amount"
            stroke="#6366f1"
            strokeWidth={2.5}
            dot={{ fill: "#6366f1", r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TrendChart;
