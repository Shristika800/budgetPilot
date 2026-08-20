export type TransactionType = "income" | "expense";

export interface Transaction {
  id: number;
  description: string;
  amount: number;
  category: string | null;
  confidence: number | null;
  transaction_type: TransactionType;
  transaction_date: string;
  created_at: string;
}

export interface SpendingCategory {
  category: string;
  amount: number;
}

export interface TransactionSummary {
  total_income: number;
  total_expenses: number;
  balance: number;
  spending_by_category: SpendingCategory[];
}
