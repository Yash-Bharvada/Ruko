/**
 * Typed dictionary of static UI labels for Document Explanation.
 * Supports: en, hi, gu (hinglish/gujlish use en labels).
 * No external i18n library needed.
 */

export interface ExplainStrings {
  badgeNew: string;
  pageTitle: string;
  pageSubtitle: string;
  privacyNotice: string;
  privacyLink: string;

  // Dropzone & Input
  uploadTab: string;
  pasteTab: string;
  dropzoneTitle: string;
  dropzoneHint: string;
  dragDropPrompt?: string;
  supportedFormats: string;
  fileSizeLimit: string;
  pastePlaceholder: string;
  videoOptionLabel?: string;
  videoOptionHint?: string;
  generateVideoStoryboard?: string;
  videoOptionDesc?: string;
  crosscheckLabel: string;
  crosscheckHint: string;
  crosscheckOption?: string;
  crosscheckOptionDesc?: string;
  trySampleBtn: string;
  trySampleDemo?: string;
  submitBtn: string;
  explainButton?: string;
  loadingReading: string;
  analyzingDocument?: string;
  loadingSimplifying: string;
  loadingDiagrams: string;
  timeoutError: string;
  fileTooLargeError: string;
  unsupportedFileError: string;
  emptyInputError: string;

  // Tabs
  tabSummary: string;
  tabDiagrams: string;
  tabVideo: string;
  tabGlossary: string;
  tabDetails: string;

  // Summary
  docTypeDetected: string;
  keyTakeaways: string;
  actionableSteps: string;
  whereInDoc: string;
  closeEvidence: string;

  // Categories
  catFee: string;
  catObligation: string;
  catDeadline: string;
  catRisk: string;
  catRight: string;
  catOther: string;

  // Diagrams
  flowchartTitle: string;
  moneyFlowTitle: string;
  timelineTitle: string;
  noDiagramsAvailable: string;
  downloadPngBtn: string;

  // Video Explainer
  composeVideoBtn: string;
  cancelComposeBtn: string;
  composingProgress: string;
  downloadVideoBtn: string;
  playLiveAudioBtn: string;
  stopVoiceBtn: string;
  captionsToggle: string;
  captionsOn: string;
  captionsOff: string;
  silentNotice: string;
  unsupportedBrowserNotice: string;

  // Glossary
  searchGlossaryPlaceholder: string;
  noGlossaryMatches: string;
  termEvidenceLabel: string;

  // Details & Banners
  confidenceNotesTitle: string;
  ocrQualityTitle: string;
  degradedBannerTitle: string;
  redFlagsDetectedTitle: string;
  noRedFlagsTitle: string;
  registrySnapshotTitle: string;
  registryNotConfirmed: string;
  runFullCheckBtn: string;
  scamCheckLaunched: string;

  // Disclaimer
  disclaimerTitle: string;
}

export const EXPLAIN_STRINGS: Record<"en" | "hi" | "gu", ExplainStrings> = {
  en: {
    badgeNew: "NEW",
    pageTitle: "Explain a Document",
    pageSubtitle:
      "Upload any loan agreement, insurance policy, legal notice, or contract. Ruko provides a plain-language summary, glossary, diagrams, and video walkthrough.",
    privacyNotice: "Processed in memory. Nothing is saved to disk or database.",
    privacyLink: "Privacy details",

    uploadTab: "Upload Document",
    pasteTab: "Paste Text",
    dropzoneTitle: "Drop your PDF, DOCX, or Image here",
    dropzoneHint: "or click to browse from your device",
    dragDropPrompt: "Drop your PDF, DOCX, or Image here, or click to browse",
    supportedFormats: "Supports PDF (.pdf), Word (.docx), PNG, JPG, WEBP",
    fileSizeLimit: "Maximum file size: 10 MB (up to 20 pages)",
    pastePlaceholder:
      "Paste the text of your loan agreement, insurance policy, notice, or financial contract here...",
    videoOptionLabel: "Generate Storyboard & Video Walkthrough",
    videoOptionHint: "Creates scene narration and visual breakdown for video walkthrough",
    generateVideoStoryboard: "Generate Storyboard & Video Walkthrough",
    videoOptionDesc: "Creates scene narration and visual breakdown for video walkthrough",
    crosscheckLabel: "Also check this document for scam red flags",
    crosscheckHint: "Runs Ruko's 12 red-flag detectors and SEBI registry matching in parallel.",
    crosscheckOption: "Also check this document for scam red flags",
    crosscheckOptionDesc: "Runs Ruko's 12 red-flag detectors and SEBI registry matching in parallel.",
    trySampleBtn: "Try a sample loan agreement",
    trySampleDemo: "Try a sample loan agreement",
    submitBtn: "Explain Document",
    explainButton: "Explain Document",
    loadingReading: "Reading and extracting document text...",
    analyzingDocument: "Analyzing Document...",
    loadingSimplifying: "Simplifying clauses and terms...",
    loadingDiagrams: "Drawing process flows and diagrams...",
    timeoutError:
      "Document explanation timed out after 90 seconds. Please try a shorter excerpt or paste the text directly.",
    fileTooLargeError: "File exceeds the 10 MB limit. Please select a smaller file.",
    unsupportedFileError:
      "Unsupported file format. Please upload a PDF, DOCX, or Image (PNG/JPG/WEBP).",
    emptyInputError: "Please provide a document file or paste document text.",

    tabSummary: "Summary",
    tabDiagrams: "Diagrams",
    tabVideo: "Video Walkthrough",
    tabGlossary: "Glossary",
    tabDetails: "Details & Red Flags",

    docTypeDetected: "Document Type",
    keyTakeaways: "Key Clauses & Takeaways",
    actionableSteps: "Important Next Steps",
    whereInDoc: "Where in the document?",
    closeEvidence: "Hide evidence",

    catFee: "Fees & Charges",
    catObligation: "Obligations",
    catDeadline: "Deadlines",
    catRisk: "Risks & Penalties",
    catRight: "Your Rights",
    catOther: "Key Term",

    flowchartTitle: "Process Flowchart",
    moneyFlowTitle: "Payment & Fund Flow",
    timelineTitle: "Important Milestones & Dates",
    noDiagramsAvailable: "No specific diagram representations identified in this document.",
    downloadPngBtn: "Download PNG",

    composeVideoBtn: "Generate Browser Video",
    cancelComposeBtn: "Cancel",
    composingProgress: "Rendering video frames and voice...",
    downloadVideoBtn: "Download Video (.webm)",
    playLiveAudioBtn: "Play with Live Voice & Captions",
    stopVoiceBtn: "Stop Voice",
    captionsToggle: "Captions",
    captionsOn: "Captions ON",
    captionsOff: "Captions OFF",
    silentNotice:
      "Note: Live browser voice synthesis cannot be recorded into the video file. The downloaded video includes visual diagrams and synced captions.",
    unsupportedBrowserNotice:
      "Your browser does not support in-browser video encoding (MediaRecorder / captureStream). You can still play the interactive live scene player with voice and captions.",

    searchGlossaryPlaceholder: "Search financial and legal terms...",
    noGlossaryMatches: "No terms match your search query.",
    termEvidenceLabel: "Verbatim quote:",

    confidenceNotesTitle: "Analysis Notes & Limitations",
    ocrQualityTitle: "OCR Text Extraction Quality",
    degradedBannerTitle: "Service Notices",
    redFlagsDetectedTitle: "Crosscheck: Potential Red Flags Identified",
    noRedFlagsTitle: "Crosscheck: No active red-flag patterns matched.",
    registrySnapshotTitle: "SEBI Snapshot Intermediary Verification",
    registryNotConfirmed:
      "The claimed registration details could not be confirmed in our dated SEBI intermediary snapshot.",
    runFullCheckBtn: "Run full scam analysis on this document",
    scamCheckLaunched: "Running scam check with original document text...",

    disclaimerTitle: "Educational Notice & Disclaimer",
  },

  hi: {
    badgeNew: "नया",
    pageTitle: "दस्तावेज़ को आसान भाषा में समझें",
    pageSubtitle:
      "कोई भी लोन एग्रीमेंट, बीमा पॉलिसी, कानूनी नोटिस या कॉन्ट्रैक्ट अपलोड करें। रुको सरल सारांश, शब्दावली, आरेख (डायग्राम) और वीडियो प्रदान करता है।",
    privacyNotice: "सुरक्षित मेमोरी में प्रोसेस किया गया। कुछ भी सेव नहीं किया जाता।",
    privacyLink: "गोपनीयता विवरण",

    uploadTab: "दस्तावेज़ अपलोड करें",
    pasteTab: "टेक्स्ट पेस्ट करें",
    dropzoneTitle: "अपनी PDF, DOCX या इमेज यहाँ डालें",
    dropzoneHint: "या अपने डिवाइस से चुनने के लिए क्लिक करें",
    dragDropPrompt: "अपनी PDF, DOCX या इमेज यहाँ डालें या क्लिक करें",
    supportedFormats: "PDF (.pdf), Word (.docx), PNG, JPG, WEBP समर्थित हैं",
    fileSizeLimit: "अधिकतम फ़ाइल साइज़: 10 MB (20 पृष्ठों तक)",
    pastePlaceholder: "अपने लोन समझौते, बीमा पॉलिसी या नोटिस का टेक्स्ट यहाँ पेस्ट करें...",
    videoOptionLabel: "स्टोरीबोर्ड और वीडियो विवरण बनाएं",
    videoOptionHint: "दृश्य दर दृश्य व्याख्या और आरेख तैयार करता है",
    generateVideoStoryboard: "स्टोरीबोर्ड और वीडियो विवरण बनाएं",
    videoOptionDesc: "दृश्य दर दृश्य व्याख्या और आरेख तैयार करता है",
    crosscheckLabel: "धोखाधड़ी के लाल झंडों (रेड-फ्लैग) के लिए भी जाँचें",
    crosscheckHint: "रुको के 12 रेड-फ्लैग नियमों और सेबी (SEBI) स्नैपशॉट से एक साथ मिलान करता है।",
    crosscheckOption: "धोखाधड़ी के लाल झंडों (रेड-फ्लैग) के लिए भी जाँचें",
    crosscheckOptionDesc: "रुको के 12 रेड-फ्लैग नियमों और सेबी (SEBI) स्नैपशॉट से एक साथ मिलान करता है।",
    trySampleBtn: "नमूना लोन समझौता आज़माएं",
    trySampleDemo: "नमूना लोन समझौता आज़माएं",
    submitBtn: "दस्तावेज़ समझें",
    explainButton: "दस्तावेज़ समझें",
    loadingReading: "दस्तावेज़ का टेक्स्ट पढ़ा जा रहा है...",
    analyzingDocument: "दस्तावेज़ का विश्लेषण हो रहा है...",
    loadingSimplifying: "शर्तों और नियमों को सरल बनाया जा रहा है...",
    loadingDiagrams: "प्रक्रिया चार्ट और डायग्राम तैयार किए जा रहे हैं...",
    timeoutError:
      "दस्तावेज़ विश्लेषण में 90 सेकंड से अधिक समय लगा। कृपया छोटा अंश या सीधा टेक्स्ट पेस्ट करें।",
    fileTooLargeError: "फ़ाइल 10 MB से बड़ी है। कृपया छोटी फ़ाइल चुनें।",
    unsupportedFileError:
      "असमर्थित फ़ाइल प्रारूप। कृपया PDF, DOCX या इमेज (PNG/JPG/WEBP) अपलोड करें।",
    emptyInputError: "कृपया दस्तावेज़ फ़ाइल चुनें या टेक्स्ट पेस्ट करें।",

    tabSummary: "सारांश",
    tabDiagrams: "डायग्राम",
    tabVideo: "वीडियो विवरण",
    tabGlossary: "शब्दावली",
    tabDetails: "विवरण और जोखिम",

    docTypeDetected: "दस्तावेज़ का प्रकार",
    keyTakeaways: "मुख्य शर्तें और निष्कर्ष",
    actionableSteps: "ज़रूरी अगले कदम",
    whereInDoc: "दस्तावेज़ में कहाँ लिखा है?",
    closeEvidence: "प्रमाण छुपाएं",

    catFee: "शुल्क और खर्चे",
    catObligation: "आपकी जिम्मेदारियां",
    catDeadline: "समय सीमा",
    catRisk: "जोखिम और पेनल्टी",
    catRight: "आपके अधिकार",
    catOther: "मुख्य शर्त",

    flowchartTitle: "प्रक्रिया फ़्लोचार्ट",
    moneyFlowTitle: "भुगतान प्रवाह",
    timelineTitle: "महत्वपूर्ण समय सीमा और तिथियां",
    noDiagramsAvailable: "इस दस्तावेज़ में कोई विशिष्ट डायग्राम नहीं मिला।",
    downloadPngBtn: "PNG डाउनलोड करें",

    composeVideoBtn: "ब्राउज़र वीडियो तैयार करें",
    cancelComposeBtn: "रद्द करें",
    composingProgress: "वीडियो फ़्रेम और आवाज़ तैयार हो रही है...",
    downloadVideoBtn: "वीडियो डाउनलोड करें (.webm)",
    playLiveAudioBtn: "लाइव आवाज़ और कैप्शन के साथ चलाएं",
    stopVoiceBtn: "आवाज़ बंद करें",
    captionsToggle: "कैप्शन",
    captionsOn: "कैप्शन चालू",
    captionsOff: "कैप्शन बंद",
    silentNotice:
      "नोट: ब्राउज़र की लाइव आवाज़ को सीधे वीडियो फ़ाइल में रिकॉर्ड नहीं किया जा सकता। डाउनलोड किए गए वीडियो में डायग्राम और सबटाइटल शामिल रहेंगे।",
    unsupportedBrowserNotice:
      "आपका ब्राउज़र वीडियो एन्कोडिंग (MediaRecorder) का समर्थन नहीं करता है। आप लाइव इंटरैक्टिव प्लेयर का उपयोग कर सकते हैं।",

    searchGlossaryPlaceholder: "वित्तीय और कानूनी शब्द खोजें...",
    noGlossaryMatches: "कोई शब्द नहीं मिला।",
    termEvidenceLabel: "मूल दस्तावेज़ से उद्धरण:",

    confidenceNotesTitle: "विश्लेषण टिप्पणियां और सीमाएं",
    ocrQualityTitle: "ओसीआर टेक्स्ट निष्कर्षण गुणवत्ता",
    degradedBannerTitle: "सिस्टम सूचनाएं",
    redFlagsDetectedTitle: "क्रॉसचेक: संभावित रेड-फ्लैग पाए गए",
    noRedFlagsTitle: "क्रॉसचेक: कोई जाना-पहचाना रेड-फ्लैग पैटर्न नहीं मिला।",
    registrySnapshotTitle: "सेबी (SEBI) स्नैपशॉट सत्यापन",
    registryNotConfirmed: "दावा किया गया रजिस्ट्रेशन नंबर हमारे सेबी स्नैपशॉट में नहीं मिला।",
    runFullCheckBtn: "इस दस्तावेज़ की पूरी स्कैम जांच करें",
    scamCheckLaunched: "मूल टेक्स्ट के साथ स्कैम जांच शुरू की जा रही है...",

    disclaimerTitle: "शैक्षणिक सूचना और डिस्क्लेमर",
  },

  gu: {
    badgeNew: "નવું",
    pageTitle: "દસ્તાવેજને સરળ ભાષામાં સમજો",
    pageSubtitle:
      "કોઈપણ લોન કરાર, વીમા પોલિસી, કાનૂની નોટિસ કે કરાર અપલોડ કરો. રૂકો સરળ સારાંશ, શબ્દાવલી, ડાયાગ્રામ અને વિડિઓ પ્રદાન કરે છે.",
    privacyNotice: "સુરક્ષિત મેમરીમાં પ્રોસેસ થયેલ. કંઈપણ સેવ કરવામાં આવતું નથી.",
    privacyLink: "ગોપનીયતા વિગતો",

    uploadTab: "દસ્તાવેજ અપલોડ કરો",
    pasteTab: "ટેક્સ્ટ પેસ્ટ કરો",
    dropzoneTitle: "તમારી PDF, DOCX અથવા ઇમેજ અહીં મૂકો",
    dropzoneHint: "અથવા તમારા ડિવાઇસમાંથી પસંદ કરવા ક્લિક કરો",
    dragDropPrompt: "તમારી PDF, DOCX અથવા ઇમેજ અહીં મૂકો અથવા ક્લિક કરો",
    supportedFormats: "PDF (.pdf), Word (.docx), PNG, JPG, WEBP સપોર્ટેડ છે",
    fileSizeLimit: "મહત્તમ ફાઇલ સાઇઝ: 10 MB (20 પૃષ્ઠો સુધી)",
    pastePlaceholder: "તમારા લોન કરાર, વીમા પોલિસી કે નોટિસનો ટેક્સ્ટ અહીં પેસ્ટ કરો...",
    videoOptionLabel: "સ્ટોરીબોર્ડ અને વિડિઓ વિવરણ બનાવો",
    videoOptionHint: "દ્રશ્યવાર સમજૂતી અને ડાયાગ્રામ તૈયાર કરે છે",
    generateVideoStoryboard: "સ્ટોરીબોર્ડ અને વિડિઓ વિવરણ બનાવો",
    videoOptionDesc: "દ્રશ્યવાર સમજૂતી અને ડાયાગ્રામ તૈયાર કરે છે",
    crosscheckLabel: "છેતરપિંડીના સંકેતો (રેડ-ફ્લેગ) માટે પણ તપાસો",
    crosscheckHint: "રૂકોના 12 રેડ-ફ્લેગ નિયમો અને સેબી (SEBI) સ્નેપશોટ સાથે સરખામણી કરે છે.",
    crosscheckOption: "છેતરપિંડીના સંકેતો (રેડ-ફ્લેગ) માટે પણ તપાસો",
    crosscheckOptionDesc: "રૂકોના 12 રેડ-ફ્લેગ નિયમો અને સેબી (SEBI) સ્નેપશોટ સાથે સરખામણી કરે છે.",
    trySampleBtn: "નમૂના લોન કરાર અજમાવો",
    trySampleDemo: "નમૂના લોન કરાર અજમાવો",
    submitBtn: "દસ્તાવેજ સમજો",
    explainButton: "દસ્તાવેજ સમજો",
    loadingReading: "દસ્તાવેજનો ટેક્સ્ટ વાંચવામાં આવી રહ્યો છે...",
    analyzingDocument: "દસ્તાવેજનું વિશ્લેષણ થઈ રહ્યું છે...",
    loadingSimplifying: "શરતો અને નિયમો સરળ બનાવવામાં આવી રહ્યા છે...",
    loadingDiagrams: "પ્રોસેસ ચાર્ટ અને ડાયાગ્રામ તૈયાર થઈ રહ્યા છે...",
    timeoutError:
      "દસ્તાવેજ વિશ્લેષણમાં 90 સેકન્ડથી વધુ સમય લાગ્યો. કૃપા કરીને નાનો ભાગ અથવા સીધો ટેક્સ્ટ પેસ્ટ કરો.",
    fileTooLargeError: "ફાઇલ 10 MB કરતાં મોટી છે. કૃપા કરીને નાની ફાઇલ પસંદ કરો.",
    unsupportedFileError:
      "અસમર્થિત ફાઇલ ફોર્મેટ. કૃપા કરીને PDF, DOCX અથવા ઇમેજ (PNG/JPG/WEBP) અપલોડ કરો.",
    emptyInputError: "કૃપા કરીને દસ્તાવેજ ફાઇલ પસંદ કરો અથવા ટેક્સ્ટ પેસ્ટ કરો.",

    tabSummary: "સારાંશ",
    tabDiagrams: "ડાયાગ્રામ",
    tabVideo: "વિડિઓ માર્ગદર્શન",
    tabGlossary: "શબ્દાવલી",
    tabDetails: "વિગતો અને જોખમો",

    docTypeDetected: "દસ્તાવેજનો પ્રકાર",
    keyTakeaways: "મુખ્ય શરતો અને તારણો",
    actionableSteps: "મહત્વપૂર્ણ આગલા પગલાં",
    whereInDoc: "દસ્તાવેજમાં ક્યાં લખેલું છે?",
    closeEvidence: "પુરાવો છુપાવો",

    catFee: "ફી અને ચાર્જ",
    catObligation: "તમારી જવાબદારીઓ",
    catDeadline: "સમય મર્યાદા",
    catRisk: "જોખમો અને દંડ",
    catRight: "તમારા અધિકારો",
    catOther: "મુખ્ય શરત",

    flowchartTitle: "પ્રક્રિયા ફ્લોચાર્ટ",
    moneyFlowTitle: "ચુકવણી પ્રવાહ",
    timelineTitle: "મહત્વપૂર્ણ સમયરેખા અને તારીખો",
    noDiagramsAvailable: "આ દસ્તાવેજમાં કોઈ ચોક્કસ ડાયાગ્રામ મળ્યો નથી.",
    downloadPngBtn: "PNG ડાઉનલોડ કરો",

    composeVideoBtn: "બ્રાઉઝર વિડિઓ બનાવો",
    cancelComposeBtn: "રદ કરો",
    composingProgress: "વિડિઓ ફ્રેમ્સ અને અવાજ તૈયાર થઈ રહ્યા છે...",
    downloadVideoBtn: "વિડિઓ ડાઉનલોડ કરો (.webm)",
    playLiveAudioBtn: "લાઇવ અવાજ અને કૅપ્શન સાથે ચલાવો",
    stopVoiceBtn: "અવાજ બંધ કરો",
    captionsToggle: "કૅપ્શન",
    captionsOn: "કૅપ્શન ચાલુ",
    captionsOff: "કૅપ્શન બંધ",
    silentNotice:
      "નોંધ: બ્રાઉઝરનો લાઇવ અવાજ સીધો વિડિઓ ફાઇલમાં રેકોર્ડ કરી શકાતો નથી. ડાઉનલોડ કરેલ વિડિઓમાં ડાયાગ્રામ અને સબટાઈટલ સામેલ રહેશે.",
    unsupportedBrowserNotice:
      "તમારું બ્રાઉઝર વિડિઓ એન્કોડિંગ (MediaRecorder) ને સપોર્ટ કરતું નથી. તમે લાઇવ ઇન્ટરેક્ટિવ પ્લેયરનો ઉપયોગ કરી શકો છો.",

    searchGlossaryPlaceholder: "નાણાકીય અને કાનૂની શબ્દો શોધો...",
    noGlossaryMatches: "કોઈ શબ્દ મળ્યો નથી.",
    termEvidenceLabel: "મૂળ દસ્તાવેજમાંથી અવતરણ:",

    confidenceNotesTitle: "વિશ્લેષણ નોંધો અને મર્યાદાઓ",
    ocrQualityTitle: "OCR ટેક્સ્ટ નિષ્કર્ષણ ગુણવત્તા",
    degradedBannerTitle: "સિસ્ટમ સૂચનાઓ",
    redFlagsDetectedTitle: "ક્રોસચેક: સંભવિત રેડ-ફ્લેગ મળ્યા",
    noRedFlagsTitle: "ક્રોસચેક: કોઈ જાણીતા રેડ-ફ્લેગ પેટર્ન મળ્યા નથી.",
    registrySnapshotTitle: "સેબી (SEBI) સ્નેપશોટ ચકાસણી",
    registryNotConfirmed: "દાવા કરેલ રજીસ્ટ્રેશન વિગતો અમારા સેબી સ્નેપશોટમાં મળી નથી.",
    runFullCheckBtn: "આ દસ્તાવેજની સંપૂર્ણ સ્કેમ તપાસ કરો",
    scamCheckLaunched: "મૂળ ટેક્સ્ટ સાથે સ્કેમ તપાસ શરૂ કરી રહ્યા છીએ...",

    disclaimerTitle: "શૈક્ષણિક સૂચના અને ડિસ્ક્લેમર",
  },
};

export function getExplainStrings(language?: string): ExplainStrings {
  const lang = (language || "en").toLowerCase().trim();
  if (lang === "hi") return EXPLAIN_STRINGS.hi;
  if (lang === "gu") return EXPLAIN_STRINGS.gu;
  return EXPLAIN_STRINGS.en; // en, hinglish, gujlish all default to en labels
}
