import { useEffect, useState } from "react";

interface MetricsList {
  metric_names: string[];
}

interface Props {
  onSelect: (deviceId: string) => void;
  deviceId: string;
}

export function MetricsDropdown(props: Props) {
  const [metrics, setMetrics] = useState([] as string[]);
  const [selected, setSelected] = useState("");
  useEffect(() => {
    async function fetchData() {
      const devicesRes = await fetch(
        `http://localhost:8000/api/v1/devices/${props.deviceId}/metrics`
      );
      const data = (await devicesRes.json()) as MetricsList;
      setMetrics(data.metric_names);
    }
    void fetchData();
  }, [props.deviceId]);
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelected(value);
    props.onSelect(value);
  };
  return (
    <>
      <p>
        <label>Select Metric</label>
      </p>
      <select value={selected} onChange={handleChange}>
        {selected || <option value="">--- Choose a metric ---</option>}
        {metrics.map((metric) => (
          <option key={metric} value={metric}>
            {metric}
          </option>
        ))}
      </select>
    </>
  );
}
