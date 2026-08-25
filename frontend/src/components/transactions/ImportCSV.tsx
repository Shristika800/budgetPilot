import { useRef, useState } from "react";
import { Upload, CheckCircle, XCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import api from "../../services/api";

interface ImportResult {
  imported: number;
  skipped: number;
  errors: { row: number; error: string }[];
}

interface Props {
  onImported: () => void;
}

function ImportCSV({ onImported }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function uploadFile(file: File) {
    if (!file.name.endsWith(".csv")) {
      setError("Only .csv files are accepted.");
      return;
    }
    setLoading(true);
    setResult(null);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post<ImportResult>("/transactions/import", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
      if (res.data.imported > 0) onImported();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Import failed. Please check your file.");
    } finally {
      setLoading(false);
    }
  }

  function handleFiles(files: FileList | null) {
    if (files && files[0]) uploadFile(files[0]);
  }

  return (
    <div className="import-csv-wrapper">
      <div
        className={`drop-zone ${dragging ? "drop-zone-active" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
        role="button"
        tabIndex={0}
        aria-label="Upload CSV file"
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      >
        <Upload size={28} className="drop-icon" />
        <p className="drop-title">{loading ? "Importing..." : "Drop your CSV here or click to upload"}</p>
        <p className="drop-hint">Required columns: description, amount, transaction_type, transaction_date</p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          style={{ display: "none" }}
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            className="import-error"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <XCircle size={16} /> {error}
          </motion.div>
        )}

        {result && (
          <motion.div
            className="import-result"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <div className="import-result-row">
              <CheckCircle size={16} color="#16a34a" />
              <span>{result.imported} transactions imported successfully</span>
            </div>
            {result.skipped > 0 && (
              <div className="import-result-row">
                <XCircle size={16} color="#dc2626" />
                <span>{result.skipped} rows skipped</span>
              </div>
            )}
            {result.errors.length > 0 && (
              <div className="import-errors-detail">
                {result.errors.map((e) => (
                  <p key={e.row} className="import-error-item">Row {e.row}: {e.error}</p>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ImportCSV;
