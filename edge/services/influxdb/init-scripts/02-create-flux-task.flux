// InfluxDB Flux Task: 30-second aggregation
// Aggregates raw 1 Hz sensor data into 30-second windows
// Computes mean, stddev, min, max for all sensor tags

option task = {
  name: "30s_sensor_aggregation",
  every: 30s,
  offset: 5s,
}

// Source bucket with raw 1 Hz data
raw_bucket = "pichia_raw"
agg_bucket = "pichia_30s"

// List of all sensor measurements to aggregate
sensors = [
  "pH",
  "DO",
  "OD",
  "Gas_MFC_air",
  "Stir_SP",
  "Stir_torque",
  "Weight",
  "Heater_PID_out",
  "Base_Pump_Rate",
  "broth",           // Temp_Broth
  "ph_probe",        // Temp_pH_Probe
  "do_probe",        // Temp_DO_Probe
  "stirrer_motor",   // Temp_Stirrer_Motor
  "exhaust",         // Temp_Exhaust
  "headspace",       // Reactor_Pressure
  "co2",             // Off_Gas_CO2
  "o2",              // Off_Gas_O2
  "flow_in",         // Gas_Flow_Inlet
  "flow_out",        // Gas_Flow_Outlet
]

// Aggregate each sensor
from(bucket: raw_bucket)
  |> range(start: -30s)
  |> filter(fn: (r) => contains(value: r._measurement, set: sensors))
  |> aggregateWindow(
       every: 30s,
       fn: (column, tables=<-) => tables
         |> mean()
         |> set(key: "_field", value: "mean")
         |> yield(name: "mean")
         |> tables
         |> stddev()
         |> set(key: "_field", value: "std")
         |> yield(name: "std")
         |> tables
         |> min()
         |> set(key: "_field", value: "min")
         |> yield(name: "min")
         |> tables
         |> max()
         |> set(key: "_field", value: "max")
         |> yield(name: "max"),
       createEmpty: false
     )
  |> to(bucket: agg_bucket, org: "bioprocess")
