/**
 * Multilingual typed strings for Breach Exposure Monitor (en, hi, gu)
 */

export interface BreachStrings {
  title: string;
  subtitle: string;
  dataSafetyBadge: string;
  dataSafetyNotice: string;
  safetyPillars: {
    minimalCollection: string;
    noCredentials: string;
    noRawLeaks: string;
    inMemoryOnly: string;
  };
  explainer: {
    title: string;
    collected: string;
    why: string;
    providers: string;
    noStorage: string;
    neverAsk: string;
  };
  form: {
    emailLabel: string;
    emailPlaceholder: string;
    consentCheckbox: string;
    submitButton: string;
    scanningButton: string;
    emailRequired: string;
    consentRequired: string;
  };
  results: {
    cleanTitle: string;
    cleanDesc: string;
    foundTitle: string;
    totalExposures: string;
    highRiskCount: string;
    financialCount: string;
    demoBadge: string;
    scanUnavailable: string;
    retryButton: string;
    financialWarningBadge: string;
    categoriesLabel: string;
    recommendedActions: string;
    remediationNotes: string;
    degradedWarning: string;
  };
  voiceAlert: {
    sectionTitle: string;
    sectionDesc: string;
    phoneLabel: string;
    phonePlaceholder: string;
    sendSmsButton: string;
    callCodeButton: string;
    sendingCode: string;
    smsSentNotice: string;
    callInitiatedNotice: string;
    smsUnavailableNotice: string;
    trialNotice: string;
    rateLimitNotice: string;
    invalidCodeNotice: string;
    codeInputLabel: string;
    codeInputPlaceholder: string;
    verifyCodeButton: string;
    verifyingCode: string;
    phoneVerifiedBadge: string;
    optInCheckbox: string;
    sendAlertButton: string;
    sendingAlert: string;
    alertSuccess: string;
    alertRejected: string;
    quietHoursNotice: string;
    simulatedBadge: string;
    playAlertButton: string;
    stopAlertButton: string;
    simulatedDesc: string;
  };
}

export const BREACH_STRINGS: Record<"en" | "hi" | "gu", BreachStrings> = {
  en: {
    title: "Breach Exposure Monitor",
    subtitle: "Check whether your email or personal data appeared in public data breaches. 100% stateless and zero storage.",
    dataSafetyBadge: "Data Safety Guarantee",
    dataSafetyNotice: "A breach exposure does not necessarily mean your account was compromised.",
    safetyPillars: {
      minimalCollection: "Minimal data collection",
      noCredentials: "No passwords or OTPs",
      noRawLeaks: "No raw leaked credentials stored",
      inMemoryOnly: "Nothing is saved: processed in memory",
    },
    explainer: {
      title: "How your data is protected during this check",
      collected: "What is collected: Only the email or phone number you input during this session.",
      why: "Why: To check against publicly known data breach indexes and verify voice alert authorization.",
      providers: "Providers: Evaluated via secure APIs (Have I Been Pwned / local mock) and Twilio Verify for phone verification.",
      noStorage: "Zero Persistence: Identifiers, responses, and tokens are processed exclusively in volatile memory and never saved to any database or disk.",
      neverAsk: "Never Asked: Ruko will NEVER ask for or accept your passwords, PINs, CVVs, banking credentials, or bank OTPs.",
    },
    form: {
      emailLabel: "Email Address",
      emailPlaceholder: "name@example.com",
      consentCheckbox: "I authorize Ruko to check external breach records for this email address. I understand that nothing will be stored or logged.",
      submitButton: "Check Exposure",
      scanningButton: "Scanning Breach Records...",
      emailRequired: "Please enter a valid email address.",
      consentRequired: "Consent is required to perform a breach exposure lookup.",
    },
    results: {
      cleanTitle: "No Exposures Found in Tested Records",
      cleanDesc: "This email address was not found in our indexed breach dataset. Note: Never consider any account permanently safe—always maintain strong unique passwords.",
      foundTitle: "Known Exposure Records Found",
      totalExposures: "Total Exposures",
      highRiskCount: "High-Risk Breaches",
      financialCount: "Financial Data Exposed",
      demoBadge: "Demo / Mock Data",
      scanUnavailable: "Scan unavailable, retry later.",
      retryButton: "Retry Scan",
      financialWarningBadge: "Financial Data Compromised",
      categoriesLabel: "Exposed Data Categories",
      recommendedActions: "Recommended Actions",
      remediationNotes: "Safety Guidelines",
      degradedWarning: "Some breach data providers were temporarily unreachable. Results may be incomplete.",
    },
    voiceAlert: {
      sectionTitle: "Automated Voice Alerts (Optional)",
      sectionDesc: "Receive an automated emergency phone call if critical high-risk exposures are detected.",
      phoneLabel: "Mobile Phone Number (with Country Code)",
      phonePlaceholder: "+91 98765 43210",
      sendSmsButton: "Send code by SMS",
      callCodeButton: "Call me with the code",
      sendingCode: "Sending Code...",
      smsSentNotice: "We sent a verification code by SMS. Please enter it below.",
      callInitiatedNotice: "We are placing a voice call to read your verification code. Please listen and enter it below.",
      smsUnavailableNotice: "SMS verification is currently unavailable for your number/carrier. Please try the 'Call me with the code' option.",
      trialNotice: "On this demo account, only phone numbers pre-approved by the organisers can receive codes.",
      rateLimitNotice: "Too many verification attempts. Please wait a few minutes before trying again.",
      invalidCodeNotice: "Invalid or expired verification code. Please check and try again.",
      codeInputLabel: "Verification Code (4-8 digits)",
      codeInputPlaceholder: "123456",
      verifyCodeButton: "Verify Code",
      verifyingCode: "Verifying...",
      phoneVerifiedBadge: "Phone Verified",
      optInCheckbox: "I opt in to receive automated voice alert calls when high-risk exposures are detected.",
      sendAlertButton: "Test Voice Alert Call",
      sendingAlert: "Placing Alert Call...",
      alertSuccess: "Voice alert call placed successfully.",
      alertRejected: "Alert call could not be placed.",
      quietHoursNotice: "Quiet Hours: Automated alert calls are suppressed between 21:00 and 08:00 IST to respect your privacy.",
      simulatedBadge: "SIMULATED ALERT (demo): no real call was placed",
      playAlertButton: "Play alert message",
      stopAlertButton: "Stop message",
      simulatedDesc: "This security alert message is simulated in your browser for demonstration purposes.",
    },
  },
  hi: {
    title: "डेटा उल्लंघन मॉनिटर",
    subtitle: "जाँचें कि क्या आपका ईमेल या व्यक्तिगत डेटा सार्वजनिक डेटा उल्लंघनों में शामिल था। 100% स्टेटलेस और शून्य स्टोरेज।",
    dataSafetyBadge: "डेटा सुरक्षा गारंटी",
    dataSafetyNotice: "डेटा उल्लंघन में शामिल होने का अनिवार्य रूप से यह मतलब नहीं है कि आपका खाता हैक हो गया है।",
    safetyPillars: {
      minimalCollection: "न्यूनतम डेटा संग्रह",
      noCredentials: "कोई पासवर्ड या ओटीपी नहीं",
      noRawLeaks: "कोई लीक क्रेडेंशियल सहेजा नहीं जाता",
      inMemoryOnly: "कुछ भी सहेजा नहीं जाता: मेमोरी में प्रोसेस किया गया",
    },
    explainer: {
      title: "इस जाँच के दौरान आपका डेटा कैसे सुरक्षित रहता है",
      collected: "क्या एकत्र किया जाता है: केवल वही ईमेल या फोन नंबर जो आप इस सत्र में दर्ज करते हैं।",
      why: "क्यों: ज्ञात उल्लंघन रिकॉर्ड की जाँच और वॉयस अलर्ट सत्यापन के लिए।",
      providers: "प्रदाता: हैव आई बीन पॉन्ड (HIBP) / मॉक और फोन सत्यापन हेतु ट्विलियो वेरीफाई।",
      noStorage: "शून्य स्टोरेज: पहचानकर्ता, परिणाम और टोकन केवल मेमोरी में रहते हैं और कभी डिस्क या डेटाबेस पर नहीं लिखे जाते।",
      neverAsk: "कभी नहीं माँगा जाता: रुको कभी भी आपसे पासवर्ड, पिन, सीवीवी, बैंकिंग क्रेडेंशियल या बैंक ओटीपी नहीं माँगेगा।",
    },
    form: {
      emailLabel: "ईमेल पता",
      emailPlaceholder: "name@example.com",
      consentCheckbox: "मैं रुको को इस ईमेल के लिए डेटाबेस की जाँच करने की अनुमति देता/देती हूँ। मैं समझता/समझती हूँ कि कुछ भी सहेजा नहीं जाएगा।",
      submitButton: "उल्लंघन की जाँच करें",
      scanningButton: "जाँच की जा रही है...",
      emailRequired: "कृपया एक मान्य ईमेल पता दर्ज करें।",
      consentRequired: "जाँच करने के लिए सहमति आवश्यक है।",
    },
    results: {
      cleanTitle: "कोई ज्ञात उल्लंघन नहीं मिला",
      cleanDesc: "यह ईमेल हमारे परीक्षण डेटासेट में नहीं मिला। हमेशा अद्वितीय और मजबूत पासवर्ड का उपयोग करें।",
      foundTitle: "डेटा उल्लंघन रिकॉर्ड मिले",
      totalExposures: "कुल उल्लंघन",
      highRiskCount: "उच्च-जोखिम उल्लंघन",
      financialCount: "वित्तीय डेटा प्रभावित",
      demoBadge: "डेमो डेटा",
      scanUnavailable: "स्कैन अनुपलब्ध है, कृपया पुनः प्रयास करें।",
      retryButton: "पुनः प्रयास करें",
      financialWarningBadge: "वित्तीय डेटा शामिल",
      categoriesLabel: "प्रभावित डेटा श्रेणियां",
      recommendedActions: "सुझाई गई कार्रवाइयां",
      remediationNotes: "सुरक्षा दिशानिर्देश",
      degradedWarning: "कुछ प्रदाता अस्थायी रूप से अनुपलब्ध थे। परिणाम आंशिक हो सकते हैं।",
    },
    voiceAlert: {
      sectionTitle: "स्वचालित वॉयस अलर्ट (वैकल्पिक)",
      sectionDesc: "यदि गंभीर उच्च-जोखिम जोखिम पाए जाते हैं तो स्वचालित आपातकालीन फोन कॉल प्राप्त करें।",
      phoneLabel: "मोबाइल नंबर (देश कोड सहित)",
      phonePlaceholder: "+91 98765 43210",
      sendSmsButton: "एसएमएस द्वारा कोड भेजें",
      callCodeButton: "कॉल द्वारा कोड प्राप्त करें",
      sendingCode: "कोड भेजा जा रहा है...",
      smsSentNotice: "हमने एसएमएस द्वारा सत्यापन कोड भेज दिया है। कृपया नीचे दर्ज करें।",
      callInitiatedNotice: "हम सत्यापन कोड बताने के लिए कॉल कर रहे हैं। कृपया सुनकर नीचे दर्ज करें।",
      smsUnavailableNotice: "आपके नंबर के लिए एसएमएस अनुपलब्ध है। कृपया 'कॉल द्वारा कोड प्राप्त करें' विकल्प चुनें।",
      trialNotice: "इस डेमो खाते पर, केवल आयोजकों द्वारा अनुमोदित फोन नंबर ही कोड प्राप्त कर सकते हैं।",
      rateLimitNotice: "बहुत अधिक प्रयास किए गए। कृपया कुछ मिनट प्रतीक्षा करें।",
      invalidCodeNotice: "अमान्य या समाप्त कोड। कृपया जाँच कर पुनः प्रयास करें।",
      codeInputLabel: "सत्यापन कोड (4-8 अंक)",
      codeInputPlaceholder: "123456",
      verifyCodeButton: "कोड सत्यापित करें",
      verifyingCode: "सत्यापित किया जा रहा है...",
      phoneVerifiedBadge: "फोन सत्यापित",
      optInCheckbox: "उच्च जोखिम की स्थिति में मैं स्वचालित वॉयस अलर्ट कॉल प्राप्त करने की सहमति देता/देती हूँ।",
      sendAlertButton: "वॉयस अलर्ट कॉल का परीक्षण करें",
      sendingAlert: "कॉल की जा रही है...",
      alertSuccess: "वॉयस अलर्ट कॉल सफलतापूर्वक भेजी गई।",
      alertRejected: "अलर्ट कॉल नहीं भेजी जा सकी।",
      quietHoursNotice: "शांत समय: आपकी गोपनीयता के लिए रात 21:00 से सुबह 08:00 IST के बीच अलर्ट कॉल नहीं की जाती हैं।",
      simulatedBadge: "सिम्युलेटेड अलर्ट (डेमो): कोई वास्तविक कॉल नहीं की गई",
      playAlertButton: "अलर्ट संदेश सुनें",
      stopAlertButton: "संदेश रोकें",
      simulatedDesc: "यह सुरक्षा अलर्ट संदेश केवल प्रदर्शन उद्देश्यों के लिए आपके ब्राउज़र में सिम्युलेट किया गया है।",
    },
  },
  gu: {
    title: "ડેટા બ્રીચ મોનિટર",
    subtitle: "તમારો ઇમેઇલ અથવા વ્યક્તિગત ડેટા જાણીતા લીક્સમાં સામેલ હતો કે કેમ તે તપાસો. 100% સ્ટેટલેસ અને શૂન્ય સંગ્રહ.",
    dataSafetyBadge: "ડેટા સલામતી ગેરંટી",
    dataSafetyNotice: "બ્રીચમાં સામેલ હોવાનો અર્થ એ નથી કે તમારું એકાઉન્ટ હેક થઈ ગયું છે.",
    safetyPillars: {
      minimalCollection: "ન્યૂનતમ ડેટા સંગ્રહ",
      noCredentials: "પાસવર્ડ કે ઓટીપી નહીં",
      noRawLeaks: "કોઈ લીક થયેલ ક્રેડેન્શિયલ સેવ થતું નથી",
      inMemoryOnly: "કંઈપણ સંગ્રહિત નથી: ફક્ત મેમરીમાં પ્રોસેસ થાય છે",
    },
    explainer: {
      title: "તમારો ડેટા કેવી રીતે સુરક્ષિત રહે છે",
      collected: "શું એકત્રિત કરવામાં આવે છે: ફક્ત તમે દાખલ કરેલ ઇમેઇલ અથવા ફોન નંબર.",
      why: "શા માટે: બ્રીચ રેકોર્ડ તપાસવા અને વોઇસ એલર્ટ ચકાસણી માટે.",
      providers: "પ્રોવાઇડર્સ: HIBP/મોક અને ફોન વેરિફિકેશન માટે ટ્વિલિયો વેરિફાય.",
      noStorage: "શૂન્ય સંગ્રહ: ઓળખકર્તાઓ અને પરિણામો ક્યારેય ડિસ્ક કે ડેટાબેઝમાં સાચવવામાં આવતા નથી.",
      neverAsk: "ક્યારેય પૂછવામાં આવતું નથી: રૂકો ક્યારેય પાસવર્ડ, પિન, સીવીવી, બેંકિંગ વિગતો કે ઓટીપી પૂછશે નહીં.",
    },
    form: {
      emailLabel: "ઇમેઇલ સરનામું",
      emailPlaceholder: "name@example.com",
      consentCheckbox: "હું આ ઇમેઇલ માટે બ્રીચ ડેટાબેઝ તપાસવાની મંજૂરી આપું છું. હું સમજું છું કે કંઈપણ સંગ્રહિત થશે નહીં.",
      submitButton: "તપાસ કરો",
      scanningButton: "તપાસ ચાલુ છે...",
      emailRequired: "કૃપા કરીને માન્ય ઇમેઇલ સરનામું દાખલ કરો.",
      consentRequired: "તપાસ માટે સંમતિ આવશ્યક છે.",
    },
    results: {
      cleanTitle: "કોઈ બ્રીચ રેકોર્ડ મળ્યો નથી",
      cleanDesc: "આ ઇમેઇલ અમારા ડેટાસેટમાં મળ્યો નથી. હંમેશા મજબૂત પાસવર્ડ વાપરો.",
      foundTitle: "જાણીતા બ્રીચ રેકોર્ડ્સ મળ્યા",
      totalExposures: "કુલ બ્રીચ",
      highRiskCount: "ઉચ્ચ જોખમ",
      financialCount: "નાણાકીય ડેટા સામેલ",
      demoBadge: "ડેમો ડેટા",
      scanUnavailable: "સ્કેન અનુપલબ્ધ છે, ફરી પ્રયાસ કરો.",
      retryButton: "ફરી પ્રયાસ કરો",
      financialWarningBadge: "નાણાકીય માહિતી ખુલ્લી પડી છે",
      categoriesLabel: "સંકળાયેલ ડેટા શ્રેણીઓ",
      recommendedActions: "ભલામણ કરેલ પગલાં",
      remediationNotes: "સુરક્ષા માર્ગદર્શિકા",
      degradedWarning: "કેટલાક પ્રદાતાઓ અનુપલબ્ધ હતા. પરિણામો અધૂરા હોઈ શકે છે.",
    },
    voiceAlert: {
      sectionTitle: "સ્વચાલિત વૉઇસ એલર્ટ (વૈકલ્પિક)",
      sectionDesc: "જો ગંભીર ઉચ્ચ-જોખમ મળે તો સ્વચાલિત ફોન કૉલ મેળવો.",
      phoneLabel: "મોબાઇલ નંબર (દેશના કોડ સાથે)",
      phonePlaceholder: "+91 98765 43210",
      sendSmsButton: "એસએમએસ દ્વારા કોડ મોકલો",
      callCodeButton: "કૉલ દ્વારા કોડ મેળવો",
      sendingCode: "કોડ મોકલવામાં આવી રહ્યો છે...",
      smsSentNotice: "અમે એસએમએસ દ્વારા કોડ મોકલ્યો છે. કૃપા કરીને નીચે લખો.",
      callInitiatedNotice: "અમે કોડ બોલવા માટે કૉલ કરી રહ્યા છીએ. કૃપા કરીને સાંભળીને નીચે લખો.",
      smsUnavailableNotice: "તમારા નંબર માટે એસએમએસ અનુપલબ્ધ છે. કૃપા કરીને 'કૉલ દ્વારા કોડ મેળવો' વિકલ્પ પસંદ કરો.",
      trialNotice: "આ ડેમો એકાઉન્ટ પર, ફક્ત પૂર્વ-મંજૂર ફોન નંબર જ કોડ મેળવી શકે છે.",
      rateLimitNotice: "ખૂબ વધુ પ્રયાસો. કૃપા કરીને થોડીવાર રાહ જુઓ.",
      invalidCodeNotice: "અમાન્ય અથવા સમાપ્ત થયેલ કોડ. કૃપા કરીને ફરી પ્રયાસ કરો.",
      codeInputLabel: "ચકાસણી કોડ (4-8 અંક)",
      codeInputPlaceholder: "123456",
      verifyCodeButton: "કોડ ચકાસો",
      verifyingCode: "ચકાસણી ચાલુ છે...",
      phoneVerifiedBadge: "ફોન ચકાસાયેલ છે",
      optInCheckbox: "ઉચ્ચ જોખમની સ્થિતિમાં સ્વચાલિત વૉઇસ કૉલ મેળવવા માટે હું સંમત છું.",
      sendAlertButton: "ટેસ્ટ વૉઇસ એલર્ટ કૉલ કરો",
      sendingAlert: "કૉલ કરવામાં આવી રહ્યો છે...",
      alertSuccess: "વૉઇસ એલર્ટ કૉલ સફળતાપૂર્વક મોકલવામાં આવ્યો.",
      alertRejected: "એલર્ટ કૉલ મોકલી શકાયો નહીં.",
      quietHoursNotice: "શાંત સમય: રાત્રે 21:00 થી સવારે 08:00 IST વચ્ચે એલર્ટ કૉલ બંધ રહેશે.",
      simulatedBadge: "સિમ્યુલેટેડ એલર્ટ (ડેમો): કોઈ વાસ્તવિક કૉલ કરવામાં આવ્યો નથી",
      playAlertButton: "એલર્ટ સંદેશ સાંભળો",
      stopAlertButton: "સંદેશ રોકો",
      simulatedDesc: "આ સુરક્ષા એલર્ટ સંદેશ ફક્ત ડેમો હેતુ માટે બ્રાઉઝરમાં સિમ્યુલેટ કરવામાં આવ્યો છે.",
    },
  },
};
