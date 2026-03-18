import pandas as pd
import matplotlib.pyplot as plt


def load_and_clean(path):
    df = pd.read_csv(path)

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["event_type"] = df["event_type"].astype(str).str.strip().str.lower()
    df["status"] = df["status"].astype(str).str.strip().str.lower()

    df["mismatch_flag"] = (
        df["mismatch_flag"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"true": True, "false": False})
    )

    df["anomaly_flag"] = (
        df["anomaly_flag"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"true": True, "false": False})
    )

    return df


def main():
    incident = load_and_clean("nordpay_refund_log.csv")
    baseline = load_and_clean("nordpay_refund_log_baseline_week_shift.csv")

    incident_refunds = incident[
        (incident["event_type"] == "refund") &
        (incident["status"] == "approved")
    ].copy()

    baseline_refunds = baseline[
        (baseline["event_type"] == "refund") &
        (baseline["status"] == "approved") &
        (baseline["mismatch_flag"] == False) &
        (baseline["anomaly_flag"] == False)
    ].copy()

    suspicious = incident_refunds[
        incident_refunds["mismatch_flag"] == True
    ].copy()

    loss = suspicious["amount_sek"].sum()
    print(f"Misstänkt förlust: {loss} SEK")

    if suspicious.empty:
        print("Ingen misstänkt data hittades.")
        return

    # Incident window = från första till sista misstänkta refund
    incident_start = suspicious["timestamp"].min().floor("h")
    incident_end = suspicious["timestamp"].max().ceil("h")

    # Samma längd en vecka tidigare
    window_length = incident_end - incident_start
    baseline_start = incident_start - pd.Timedelta(days=7)
    baseline_end = baseline_start + window_length

    # Incident: misstänkt kostnad per timme
    incident_window = suspicious[
        (suspicious["timestamp"] >= incident_start) &
        (suspicious["timestamp"] <= incident_end)
    ]

    incident_cost = (
        incident_window
        .set_index("timestamp")
        .resample("h")["amount_sek"]
        .sum()
        .reset_index()
    )

    # Baseline: normal refund-kostnad per timme i motsvarande fönster
    baseline_window = baseline_refunds[
        (baseline_refunds["timestamp"] >= baseline_start) &
        (baseline_refunds["timestamp"] <= baseline_end)
    ]

    baseline_cost = (
        baseline_window
        .set_index("timestamp")
        .resample("h")["amount_sek"]
        .sum()
        .reset_index()
    )

    # Gör om till relativa timmar så kurvorna jämförs i samma spann
    incident_cost["hour"] = range(len(incident_cost))
    baseline_cost["hour"] = range(len(baseline_cost))

    # Matcha längden om de diffar med 1 timme pga rounding
    min_len = min(len(incident_cost), len(baseline_cost))
    incident_cost = incident_cost.iloc[:min_len]
    baseline_cost = baseline_cost.iloc[:min_len]

    plt.figure(figsize=(14, 6))
    plt.plot(
        incident_cost["hour"],
        incident_cost["amount_sek"],
        label="Incident (misstänkt)"
    )
    plt.plot(
        baseline_cost["hour"],
        baseline_cost["amount_sek"],
        label="Baseline (normal vecka tidigare)"
    )

    plt.xlabel("Timmar in i jämförelsefönstret")
    plt.ylabel("SEK")
    plt.title("Refund-kostnad över tid: incident vs normal vecka tidigare")
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()