import { useEffect, useState } from "react";

interface LatestMetricsData {
  metrics: Record<string, number>;
  timestamp: number;
}

interface Props {
  deviceId: string;
}

const REFRESH_MS = Number((import.meta as any).env?.VITE_REFRESH_MS ?? 5000);

export function LatestMetrics(props: Props) {
  const [metrics, setMetrics] = useState<LatestMetricsData["metrics"] | null>(
    null
  );
  const [timestamp, setTimestamp] = useState(0);
  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const devicesRes = await fetch(
          `http://localhost:8000/api/v1/devices/${props.deviceId}/metrics/latest`
        );
        const data = (await devicesRes.json()) as LatestMetricsData;
        if (cancelled) return;
        console.log(data);
        setMetrics(data.metrics);
        setTimestamp(data.timestamp);
      } catch {
        if (!cancelled) setMetrics(null);
      }
    }
    void fetchData();
    const id = window.setInterval(fetchData, REFRESH_MS);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [props.deviceId]);

  const formattedTime = timestamp
    ? new Date(timestamp * 1000).toLocaleString()
    : "";

  return (
    <>
      {metrics && (
        <>
          Latest metrics - {formattedTime}
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Info</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(metrics).map((metric) => (
                <tr key={metric[0]}>
                  <td>{metric[0].split("-")[0]}</td>
                  <td>{metric[0].split("-")[1]}</td>
                  <td>{metric[1]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </>
  );
}
