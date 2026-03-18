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

    return df


def main():
    # Load both datasets
    incident = load_and_clean("nordpay_refund_log.csv")
    baseline = load_and_clean("nordpay_refund_log_baseline_week_shift.csv")

    # Filter refunds only
    incident_refunds = incident[incident["event_type"] == "refund"]
    baseline_refunds = baseline[baseline["event_type"] == "refund"]

    # Suspicious = mismatch
    suspicious = incident_refunds[
        (incident_refunds["mismatch_flag"] == True) &
        (incident_refunds["status"] == "approved")
    ]

    # Print loss
    loss = suspicious["amount_sek"].sum()
    print(f"Misstänkt förlust: {loss} SEK")

    if suspicious.empty:
        print("Ingen misstänkt data hittades.")
        return

    # Incident curve
    incident_cost = (
        suspicious
        .set_index("timestamp")
        .resample("h")["amount_sek"]
        .sum()
    )

    # Baseline curve (ALL refunds)
    baseline_cost = (
        baseline_refunds[baseline_refunds["status"] == "approved"]
        .set_index("timestamp")
        .resample("h")["amount_sek"]
        .sum()
    )

    # Align baseline to same time (shift forward 7 days)
    baseline_cost.index = baseline_cost.index + pd.Timedelta(days=7)

    # Plot (graph)
    plt.figure(figsize=(14, 6))

    plt.plot(incident_cost.index, incident_cost.values, label="Incident (misstänkt)")
    plt.plot(baseline_cost.index, baseline_cost.values, label="Baseline (vecka tidigare)")

    plt.ylabel("SEK")
    plt.title("Refund-kostnad över tid: Incident vs vecka tidigare")
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()