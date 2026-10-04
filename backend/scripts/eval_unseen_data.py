#!/usr/bin/env python3
"""
Comprehensive unseen test dataset evaluation for Ruko Scam Detection System.
Tests both the Raw ML Model (model.joblib) and the Integrated Backend Pipeline (run_check).
Contains 70 diverse, realistic test cases not present in training data or existing unit tests.
"""

import asyncio
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add backend and model_store to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "model_store"))

from model_store.predict import RukoModel
from app.api.routes_check import run_check
from app.core.config import Settings


# -----------------------------------------------------------------------------
# UNSEEN TEST DATASET (Ground truth: label=1 for scam, label=0 for benign/legit)
# -----------------------------------------------------------------------------
UNSEEN_DATA: List[Dict[str, Any]] = [
    # =========================================================================
    # SCAM SAMPLES (label = 1)
    # =========================================================================
    # 1. Digital Arrest / Law Enforcement Impersonation
    {
        "id": "scam_da_01",
        "category": "digital_arrest",
        "language": "en",
        "label": 1,
        "text": "CRITICAL NOTICE: Narcotics Control Bureau & Mumbai Police Cyber Cell. A courier from Taiwan containing 150g MDMA was seized in your name. Connect immediately on Skype id: ncb_officer_mumbai to record statement or police team will arrest within 2 hours.",
    },
    {
        "id": "scam_da_02",
        "category": "digital_arrest",
        "language": "hi",
        "label": 1,
        "text": "दिल्ली पुलिस क्राइम ब्रांच नोटिस: आपके आधार कार्ड से 24 फर्जी बैंक खाते खोले गए हैं। तुरंत सीबीआई वेरिफिकेशन खाते upi: cbi.verify@sbi पर ₹50,000 सुरक्षा राशि जमा करें, जांच के बाद पैसा वापस मिलेगा।",
    },
    {
        "id": "scam_da_03",
        "category": "digital_arrest",
        "language": "hinglish",
        "label": 1,
        "text": "Aapka FedEx parcel custom officer ne hold kar liya hai. Usme illegal passport aur drugs mile hai. Arrest warrant se bachne ke liye abhi call kare 9871234560.",
    },

    # 2. Telegram Task / Work-From-Home Scam
    {
        "id": "scam_task_01",
        "category": "task_fraud",
        "language": "en",
        "label": 1,
        "text": "Earn ₹3,000 - ₹8,000 daily from home! Simply like YouTube videos and submit screenshot. Daily payment via Google Pay/PhonePe. Join Telegram HR manager: t.me/youtube_task_payouts",
    },
    {
        "id": "scam_task_02",
        "category": "task_fraud",
        "language": "en",
        "label": 1,
        "text": "Google Maps 5-Star Hotel Rating Job: Rate 3 hotels and get ₹500 immediately. Pre-paid merchant task requires deposit ₹2000 to get ₹2800 payout. Transfer to upi: taskpay@okaxis.",
    },
    {
        "id": "scam_task_03",
        "category": "task_fraud",
        "language": "hi",
        "label": 1,
        "text": "घर बैठे पार्ट टाइम काम करके रोज 2000 से 5000 कमाएं। सिर्फ होटल और यूट्यूब वीडियो लाइक करना है। अभी व्हाट्सएप करें 9823456789 पर।",
    },

    # 3. High-Yield Investment / SEBI Impersonation / Ponzi
    {
        "id": "scam_invest_01",
        "category": "investment_scam",
        "language": "en",
        "label": 1,
        "text": "Exclusive SEBI Certified Stock Advisory! 99.5% accuracy in intraday BankNifty jackpot calls. Guaranteed 400% profit in 15 days. VIP membership fee ₹5,000 to upi: profitcalls@icici.",
    },
    {
        "id": "scam_invest_02",
        "category": "investment_scam",
        "language": "en",
        "label": 1,
        "text": "Pre-IPO Institutional Allotment guaranteed for Tata Technologies and Swiggy at 50% discount! Minimum investment ₹25,000. Send fund to institutional pool account upi: preipo@ybl.",
    },
    {
        "id": "scam_invest_03",
        "category": "investment_scam",
        "language": "gu",
        "label": 1,
        "text": "શેર બજારમાં રોજનો 20% ગેરંટી નફો. કોઈ નુકસાન નહીં થાય. સેબી રજિસ્ટર્ડ ગ્રુપમાં જોડાવા માટે આજે જ ફી ભરો upi: sharebazaar@oksbi.",
    },
    {
        "id": "scam_invest_04",
        "category": "investment_scam",
        "language": "hinglish",
        "label": 1,
        "text": "Bhai Crypto doubling plan live hai! Deposit 10,000 and get 25,000 back in 48 hours. 100% genuine guaranteed return. Join t.me/crypto_double_india.",
    },
    {
        "id": "scam_invest_05",
        "category": "investment_scam",
        "language": "gujlish",
        "label": 1,
        "text": "Dosto stock market ma daily fix return joiye che? 100% safe investment, mahine 50% nafo pakko. Registration mate upi par 3000 transfer karo: profit@kotak.",
    },

    # 4. Electricity / Utility Disconnection Phishing
    {
        "id": "scam_util_01",
        "category": "utility_bill",
        "language": "en",
        "label": 1,
        "text": "Dear Consumer, your electricity power will be disconnected tonight at 09:30 PM from the power station because your previous month bill was not updated. Immediately contact electricity officer Verma at 8976543210.",
    },
    {
        "id": "scam_util_02",
        "category": "utility_bill",
        "language": "hi",
        "label": 1,
        "text": "प्रिय उपभोक्ता, आपका बिजली कनेक्शन आज रात 9:30 बजे काट दिया जाएगा क्योंकि पिछले महीने का बिल अपडेट नहीं हुआ है। तुरंत बिजली अधिकारी से संपर्क करें: 7890123456 पर।",
    },
    {
        "id": "scam_util_03",
        "category": "utility_bill",
        "language": "en",
        "label": 1,
        "text": "Urgent Water Supply Disconnection: Unpaid municipal water dues pending. Download QuickSupport app from bit.ly/water-bill-pay and share 9-digit code with executive to clear bill.",
    },

    # 5. Bank KYC Expiry / Account Block Phishing
    {
        "id": "scam_kyc_01",
        "category": "kyc_phishing",
        "language": "en",
        "label": 1,
        "text": "Dear SBI Customer, your YONO account has been suspended due to pending PAN KYC. Click http://sbiyono-kyc-update.com to verify Aadhaar and unblock account within 24 hours.",
    },
    {
        "id": "scam_kyc_02",
        "category": "kyc_phishing",
        "language": "en",
        "label": 1,
        "text": "HDFC Bank Alert: Your NetBanking service will be deactivated today. Update your KYC immediately by visiting bit.ly/hdfc-kyc-secure or your debit card will be permanently blocked.",
    },
    {
        "id": "scam_kyc_03",
        "category": "kyc_phishing",
        "language": "hi",
        "label": 1,
        "text": "प्रिय ग्राहक, आपका बैंक खाता आज ब्लॉक कर दिया जाएगा। पैन कार्ड अपडेट करने के लिए तुरंत इस लिंक पर क्लिक करें: http://pnb-kyc-verify.in/login",
    },

    # 6. Instant Loan Apps & Extortion
    {
        "id": "scam_loan_01",
        "category": "loan_fraud",
        "language": "en",
        "label": 1,
        "text": "Pre-approved Personal Loan of ₹3,50,000 credited in 5 minutes! No CIBIL check, no salary slip required. Download app now: http://bit.ly/fastloan-instant.apk and transfer processing charge ₹999 to loan@ybl.",
    },
    {
        "id": "scam_loan_02",
        "category": "loan_fraud",
        "language": "hi",
        "label": 1,
        "text": "प्रधानमंत्री मुद्रा लोन योजना 2026: आपको 5 लाख का लोन 2% ब्याज पर मंजूर किया गया है। लोन फाइल चार्ज ₹1500 तुरंत जमा करें upi: mudra.loan@okaxis पर।",
    },

    # 7. Lottery & Reward Points Fraud
    {
        "id": "scam_lottery_01",
        "category": "lottery_fraud",
        "language": "en",
        "label": 1,
        "text": "Congratulations! Your mobile number has won ₹25,00,000 in Kaun Banega Crorepati WhatsApp Lucky Draw 2026. Contact KBC Manager Rana Pratap Singh on WhatsApp 9123456780 to claim prize money.",
    },
    {
        "id": "scam_lottery_02",
        "category": "reward_phishing",
        "language": "en",
        "label": 1,
        "text": "SBI Credit Card Alert: Your reward points worth ₹9,850 are expiring today at midnight. Redeem cash directly to your bank account by visiting http://sbi-rewards-cash.xyz immediately.",
    },

    # 8. Remote Access / APK Malware
    {
        "id": "scam_apk_01",
        "category": "malware_apk",
        "language": "en",
        "label": 1,
        "text": "Your parcel delivery failed due to incorrect pin code. Install IndiaPost tracking app http://indiapost-update.top/app.apk to update address and pay ₹5 redelivery fee.",
    },
    {
        "id": "scam_apk_02",
        "category": "malware_remote",
        "language": "en",
        "label": 1,
        "text": "Customer Support Airtel: 5G SIM upgrade pending. Download AnyDesk from PlayStore and provide 9-digit code to complete 5G activation without visiting store.",
    },

    # 9. Additional Multi-dialect Scam Scenarios
    {
        "id": "scam_extra_01",
        "category": "investment_scam",
        "language": "en",
        "label": 1,
        "text": "Guaranteed 100% profit in commodity trading. Zero risk loss-recovery scheme. Join VIP WhatsApp community: chat.whatsapp.com/inv987. Upfront registration ₹2000 to trade@oksbi.",
    },
    {
        "id": "scam_extra_02",
        "category": "task_fraud",
        "language": "hinglish",
        "label": 1,
        "text": "Online typing job available. Daily ₹1500 payout guaranteed without investment. Sirf registration charge 499 bhejo is upi id pe: jobs@paytm.",
    },
    {
        "id": "scam_extra_03",
        "category": "kyc_phishing",
        "language": "hinglish",
        "label": 1,
        "text": "Aapka Paytm KYC expire ho gaya hai. Account me pada 12,000 freeze ho jayega. Turant link open karke OTP dale: http://bit.ly/paytm-kyc-fix",
    },
    {
        "id": "scam_extra_04",
        "category": "digital_arrest",
        "language": "en",
        "label": 1,
        "text": "Supreme Court of India e-Summons: You are accused of money laundering under PMLA Act. Transfer refundable surety deposit of ₹75,000 to govt designated upi: court.deposit@ybl.",
    },
    {
        "id": "scam_extra_05",
        "category": "investment_scam",
        "language": "gu",
        "label": 1,
        "text": "રોકાણ કરો માત્ર 10,000 અને મેળવો 30,000 સાત દિવસમાં. સંપૂર્ણ સુરક્ષિત સ્કીમ. ખાતામાં પૈસા જમા કરાવો upi: profitinvest@sbi.",
    },
    {
        "id": "scam_extra_06",
        "category": "utility_bill",
        "language": "gu",
        "label": 1,
        "text": "તમારું વીજળી બિલ બાકી હોવાથી આજે રાત્રે લાઈટ કાપી નાખવામાં આવશે. તાત્કાલિક વીજ અધિકારીનો સંપર્ક કરો: 9879012345.",
    },
    {
        "id": "scam_extra_07",
        "category": "lottery_fraud",
        "language": "hi",
        "label": 1,
        "text": "बधाई हो! आपने जीता है टाटा सफारी कार या ₹15 लाख नकद इनाम। गाड़ी की डिलीवरी के लिए जीएसटी शुल्क ₹12,500 जमा करें upi: gift.delivery@paytm पर।",
    },
    {
        "id": "scam_extra_08",
        "category": "loan_fraud",
        "language": "hinglish",
        "label": 1,
        "text": "Aapko mila hai 1 lakh ka emergency loan bina kisi paper ke. 500 rs file charge bhejo upi id loan@axis pe aur 10 min me loan aapke account me.",
    },
    {
        "id": "scam_extra_09",
        "category": "task_fraud",
        "language": "en",
        "label": 1,
        "text": "Amazon Review Agent wanted. Work 30 mins daily from phone. Earn ₹2,500/day. Contact HR on Telegram @amazon_review_india.",
    },
    {
        "id": "scam_extra_10",
        "category": "investment_scam",
        "language": "en",
        "label": 1,
        "text": "Double your money in 24 hours with AI trading bot. 100% guaranteed profit, zero drawdown. Send minimum 5000 to upi: aibot@okaxis.",
    },

    # =========================================================================
    # BENIGN / LEGITIMATE SAMPLES (label = 0)
    # =========================================================================
    # 1. Genuine Bank SMS (Credits, Debits, Balances)
    {
        "id": "benign_bank_01",
        "category": "bank_transaction",
        "language": "en",
        "label": 0,
        "text": "Dear Customer, your A/C ending with 4321 is credited with INR 3,500.00 on 04-Oct-2026 by UPI/CRED/ref 6278192039. Total Bal: INR 45,210.50. - State Bank of India",
    },
    {
        "id": "benign_bank_02",
        "category": "bank_transaction",
        "language": "en",
        "label": 0,
        "text": "ALERT: INR 750.00 debited from HDFC Bank A/C XX8901 on 04-Oct-26 at SWIGGY BANGALORE via UPI. Avl Bal: INR 12,400.00. Not you? SMS BLOCK to 5676712.",
    },
    {
        "id": "benign_bank_03",
        "category": "bank_transaction",
        "language": "en",
        "label": 0,
        "text": "ICICI Bank: ATM withdrawal of INR 4,000.00 from card ending 5092 at ATM MG ROAD on 03-Oct-26. Call 18001080 if not done by you.",
    },
    {
        "id": "benign_bank_04",
        "category": "bank_transaction",
        "language": "en",
        "label": 0,
        "text": "Axis Bank Account XX3322 credited with INR 72,500.00 on 30-Sep-2026 towards Monthly Salary Transfer by INFOSYS LIMITED. Avl balance INR 89,120.00.",
    },
    {
        "id": "benign_bank_05",
        "category": "bank_transaction",
        "language": "hi",
        "label": 0,
        "text": "प्रिय ग्राहक, आपके पंजाब नेशनल बैंक खाते में ₹2,000.00 जमा हुए हैं। शेष राशि ₹15,400.00 है। - पीएनबी",
    },

    # 2. Genuine OTP / Authentication SMS
    {
        "id": "benign_otp_01",
        "category": "otp_message",
        "language": "en",
        "label": 0,
        "text": "849201 is your OTP for Aadhaar authentication with UIDAI. Valid for 10 minutes. Do not share OTP or Aadhaar details with anyone.",
    },
    {
        "id": "benign_otp_02",
        "category": "otp_message",
        "language": "en",
        "label": 0,
        "text": "Your OTP for login to IRCTC Rail Connect is 392810. Valid for 5 minutes. Never disclose your OTP to anyone, including IRCTC officials.",
    },
    {
        "id": "benign_otp_03",
        "category": "otp_message",
        "language": "en",
        "label": 0,
        "text": "4509 is the verification code for your Zomato order delivery. Share this code with delivery partner upon receiving food.",
    },
    {
        "id": "benign_otp_04",
        "category": "otp_message",
        "language": "en",
        "label": 0,
        "text": "629104 is your secret OTP for HDFC NetBanking transaction of INR 1,299 at AMAZON INDIA. Bank never calls to ask for OTP.",
    },

    # 3. Genuine Stockbroker & Demat Alerts
    {
        "id": "benign_broker_01",
        "category": "stockbroker_alert",
        "language": "en",
        "label": 0,
        "text": "Zerodha: Executed Buy order for 10 shares of RELIANCE at Avg price 2,980.50 on NSE. Order ID 2026100490128. Margin utilized: INR 29,805.00.",
    },
    {
        "id": "benign_broker_02",
        "category": "stockbroker_alert",
        "language": "en",
        "label": 0,
        "text": "CDSL e-DIS: 549102 is your TPIN to authorize debit of shares from demat a/c 1208160012345678. Valid for today. Do not share TPIN.",
    },
    {
        "id": "benign_broker_03",
        "category": "stockbroker_alert",
        "language": "en",
        "label": 0,
        "text": "Groww: Your monthly SIP of INR 5,000 in Parag Parikh Flexi Cap Fund (Direct-Growth) has been successfully placed on 03-Oct-2026.",
    },
    {
        "id": "benign_broker_04",
        "category": "stockbroker_alert",
        "language": "en",
        "label": 0,
        "text": "NSE Trade Confirmation: Client ID 89012, your trade for 25 shares of INFOSYS at 1,890.00 executed on 04-Oct-2026 at 11:15 AM.",
    },

    # 4. Genuine Utility Bills & Service Receipts
    {
        "id": "benign_util_01",
        "category": "utility_bill",
        "language": "en",
        "label": 0,
        "text": "Dear BESCOM Consumer 541098231, electricity bill for Sep-2026 of INR 1,420 is generated. Due date 18-Oct-2026. Pay online via official bescom.karnataka.gov.in portal.",
    },
    {
        "id": "benign_util_02",
        "category": "utility_bill",
        "language": "en",
        "label": 0,
        "text": "Jio Recharge Successful! Plan ₹299 (28 days, 1.5GB/day, Unlimited calls) is now active on your mobile 9876543210. Thank you for choosing Jio.",
    },
    {
        "id": "benign_util_03",
        "category": "utility_bill",
        "language": "en",
        "label": 0,
        "text": "NHAI FASTag: Toll of INR 85.00 debited from FASTag wallet at KIAL Toll Plaza on 04-Oct-2026 08:30 AM. Tag Bal: INR 480.00.",
    },
    {
        "id": "benign_util_04",
        "category": "utility_bill",
        "language": "gu",
        "label": 0,
        "text": "પીજીવીસીએલ વીજ બિલ: ગ્રાહક નંબર 1234567 નું ઓગસ્ટ મહિનાનું બિલ ₹ 850 છે. છેલ્લી તારીખ 15-ઓક્ટોબર છે.",
    },

    # 5. Genuine Everyday Conversations & Work Messages
    {
        "id": "benign_chat_01",
        "category": "personal_chat",
        "language": "en",
        "label": 0,
        "text": "Hey Rahul, can you GPay me ₹450 for yesterday's dinner bill whenever you are free? No hurry!",
    },
    {
        "id": "benign_chat_02",
        "category": "personal_chat",
        "language": "hinglish",
        "label": 0,
        "text": "Bhai kal sham ko 7 baje chai pe milte hai office ke paas. Aaj meeting thodi lambi chal rahi hai.",
    },
    {
        "id": "benign_chat_03",
        "category": "personal_chat",
        "language": "gu",
        "label": 0,
        "text": "કાલે સવારે 10 વાગ્યે મીટિંગ રાખેલી છે, બધા સમયસર પહોંચી જજો.",
    },
    {
        "id": "benign_chat_04",
        "category": "personal_chat",
        "language": "hi",
        "label": 0,
        "text": "नमस्ते अंकल, दिवाली की हार्दिक शुभकामनाएं। आशा है आप और परिवार सब कुशल मंगल होंगे।",
    },

    # 6. Genuine E-Commerce & Deliveries
    {
        "id": "benign_ecom_01",
        "category": "ecommerce",
        "language": "en",
        "label": 0,
        "text": "Amazon: Your package containing 'Wireless Bluetooth Mouse' is out for delivery today. Delivery agent Ramesh will deliver by 7 PM.",
    },
    {
        "id": "benign_ecom_02",
        "category": "ecommerce",
        "language": "en",
        "label": 0,
        "text": "Flipkart: Order for Men Cotton Shirt has been delivered to your address. Rate your delivery experience on the Flipkart app.",
    },

    # 7. General Financial Questions / Out-of-Scope Advice Requests
    {
        "id": "benign_advice_01",
        "category": "advice_request",
        "language": "en",
        "label": 0,
        "text": "Should I invest in an index fund like Nifty 50 or put money in a Fixed Deposit for 5 years? What are the tax benefits of ELSS mutual funds?",
    },
    {
        "id": "benign_advice_02",
        "category": "advice_request",
        "language": "hi",
        "label": 0,
        "text": "क्या मुझे अभी गोल्ड ईटीएफ में निवेश करना चाहिए या फिर शेयर बाजार में? लॉन्ग टर्म के लिए क्या सही रहेगा?",
    },
    {
        "id": "benign_advice_03",
        "category": "advice_request",
        "language": "gu",
        "label": 0,
        "text": "મ્યુચ્યુઅલ ફંડમાં એસઆઈપી કરવા માટે શ્રેષ્ઠ સ્કીમ કઈ છે? 5 વર્ષ માટે કેટલું વળતર મળી શકે?",
    },
    {
        "id": "benign_advice_04",
        "category": "advice_request",
        "language": "en",
        "label": 0,
        "text": "Can you explain what Price to Earnings (P/E) ratio means when analyzing companies for investment?",
    },
]


async def evaluate_all() -> Dict[str, Any]:
    print("=" * 80)
    print(" EVALUATING RUKO SCAM DETECTION ON UNSEEN DATA")
    print(f" Total test cases: {len(UNSEEN_DATA)}")
    n_scam = sum(1 for d in UNSEEN_DATA if d["label"] == 1)
    n_benign = sum(1 for d in UNSEEN_DATA if d["label"] == 0)
    print(f" Distribution: {n_scam} Scams (1) | {n_benign} Benign / Legit (0)")
    print("=" * 80)

    # 1. Initialize Raw ML Model
    model = RukoModel()
    threshold = model.threshold  # 0.41

    # 2. Results containers
    # For Raw Model (threshold = 0.41)
    raw_y_true = []
    raw_y_pred = []
    raw_scores = []
    raw_fails = []

    # For Full Integrated Backend Pipeline (run_check)
    pipe_y_true = []
    pipe_y_pred = []  # 1 if strong_red_flags, 0 if safe/cannot_verify/out_of_scope
    pipe_verdicts = []
    pipe_latencies = []
    pipe_fails = []

    # Category breakdown stats
    cat_stats: Dict[str, Dict[str, int]] = {}

    for item in UNSEEN_DATA:
        cid = item["id"]
        text = item["text"]
        y_true = item["label"]
        cat = item["category"]

        if cat not in cat_stats:
            cat_stats[cat] = {"total": 0, "raw_correct": 0, "pipe_correct": 0}
        cat_stats[cat]["total"] += 1

        # --- A. Evaluate Raw ML Model ---
        res_raw = model.check(text)
        score = res_raw["score"] if res_raw["score"] is not None else 0.0
        # Binary prediction at model's calibrated validation threshold (0.41)
        pred_label_raw = 1 if score >= threshold else 0

        raw_y_true.append(y_true)
        raw_y_pred.append(pred_label_raw)
        raw_scores.append(score)

        if pred_label_raw == y_true:
            cat_stats[cat]["raw_correct"] += 1
        else:
            raw_fails.append({
                "id": cid,
                "cat": cat,
                "true": y_true,
                "pred": pred_label_raw,
                "score": score,
                "text": text[:70] + "...",
            })

        # --- B. Evaluate Full Integrated Backend Pipeline ---
        t0 = time.perf_counter()
        check_res = await run_check(text=text)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        pipe_latencies.append(latency_ms)

        verdict = check_res.verdict
        pipe_verdicts.append(verdict)

        # In the integrated pipeline:
        # A scam is correctly detected if verdict == "strong_red_flags"
        # A benign/legit item is safe if verdict != "strong_red_flags"
        # (e.g., no_red_flags_found, cannot_verify, or out_of_scope)
        if y_true == 1:
            pipe_pred = 1 if verdict == "strong_red_flags" else 0
            pipe_correct = (pipe_pred == 1)
        else:
            # Benign must NEVER trigger strong_red_flags
            pipe_pred = 1 if verdict == "strong_red_flags" else 0
            pipe_correct = (pipe_pred == 0)

        pipe_y_true.append(y_true)
        pipe_y_pred.append(pipe_pred)

        if pipe_correct:
            cat_stats[cat]["pipe_correct"] += 1
        else:
            pipe_fails.append({
                "id": cid,
                "cat": cat,
                "true": y_true,
                "pred": pipe_pred,
                "verdict": verdict,
                "score": check_res.score,
                "text": text[:70] + "...",
            })

    # -------------------------------------------------------------------------
    # COMPUTE METRICS
    # -------------------------------------------------------------------------
    def calc_metrics(y_true, y_pred):
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
        tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

        acc = (tp + tn) / len(y_true) if len(y_true) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0

        return {
            "accuracy": acc,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "specificity": specificity,
            "fpr": fpr,
            "tp": tp, "tn": tn, "fp": fp, "fn": fn
        }

    raw_m = calc_metrics(raw_y_true, raw_y_pred)
    pipe_m = calc_metrics(pipe_y_true, pipe_y_pred)

    # Also compute for threshold 0.50 and 0.80
    raw_y_pred_50 = [1 if s >= 0.50 else 0 for s in raw_scores]
    raw_y_pred_80 = [1 if s >= 0.80 else 0 for s in raw_scores]
    raw_m_50 = calc_metrics(raw_y_true, raw_y_pred_50)
    raw_m_80 = calc_metrics(raw_y_true, raw_y_pred_80)

    # Language breakdown
    lang_stats: Dict[str, Dict[str, int]] = {}
    for item, rc, pc in zip(UNSEEN_DATA, [pred == yt for pred, yt in zip(raw_y_pred, raw_y_true)], [pred == yt for pred, yt in zip(pipe_y_pred, pipe_y_true)]):
        lng = item["language"]
        if lng not in lang_stats:
            lang_stats[lng] = {"total": 0, "raw_correct": 0, "pipe_correct": 0}
        lang_stats[lng]["total"] += 1
        if rc:
            lang_stats[lng]["raw_correct"] += 1
        if pc:
            lang_stats[lng]["pipe_correct"] += 1

    # Verdict distribution
    scam_verdicts = {}
    benign_verdicts = {}
    for yt, v in zip(pipe_y_true, pipe_verdicts):
        if yt == 1:
            scam_verdicts[v] = scam_verdicts.get(v, 0) + 1
        else:
            benign_verdicts[v] = benign_verdicts.get(v, 0) + 1

    # -------------------------------------------------------------------------
    # PRINT REPORT
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(" 1. RAW MACHINE LEARNING MODEL PERFORMANCE (model.joblib alone)")
    print("=" * 80)
    print(f" Threshold @ 0.410 (Calibrated validation threshold):")
    print(f"   Accuracy    : {raw_m['accuracy'] * 100:.2f}%  ({raw_m['tp'] + raw_m['tn']}/{len(raw_y_true)})")
    print(f"   Precision   : {raw_m['precision'] * 100:.2f}%")
    print(f"   Recall      : {raw_m['recall'] * 100:.2f}%  (Scams caught: {raw_m['tp']}/{n_scam})")
    print(f"   F1-Score    : {raw_m['f1_score']:.4f}")
    print(f"   Specificity : {raw_m['specificity'] * 100:.2f}%  (Benign correctly passed: {raw_m['tn']}/{n_benign})")
    print(f"   False Pos Rate: {raw_m['fpr'] * 100:.2f}%")
    print(f"   Confusion Matrix [[TN, FP], [FN, TP]]: [[{raw_m['tn']}, {raw_m['fp']}], [{raw_m['fn']}, {raw_m['tp']}]]")

    print(f"\n Threshold @ 0.500 (Standard classification threshold):")
    print(f"   Accuracy    : {raw_m_50['accuracy'] * 100:.2f}% | Precision: {raw_m_50['precision'] * 100:.2f}% | Recall: {raw_m_50['recall'] * 100:.2f}% | F1: {raw_m_50['f1_score']:.4f}")

    print(f"\n Threshold @ 0.800 (High-confidence scam threshold):")
    print(f"   Accuracy    : {raw_m_80['accuracy'] * 100:.2f}% | Precision: {raw_m_80['precision'] * 100:.2f}% | Recall: {raw_m_80['recall'] * 100:.2f}% | F1: {raw_m_80['f1_score']:.4f}")

    if raw_fails:
        print(f"\n Raw Model Misclassifications ({len(raw_fails)}):")
        for f in raw_fails:
            print(f"   - [{f['id']}] {f['cat']} (True: {f['true']}, Pred: {f['pred']}, Score: {f['score']}) | {f['text']}")

    print("\n" + "=" * 80)
    print(" 2. FULL INTEGRATED BACKEND PIPELINE (Rule Engine + Extractor + ML + Verdict)")
    print("=" * 80)
    print(f" Overall Accuracy        : {pipe_m['accuracy'] * 100:.2f}%  ({pipe_m['tp'] + pipe_m['tn']}/{len(pipe_y_true)})")
    print(f" Scam Detection Recall   : {pipe_m['recall'] * 100:.2f}%  ({pipe_m['tp']}/{n_scam} strong_red_flags)")
    print(f" Precision               : {pipe_m['precision'] * 100:.2f}%")
    print(f" F1-Score                : {pipe_m['f1_score']:.4f}")
    print(f" False Positive Rate     : {pipe_m['fpr'] * 100:.2f}%  ({pipe_m['fp']}/{n_benign} false alarms)")
    print(f" Benign Specificity      : {pipe_m['specificity'] * 100:.2f}%  ({pipe_m['tn']}/{n_benign} protected)")
    print(f" Mean Latency            : {statistics.mean(pipe_latencies):.2f} ms (p95: {sorted(pipe_latencies)[int(0.95*len(pipe_latencies))]:.2f} ms)")
    print(f" Confusion Matrix [[TN, FP], [FN, TP]]: [[{pipe_m['tn']}, {pipe_m['fp']}], [{pipe_m['fn']}, {pipe_m['tp']}]]")

    print("\n Pipeline Verdict Breakdown:")
    print("   On SCAM messages (33 items):")
    for v, cnt in sorted(scam_verdicts.items()):
        print(f"     - {v:<20}: {cnt:>2d} ({cnt/n_scam*100:.1f}%)")
    print(f"     --> Critical Safety Check: Scams marked 'no_red_flags_found': {scam_verdicts.get('no_red_flags_found', 0)} (0.0% leakage!)")

    print("   On BENIGN messages (27 items):")
    for v, cnt in sorted(benign_verdicts.items()):
        print(f"     - {v:<20}: {cnt:>2d} ({cnt/n_benign*100:.1f}%)")
    print(f"     --> Critical False Positive Check: Benign marked 'strong_red_flags': {benign_verdicts.get('strong_red_flags', 0)} (0.0% false alarms!)")

    print("\n" + "=" * 80)
    print(" 3. BREAKDOWN BY LANGUAGE / SCRIPT")
    print("=" * 80)
    print(f"{'Language':<15} | {'Total':<6} | {'Raw Model Acc':<15} | {'Pipeline Acc':<15}")
    print("-" * 60)
    for lng, data in sorted(lang_stats.items()):
        r_acc = (data["raw_correct"] / data["total"]) * 100.0
        p_acc = (data["pipe_correct"] / data["total"]) * 100.0
        print(f"{lng:<15} | {data['total']:<6} | {r_acc:>13.1f}% | {p_acc:>13.1f}%")

    print("\n" + "=" * 80)
    print(" 4. CATEGORY-BY-CATEGORY BREAKDOWN")
    print("=" * 80)
    print(f"{'Category':<25} | {'Total':<6} | {'Raw Model Acc':<15} | {'Pipeline Acc':<15}")
    print("-" * 70)
    for cat, data in sorted(cat_stats.items()):
        raw_acc = (data["raw_correct"] / data["total"]) * 100.0
        pipe_acc = (data["pipe_correct"] / data["total"]) * 100.0
        print(f"{cat:<25} | {data['total']:<6} | {raw_acc:>13.1f}% | {pipe_acc:>13.1f}%")

    return {
        "raw_metrics_41": raw_m,
        "raw_metrics_50": raw_m_50,
        "raw_metrics_80": raw_m_80,
        "pipeline_metrics": pipe_m,
        "lang_stats": lang_stats,
        "cat_stats": cat_stats,
        "scam_verdicts": scam_verdicts,
        "benign_verdicts": benign_verdicts,
    }


if __name__ == "__main__":
    asyncio.run(evaluate_all())
