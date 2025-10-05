import { useState } from "react";
import { DeviceDropdown } from "./DeviceDropdown";
import { LatestMetrics } from "./LatestMetrics";
import { MetricsDropdown } from "./MetricsDropdown";
import { MetricsTimeSeries } from "./MetricsTimeSeries";

function App() {
  const [selectedDevice, setSelectedDevice] = useState("");
  const [selectedMetric, setSelectedMetric] = useState("");
  const handleDeviceSelection = (deviceId: string) => {
    setSelectedDevice(deviceId);
  };
  const handleMetricSelection = (metric: string) => {
    setSelectedMetric(metric);
  };
  return (
    <>
      <h1>Monitoring</h1>
      <DeviceDropdown onSelect={handleDeviceSelection} />
      <div>{selectedDevice && <LatestMetrics deviceId={selectedDevice} />}</div>
      <div>
        {selectedDevice && (
          <MetricsDropdown
            deviceId={selectedDevice}
            onSelect={handleMetricSelection}
          />
        )}
      </div>
      <div>
        {selectedMetric && (
          <MetricsTimeSeries
            deviceId={selectedDevice}
            metricKey={selectedMetric}
          />
        )}
      </div>
    </>
  );
}

export default App;
