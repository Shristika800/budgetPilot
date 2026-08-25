import { useState } from "react";
import { PlusCircle } from "lucide-react";
import api from "../../services/api";

interface Props {
  onAdded: () => void;
}

interface FormState {
  description: string;
  amount: string;
  transaction_type: "income" | "expense";
  transaction_date: string;
}

function today() {
  return new Date().toISOString().slice(0, 16); // "YYYY-MM-DDTHH:MM"
}

function AddTransactionForm({ onAdded }: Props) {
  const [form, setForm] = useState<FormState>({
    description: "",
    amount: "",
    transaction_type: "expense",
    transaction_date: today(),
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const amount = parseFloat(form.amount);

    if (!form.description.trim()) {
      setError("Description is required.");
      return;
    }
    if (isNaN(amount) || amount <= 0) {
      setError("Enter a valid amount greater than 0.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await api.post("/transactions/", {
        description: form.description.trim(),
        amount,
        transaction_type: form.transaction_type,
        transaction_date: new Date(form.transaction_date).toISOString(),
      });

      // Reset form
      setForm({
        description: "",
        amount: "",
        transaction_type: "expense",
        transaction_date: today(),
      });

      onAdded();
    } catch {
      setError("Failed to add transaction. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="add-transaction-form" onSubmit={handleSubmit} noValidate>
      <h3>Add Transaction</h3>

      {error && <p className="form-error" role="alert">{error}</p>}

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="description">Description</label>
          <input
            id="description"
            name="description"
            type="text"
            placeholder="e.g. Swiggy dinner"
            value={form.description}
            onChange={handleChange}
            maxLength={500}
            autoComplete="off"
          />
        </div>

        <div className="form-group form-group-sm">
          <label htmlFor="amount">Amount (₹)</label>
          <input
            id="amount"
            name="amount"
            type="number"
            placeholder="0.00"
            min="0.01"
            step="0.01"
            value={form.amount}
            onChange={handleChange}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group form-group-sm">
          <label htmlFor="transaction_type">Type</label>
          <select
            id="transaction_type"
            name="transaction_type"
            value={form.transaction_type}
            onChange={handleChange}
          >
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="transaction_date">Date</label>
          <input
            id="transaction_date"
            name="transaction_date"
            type="datetime-local"
            value={form.transaction_date}
            onChange={handleChange}
          />
        </div>
      </div>

      <button
        type="submit"
        className="submit-btn"
        disabled={submitting}
        aria-busy={submitting}
      >
        <PlusCircle size={16} />
        {submitting ? "Adding..." : "Add Transaction"}
      </button>
    </form>
  );
}

export default AddTransactionForm;
