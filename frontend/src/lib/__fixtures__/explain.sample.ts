import type { DocExplanation } from "../api";

export const SAMPLE_EXPLANATION_EN: DocExplanation = {
  request_id: "sample-loan-agreement-en",
  language: "en",
  input_source: "text",
  doc_type_guess: "loan_agreement",
  summary:
    "This document outlines a personal loan agreement for a principal amount of INR 2,50,000 between Apex Finance and the borrower. It establishes an interest rate of 14.5% and a repayment schedule of 24 monthly installments of INR 12,060 due on the 5th of every month. Additionally, it specifies an upfront processing fee of INR 3,500.",
  glossary: [
    {
      term: "Principal Amount",
      meaning: "The original sum of money borrowed before interest and fees are added.",
      evidence: "Principal amount INR 2,50,000",
    },
    {
      term: "EMI",
      meaning:
        "Equated Monthly Installment, a fixed payment amount made by a borrower to a lender on a specified date each month.",
      evidence: "Repayment in 24 EMIs of INR 12,060",
    },
    {
      term: "Processing Fee",
      meaning:
        "A one-time upfront administrative charge deducted by the lender for handling the loan application.",
      evidence: "Upfront processing fee of INR 3,500",
    },
  ],
  key_points: [
    {
      id: "kp_1",
      category: "fee",
      text: "A one-time non-refundable upfront processing fee of INR 3,500 is deducted before loan disbursement.",
      evidence: "Upfront processing fee of INR 3,500.",
    },
    {
      id: "kp_2",
      category: "obligation",
      text: "Repayment must be completed in 24 monthly installments of INR 12,060 due on the 5th of each month.",
      evidence: "Repayment in 24 EMIs of INR 12,060 due on the 5th of every month.",
    },
    {
      id: "kp_3",
      category: "obligation",
      text: "The loan carries a fixed annual interest rate of 14.5%.",
      evidence: "Principal amount INR 2,50,000 at 14.5% interest rate.",
    },
  ],
  steps: [
    {
      order: 1,
      title: "Pay Upfront Processing Fee",
      text: "Pay the administrative processing fee of INR 3,500 to finalize documentation.",
      evidence: "Upfront processing fee of INR 3,500.",
    },
    {
      order: 2,
      title: "Receive Loan Disbursement",
      text: "The lender transfers the net principal amount of INR 2,50,000 directly to your verified bank account.",
      evidence: "Principal amount INR 2,50,000",
    },
    {
      order: 3,
      title: "Set Up Monthly Auto-Debit",
      text: "Ensure funds of INR 12,060 are available on the 5th of each month for 24 cycles.",
      evidence: "Repayment in 24 EMIs of INR 12,060 due on the 5th of every month.",
    },
  ],
  diagrams: {
    flowchart: {
      title: "Loan Processing Workflow",
      nodes: [
        { id: "n1", label: "Loan Agreement Signed", kind: "start" },
        { id: "n2", label: "Pay Upfront Fee INR 3,500", kind: "step" },
        { id: "n3", label: "Disburse INR 2,50,000", kind: "money" },
        { id: "n4", label: "Repay 24 Monthly EMIs", kind: "loop" },
        { id: "n5", label: "Loan Fully Closed", kind: "end" },
      ],
      edges: [
        { source: "n1", target: "n2", label: "documentation" },
        { source: "n2", target: "n3", label: "approval" },
        { source: "n3", target: "n4", label: "disbursed" },
        { source: "n4", target: "n5", label: "completed" },
      ],
    },
    money_flow: {
      title: "Payment Flow Diagram",
      nodes: [
        { id: "m1", label: "Lender (Apex Finance)", kind: "party" },
        { id: "m2", label: "Disbursement INR 2,50,000", kind: "money" },
        { id: "m3", label: "Borrower", kind: "party" },
        { id: "m4", label: "Monthly EMI INR 12,060", kind: "money" },
      ],
      edges: [
        { source: "m1", target: "m2", label: "transfers" },
        { source: "m2", target: "m3", label: "receives" },
        { source: "m3", target: "m4", label: "repays monthly" },
        { source: "m4", target: "m1", label: "returned" },
      ],
    },
    timeline: [
      {
        label: "Processing Fee & Verification",
        date_text: "Day 1 (Immediate)",
        evidence: "Upfront processing fee of INR 3,500.",
      },
      {
        label: "Loan Disbursal to Bank Account",
        date_text: "Day 3 (Within 48-72h)",
        evidence: "Principal amount INR 2,50,000",
      },
      {
        label: "First Monthly EMI Due",
        date_text: "5th of Next Month",
        evidence: "due on the 5th of every month.",
      },
      {
        label: "Final Repayment (24th EMI)",
        date_text: "Month 24",
        evidence: "Repayment in 24 EMIs",
      },
    ],
  },
  storyboard: [
    {
      scene_id: "scene_1",
      narration:
        "This document outlines a personal loan agreement for a principal amount of INR 2,50,000. It establishes a 14.5 percent interest rate and repayment over 24 monthly installments.",
      caption: "Document Overview: Personal Loan Agreement",
      visual: { type: "title", ref: "overview" },
      issued_at: Math.floor(Date.now() / 1000),
      speak_token: "mock-token-1",
    },
    {
      scene_id: "scene_2",
      narration:
        "A one-time non-refundable upfront processing fee of INR 3,500 is deducted. Repayment must be completed in 24 monthly installments of INR 12,060.",
      caption: "Key Obligations & Fees",
      visual: { type: "bullets", ref: "key_obligations" },
      issued_at: Math.floor(Date.now() / 1000),
      speak_token: "mock-token-2",
    },
    {
      scene_id: "scene_3",
      narration:
        "First, Loan Agreement Signed. Then, Pay Upfront Fee INR 3,500. Then, Disburse INR 2,50,000. Finally, Loan Fully Closed.",
      caption: "Loan Processing Workflow",
      visual: { type: "flowchart", ref: "flowchart_1" },
      issued_at: Math.floor(Date.now() / 1000),
      speak_token: "mock-token-3",
    },
    {
      scene_id: "scene_4",
      narration: "Step 1: Pay Upfront Processing Fee. Step 2: Receive Loan Disbursement.",
      caption: "Important Next Steps",
      visual: { type: "bullets", ref: "steps" },
      issued_at: Math.floor(Date.now() / 1000),
      speak_token: "mock-token-4",
    },
    {
      scene_id: "scene_5",
      narration:
        "First, Processing Fee & Verification on Day 1 (Immediate). Finally, First Monthly EMI Due on 5th of Next Month.",
      caption: "Important Milestones & Dates",
      visual: { type: "timeline", ref: "timeline_1" },
      issued_at: Math.floor(Date.now() / 1000),
      speak_token: "mock-token-5",
    },
    {
      scene_id: "scene_6",
      narration:
        "Ruko is an automated educational tool for scam detection. It is not financial advice, legal advice, or a guarantee of safety. Always verify independently with official regulators such as SEBI.",
      caption: "Educational Notice & Disclaimer",
      visual: { type: "title", ref: "disclaimer" },
      issued_at: Math.floor(Date.now() / 1000),
      speak_token: "mock-token-6",
    },
  ],
  ruko_flags: [],
  registry: null,
  ocr_quality: "n/a",
  confidence_notes: ["Terms and clauses were extracted directly from the provided agreement text."],
  disclaimer:
    "Ruko is an automated educational tool for scam detection. It is not financial advice, legal advice, or a guarantee of safety. Always verify independently with official regulators such as SEBI.",
  degraded: [],
};

export const SAMPLE_EXPLANATION_HI: DocExplanation = {
  ...SAMPLE_EXPLANATION_EN,
  request_id: "sample-loan-agreement-hi",
  language: "hi",
  summary:
    "यह दस्तावेज़ 2,50,000 रुपये की मूल राशि के लिए एक व्यक्तिगत ऋण समझौते (पर्सनल लोन एग्रीमेंट) का विवरण देता है। यह 14.5% की ब्याज दर और 24 महीनों के लिए हर महीने की 5 तारीख को 12,060 रुपये की ईएमआई तय करता है। इसके अलावा 3,500 रुपये की अग्रिम प्रोसेसिंग फीस भी शामिल है।",
  glossary: [
    {
      term: "मूल राशि (Principal Amount)",
      meaning: "ब्याज और अन्य शुल्कों से पहले उधार ली गई वास्तविक राशि।",
      evidence: "Principal amount INR 2,50,000",
    },
    {
      term: "ईएमआई (EMI)",
      meaning: "समान मासिक किस्त जो हर महीने तय तारीख पर ऋण चुकाने के लिए दी जाती है।",
      evidence: "Repayment in 24 EMIs of INR 12,060",
    },
  ],
  disclaimer:
    "रुको स्कैम की पहचान करने वाला एक ऑटोमेटेड शैक्षणिक टूल है। यह कोई वित्तीय या कानूनी सलाह नहीं है, और न ही सुरक्षा की कोई गारंटी है। हमेशा सेबी (SEBI) जैसे आधिकारिक नियामकों से स्वयं पुष्टि करें।",
};

export const SAMPLE_EXPLANATION_GU: DocExplanation = {
  ...SAMPLE_EXPLANATION_EN,
  request_id: "sample-loan-agreement-gu",
  language: "gu",
  summary:
    "આ દસ્તાવેજ 2,50,000 રૂપિયાની રકમ માટે પર્સનલ લોન કરારની રૂપરેખા આપે છે. તેમાં 14.5% નો વ્યાજ દર અને દર મહિનાની 5મી તારીખે 12,060 રૂપિયાના 24 માસિક હપ્તા (EMI) નું સમયપત્રક નક્કી કરવામાં આવ્યું છે.",
  glossary: [
    {
      term: "મુદ્દલ રકમ (Principal Amount)",
      meaning: "વ્યાજ અને ચાર્જ ઉમેર્યા પહેલાં ઉછીના લીધેલ વાસ્તવિક રકમ.",
      evidence: "Principal amount INR 2,50,000",
    },
  ],
  disclaimer:
    "રૂકો એ સ્કેમ ઓળખવા માટેનું એક ઓટોમેટેડ શૈક્ષણિક ટૂલ છે. આ કોઈ નાણાકીય કે કાનૂની સલાહ નથી, કે સલામતીની ખાતરી નથી. હંમેશા સેબી (SEBI) જેવા સત્તાવાર નિયામકો સાથે જાતે ખાતરી કરો.",
};

export function getSampleExplanation(lang = "en"): DocExplanation {
  const l = (lang || "en").toLowerCase().trim();
  if (l === "hi") return SAMPLE_EXPLANATION_HI;
  if (l === "gu") return SAMPLE_EXPLANATION_GU;
  return SAMPLE_EXPLANATION_EN;
}
