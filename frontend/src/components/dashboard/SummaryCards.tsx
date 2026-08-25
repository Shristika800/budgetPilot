import type { TransactionSummary } from "../../types/transaction";

interface Props {
  summary: TransactionSummary;
}

function SummaryCards({ summary }: Props) {
  return (
    <div className="cards">
      <div className="card">
        <p className="card-label">Total Income</p>
        <p className="card-value income">₹{Number(summary.total_income).toFixed(2)}</p>
      </div>

      <div className="card">
        <p className="card-label">Total Expenses</p>
        <p className="card-value expense">₹{Number(summary.total_expenses).toFixed(2)}</p>
      </div>

      <div className="card">
        <p className="card-label">Balance</p>
        <p className={`card-value ${Number(summary.balance) >= 0 ? "income" : "expense"}`}>
          ₹{Number(summary.balance).toFixed(2)}
        </p>
      </div>
    </div>
  );
}

export default SummaryCards;
