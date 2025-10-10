import { useEffect, useState } from "react";

interface MetricsValuesData {
  metric_values: number[][];
}

interface Props {
  deviceId: string;
  metricKey: string;
}

const REFRESH_MS = 5000; // 5s

export function MetricsTimeSeries(props: Props) {
  const [metrics, setMetrics] = useState<
    { timestamp: number; value: number }[] | null
  >(null);
  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const metricsValuesRes = await fetch(
          `http://localhost:8000/api/v1/devices/${
            props.deviceId
          }/metrics/${props.metricKey.replaceAll("/", "_-_")}/timeseries`
        );
        const data = (await metricsValuesRes.json()) as MetricsValuesData;
        if (cancelled) return;
        setMetrics(
          data.metric_values.map((dataPoint) => ({
            timestamp: dataPoint[0],
            value: dataPoint[1],
          }))
        );
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
  }, [props.deviceId, props.metricKey]);

  const formatTime = (timestamp: number) =>
    timestamp ? new Date(timestamp * 1000).toLocaleString() : "";

  return (
    <>
      {metrics && (
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((dataPoint) => (
              <tr key={dataPoint.timestamp}>
                <td>{formatTime(dataPoint.timestamp)}</td>
                <td>{dataPoint.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
