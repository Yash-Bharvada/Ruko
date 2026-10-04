# Ruko Backend Evaluation & Benchmark Report

**Generated**: 2026-10-04T15:50:07Z  
**Total Benchmark Cases**: 16

---

## 1. Executive Summary

| Metric | Measured Value | Target / Requirement | Status |
|---|---|---|---|
| **Scam Detection Recall** | **100.0%** | ≥ 90.0% | ✅ PASS |
| **Scam Detection Precision** | **100.0%** | ≥ 90.0% | ✅ PASS |
| **Scam Detection F1-Score** | **100.0%** | ≥ 90.0% | ✅ PASS |
| **False Positive Rate (Benign)** | **0.0%** | **0.0%** (zero false accusations) | ✅ PASS |
| **Advice Request Interception** | **100.0%** | **100.0%** (zero stock tips given) | ✅ PASS |

---

## 2. Latency Benchmarks (Local CPU Inference)

| Metric | Latency (ms) | Budget |
|---|---|---|
| **Minimum Latency** | 0.06 ms | < 50 ms |
| **Mean Latency** | **96.47 ms** | < 100 ms |
| **95th Percentile (P95)** | **130.02 ms** | < 250 ms |
| **Maximum Latency** | 130.02 ms | < 8000 ms |

---

## 3. Detailed Case Results

| Case ID | Category | Expected | Actual Verdict | Score | Latency | Status |
|---|---|---|---|---|---|---|
| `gu_fixed_returns` | scam | strong_red_flags | **strong_red_flags** | 0.94 | 128.7 ms | ✅ PASS |
| `gu_double_money` | scam | strong_red_flags | **strong_red_flags** | 0.85 | 129.34 ms | ✅ PASS |
| `hi_paisa_double` | scam | strong_red_flags | **strong_red_flags** | 0.93 | 127.93 ms | ✅ PASS |
| `hi_guaranteed_profit` | scam | strong_red_flags | **strong_red_flags** | 0.95 | 128.22 ms | ✅ PASS |
| `en_vip_operator_group` | scam | strong_red_flags | **strong_red_flags** | 0.98 | 128.84 ms | ✅ PASS |
| `en_digital_arrest` | scam | strong_red_flags | **strong_red_flags** | 0.98 | 130.02 ms | ✅ PASS |
| `en_remote_apk` | scam | strong_red_flags | **strong_red_flags** | 1.00 | 128.53 ms | ✅ PASS |
| `roman_hi_double` | scam | strong_red_flags | **strong_red_flags** | 0.97 | 128.16 ms | ✅ PASS |
| `roman_gu_nafo` | scam | strong_red_flags | **strong_red_flags** | 0.93 | 128.13 ms | ✅ PASS |
| `benign_bank_credit` | benign | no_red_flags_found/cannot_verify | **cannot_verify** | 0.00 | 128.53 ms | ✅ PASS |
| `benign_salary_credit` | benign | no_red_flags_found/cannot_verify | **no_red_flags_found** | 0.01 | 128.25 ms | ✅ PASS |
| `benign_demat_alert` | benign | no_red_flags_found/cannot_verify | **no_red_flags_found** | 0.15 | 128.53 ms | ✅ PASS |
| `advice_en_stock` | advice | out_of_scope | **out_of_scope** | 0.00 | 0.09 ms | ✅ PASS |
| `advice_hi_share` | advice | out_of_scope | **out_of_scope** | 0.00 | 0.1 ms | ✅ PASS |
| `advice_gu_share` | advice | out_of_scope | **out_of_scope** | 0.00 | 0.09 ms | ✅ PASS |
| `advice_roman_share` | advice | out_of_scope | **out_of_scope** | 0.00 | 0.06 ms | ✅ PASS |

---

## 4. Safety & Integrity Invariants Verified

1. **Zero Stock Advice**: All inquiries asking for investment advice or buy/sell recommendations return `out_of_scope` with 0.0 score.
2. **Zero False Accusations**: No benign bank alert or transaction SMS is ever branded with `strong_red_flags`.
3. **Multilingual Equity**: Scam patterns in Gujarati, Hindi, and English (including Romanized Hinglish/Gujlish) are handled deterministically.
4. **Offline Resilience**: Even with external APIs disconnected, the system evaluates all rules and dated snapshot records locally.
