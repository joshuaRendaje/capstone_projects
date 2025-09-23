import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

function App() {
  const [latest, setLatest] = useState({});
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const res = await fetch("http://localhost:8000/latest-reading");
        const json = await res.json();

        // Ensure timestamp exists (fallback: local time)
        const reading = {
          ...json,
          timestamp: json.timestamp || new Date().toLocaleTimeString(),
          temperature: Number(json.temperature),
          tds: Number(json.tds),
          turbidity_ntu: Number(json.turbidity_ntu),
        };

        setLatest(reading);

        // Append to history with limit of 20
        setHistory((prev) => {
          const newHistory = [...prev, reading];
          return newHistory.slice(-20);
        });
      } catch (err) {
        console.error("❌ Error fetching latest:", err);
      }
    };

    fetchLatest();
    const interval = setInterval(fetchLatest, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold text-center mb-8 tracking-wide">
        Oyster AI Monitoring Dashboard
      </h1>

      {/* Graph Section */}
      <div className="bg-gray-800 rounded-2xl shadow-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" stroke="#555" />
            <XAxis dataKey="timestamp" stroke="#aaa" />
            <YAxis stroke="#aaa" />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="temperature"
              stroke="#f87171"
              dot={false}
              name="🌡 Temp (°C)"
            />
            <Line
              type="monotone"
              dataKey="tds"
              stroke="#34d399"
              dot={false}
              name="🧂 TDS"
            />
            <Line
              type="monotone"
              dataKey="turbidity_ntu"
              stroke="#fbbf24"
              dot={false}
              name="🌫 Turbidity"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Live Readings */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SensorCard
          label="🌡 Temp (°C)"
          value={latest.temperature}
          note={latest.temperature_status}
          color="text-red-400"
        />
        <SensorCard
          label="🧂 TDS"
          value={latest.tds}
          note={latest.tds_status}
          color="text-green-400"
        />
        <SensorCard
          label="🌫 Turbidity (NTU)"
          value={latest.turbidity_ntu}
          note={latest.turbidity_status}
          color="text-yellow-400"
        />
      </div>

      {/* Timestamp */}
      <p className="text-center text-gray-400 text-sm mt-6">
        ⏱ Last updated: {latest.timestamp || "--"}
      </p>
    </div>
  );
}

function SensorCard({ label, value, note, color }) {
  return (
    <div className="bg-gray-800 rounded-xl p-4 text-center shadow-md">
      <p className="text-sm text-gray-400">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {value !== undefined ? value : "--"}
      </p>
      {note && <p className="text-xs text-gray-500 mt-1">{note}</p>}
    </div>
  );
}

export default App;
