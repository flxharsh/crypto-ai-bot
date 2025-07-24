import json
import os
from datetime import datetime

HISTORY_FILE = "trade_history.json"
ACCURACY_FILE = "accuracy.json"

# 📥 Load trade history
def load_trade_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Error decoding trade_history.json")
                return []
    return []

# 💾 Save accuracy report
def save_accuracy_report(report):
    with open(ACCURACY_FILE, "w") as file:
        json.dump(report, file, indent=4)

# 📊 Evaluate accuracy of closed trades
def evaluate_trade_accuracy():
    trades = load_trade_history()
    if not trades:
        print("⚠️ No trade history found.")
        return {
            "accuracy_percent": 0.0,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "evaluated_trades": []
        }

    wins = 0
    losses = 0
    details = []

    for trade in trades:
        if trade.get("signal") == "WAIT":
            continue

        entry = trade.get("entry_price")
        exit_ = trade.get("exit_price")

        # 🩹 Fix missing entry price fallback
        if entry in [None, "", 0] and trade.get("signal") == "SELL":
            entry = trade.get("price")

        if entry in [None, "", 0] or exit_ in [None, "", 0]:
            print(f"⚠️ Skipping invalid trade: {trade}")
            continue

        try:
            entry = float(entry)
            exit_ = float(exit_)
            side = trade.get("signal", "").upper()

            if side not in ["BUY", "SELL"]:
                continue

            pnl = (exit_ - entry) if side == "BUY" else (entry - exit_)
            is_win = pnl > 0
            result = "WIN" if is_win else "LOSS"

            if is_win:
                wins += 1
            else:
                losses += 1

            details.append({
                "symbol": trade.get("symbol", "UNKNOWN"),
                "side": side,
                "entry": round(entry, 2),
                "exit": round(exit_, 2),
                "pnl": round(pnl, 2),
                "result": result,
                "timestamp": trade.get("timestamp", "UNKNOWN")
            })

        except Exception as e:
            print(f"⚠️ Error evaluating trade: {e}")
            continue

    total = wins + losses
    win_rate = (wins / total) * 100 if total > 0 else 0.0

    report = {
        "accuracy_percent": round(win_rate, 2),
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "evaluated_trades": details
    }

    save_accuracy_report(report)
    print(f"✅ Accuracy Report Saved: {wins}/{total} WIN → {win_rate:.2f}%")

    return report
