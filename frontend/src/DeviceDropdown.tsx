import { useEffect, useState } from "react";

interface DevicesList {
  devices: string[];
}

interface Props {
  onSelect: (deviceId: string) => void;
}

export function DeviceDropdown(props: Props) {
  const [devices, setDevices] = useState([] as string[]);
  const [selected, setSelected] = useState("");
  useEffect(() => {
    async function fetchData() {
      const devicesRes = await fetch("http://localhost:8000/api/v1/devices");
      const data = (await devicesRes.json()) as DevicesList;
      setDevices(data.devices);
    }
    void fetchData();
  }, []);
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelected(value);
    props.onSelect(value);
  };
  return (
    <>
      <p>
        <label>Select Device</label>
      </p>
      <select value={selected} onChange={handleChange}>
        {selected || <option value="">--- Choose a device ---</option>}
        {devices.map((device) => (
          <option key={device} value={device}>
            {device}
          </option>
        ))}
      </select>
    </>
  );
}
