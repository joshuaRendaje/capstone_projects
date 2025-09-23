import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";
import { Card, CardContent } from "@/components/ui/card";

export default function Dashboard() {
  const [latest, setLatest] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://localhost:8000/latest-reading");
        if (!res.ok) {
          throw new Error("API error: " + res.status);
        }
        const json = await res.json();
        setLatest(json);

        // update history (time-series graph)
        setHistory((prev) => {
          const newHistory = [...prev, json];
          return newHistory.slice(-20); // keep last 20 readings
        });
      } catch (err) {
        console.error("❌ Error fetching data:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // refresh every 5s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {latest && (
          <>
            {/* Temperature */}
            <Card className="shadow-lg rounded-2xl">
              <CardContent className="p-4">
                <h2 className="font-bold text-lg">🌡 Temperature</h2>
                <p className="text-xl">{latest.temperature} °C</p>
                <p className="text-green-600">{latest.temperature_status}</p>
                <p className="text-gray-500 text-sm">Level: {latest.temperature_level}</p>
              </CardContent>
            </Card>

            {/* TDS */}
            <Card className="shadow-lg rounded-2xl">
              <CardContent className="p-4">
                <h2 className="font-bold text-lg">💧 TDS</h2>
                <p className="text-xl">{latest.tds} ppm</p>
                <p className="text-red-600">{latest.tds_status}</p>
                <p className="text-gray-500 text-sm">Level: {latest.tds_level}</p>
              </CardContent>
            </Card>

            {/* Turbidity */}
            <Card className="shadow-lg rounded-2xl">
              <CardContent className="p-4">
                <h2 className="font-bold text-lg">🌊 Turbidity</h2>
                <p className="text-xl">{latest.turbidity_ntu} NTU</p>
                <p className="text-green-600">{latest.turbidity_status}</p>
                <p className="text-gray-500 text-sm">Level: {latest.turbidity_level}</p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Time-Series Graph */}
      <div className="col-span-1 lg:col-span-2 bg-white shadow-lg rounded-2xl p-4">
        <h2 className="text-lg font-bold mb-4">📈 Water Quality Trends</h2>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" tick={{ fontSize: 12 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="temperature"
              stroke="#ff7300"
              dot={false}
              name="Temperature (°C)"
            />
            <Line
              type="monotone"
              dataKey="tds"
              stroke="#387908"
              dot={false}
              name="TDS (ppm)"
            />
            <Line
              type="monotone"
              dataKey="turbidity_ntu"
              stroke="#1f77b4"
              dot={false}
              name="Turbidity (NTU)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
