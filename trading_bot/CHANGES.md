# Changes - April 24, 2026

## VPS Migration & Dynamic Position Sizing Fix

### Summary
Migrated DamJanBot to new VPS (IP: 153.75.244.71) and fixed critical bug where position size was not recalculating after realized PnL updates.

---

## 🔧 Bug Fix: Dynamic Position Sizing

### Problem
When flipping positions (e.g., SHORT → LONG), the bot was calculating the new position size using the **old balance** before the realized PnL from the closing trade was added. This meant:
- Starting balance: $1,000
- After profit of $81.37 → Balance should be $1,081.37
- But bot was using $1,060.15 (old balance) for position sizing
- Result: Wrong position size (0.007068 BTC instead of 0.007209 BTC)

### Solution
Modified `_flip_position()` in `trading_bot_server.py` to:
1. Close current position and calculate realized PnL
2. **Update** `self.position_state.realized_pnl` with the new PnL
3. **Recalculate** position size using the updated balance
4. Open new position with the correct size

### Code Changes

**File: `trading_bot_server.py`**

```python
# OLD: Used hardcoded $1000 balance
def _calculate_position_size(self, price: Decimal) -> Decimal:
    balance = Decimal("1000.0")
    allocation = Decimal("0.50")
    position_value = balance * allocation
    quantity = position_value / price if price > 0 else Decimal("0.01")
    return quantity

# NEW: Uses current balance including realized PnL
def _calculate_position_size(self, price: Decimal) -> Decimal:
    starting_balance = Decimal("1000.0")
    current_balance = starting_balance + self.position_state.realized_pnl
    allocation = Decimal("0.50")
    position_value = current_balance * allocation
    quantity = position_value / price if price > 0 else Decimal("0.01")
    logger.info(f"💰 Calculating position size: Balance=${current_balance:.2f} ...")
    return quantity
```

```python
# OLD: Used pre-calculated quantity
def _flip_position(self, symbol, current_side, action, new_quantity, price):
    # ... close position ...
    self.position_state.realized_pnl += realized_pnl
    # ... open with new_quantity (WRONG - used old balance) ...

# NEW: Recalculates after updating realized PnL
def _flip_position(self, symbol, current_side, action, new_quantity, price):
    # ... close position ...
    self.position_state.realized_pnl += realized_pnl
    
    # Recalculate with updated balance
    updated_quantity = self._calculate_position_size(price)
    
    # ... open with updated_quantity (CORRECT) ...
```

### Verification
Tested with flip from SHORT @ $78,150 → LONG @ $75,000:
- Realized PnL from close: +$21.22
- Updated balance: $1,081.37
- New position size: 0.007209 BTC ✅ (was 0.007068 BTC)

---

## 📊 Dashboard Improvements

### Added Simulated Balance Display
- Shows current balance including realized PnL
- Added "Sim Balance" card to summary bar
- Updated Configuration section with:
  - Starting Balance: $1,000.00
  - Current Balance: $X,XXX.XX (includes realized PnL)
  - Position Size: 50% of current balance = $XXX.XX

**File: `trading_bot_server.py`** (DashboardHandler)

---

## 🔧 Engine Balance Fix

### Fixed Starting Balance Mismatch
- `dry_run_engine.py` had $10,000 starting balance
- `trading_bot_server.py` used $1,000 starting balance
- **Fixed:** Aligned engine to $1,000 to match bot config

**File: `dry_run_engine.py`**
```python
# OLD
self.simulated_balance = Decimal("10000.0")

# NEW
self.simulated_balance = Decimal("1000.0")
```

---

## 🌐 VPS Migration

### New Server Configuration
- **IP:** 153.75.244.71
- **User:** root (was dame on old VPS)
- **Path:** /root/.openclaw/workspace/trading_bot

### Services Configured
- nginx (webhook proxy port 80, dashboard proxy port 8080→6000)
- systemd: trading-bot.service
- systemd: openclaw-gateway.service

### Files Updated for New IP
- `trading_bot_server.py`: Updated hardcoded IP references
- `start_webhook_server.py`: Updated IP references
- `fix_position.py`: Updated IP references
- nginx configs: Created for new server

---

## 📱 Telegram Integration

### Added Environment Variables
- `TELEGRAM_BOT_TOKEN`: From `start_with_telegram.sh`
- `TELEGRAM_CHAT_ID`: From `start_with_telegram.sh`

### Tested Successfully
- Sent test message to channel ✅

---

## Files Modified
1. `trading_bot_server.py` - Dynamic sizing, dashboard, IP updates
2. `dry_run_engine.py` - Balance alignment
3. `bot_state.json` - Synced with old bot state
4. `alert_log.jsonl` - Synced with old bot history

## Authors
- Dame & Jan | 2026
- Assisted by Claw 🦞
