import { useEffect, useState } from "react";

interface LatestMetricsData {
  metrics: Record<string, number>;
  timestamp: number;
}

interface Props {
  deviceId: string;
}

export function LatestMetrics(props: Props) {
  const [metrics, setMetrics] = useState<LatestMetricsData["metrics"] | null>(
    null
  );
  const [timestamp, setTimestamp] = useState(0);
  useEffect(() => {
    async function fetchData() {
      try {
        const devicesRes = await fetch(
          `http://localhost:8000/api/v1/devices/${props.deviceId}/metrics/latest`
        );
        const data = (await devicesRes.json()) as LatestMetricsData;
        console.log(data);
        setMetrics(data.metrics);
        setTimestamp(data.timestamp);
      } catch {
        setMetrics(null);
      }
    }
    void fetchData();
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
