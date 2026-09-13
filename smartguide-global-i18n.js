/* BIS SmartGuide global UI translation layer v1 */
(() => {
  'use strict';
  const dictionaries = {
    English: {
      'Overview':'Overview','Browse Standards':'Browse Standards','Standards':'Standards','Compliance':'Compliance','Compliance Passport':'Compliance Passport','Mandatory / QCO':'Mandatory / QCO','BIS Certification':'BIS Certification','Find a Laboratory':'Find a Laboratory','Analyze a Document':'Analyze a Document','Explore Connections':'Explore Connections','Consumer Services':'Consumer Services','QR / Barcode':'QR / Barcode','Report Studio':'Report Studio','Analytics':'Analytics','Advanced Features':'Advanced Features','AI Assistant':'AI Assistant','Find a standard':'Find a standard','Verify ISI / CM/L':'Verify ISI / CM/L','Find a laboratory':'Find a laboratory','Analyze a document':'Analyze a document','Check mandatory rules':'Check mandatory rules','Ask SmartGuide':'Ask SmartGuide','New to BIS compliance?':'New to BIS compliance?','Knowledge Engine':'Knowledge Engine','Agentic RAG':'Agentic RAG','System Online':'System Online','Startup / Innovator':'Startup / Innovator','Manufacturer':'Manufacturer','Consumer':'Consumer','Importer':'Importer','Procurement':'Procurement','Student':'Student','Laboratory':'Laboratory','English':'English','Hindi':'Hindi','Kannada':'Kannada','Telugu':'Telugu','Tamil':'Tamil','Clear':'Clear','Voice input':'Voice input','Auto Speak: ON':'Auto Speak: ON','Stop':'Stop','Listen':'Listen','Confidence':'Confidence','Support level':'Support level','Evidence Trail':'Evidence Trail','Product Intelligence':'Product Intelligence','Product':'Product','Standard':'Standard','Requirements':'Requirements','Certification':'Certification','Laboratory':'Laboratory','Documents':'Documents','Check':'Check','Search':'Search','Submit':'Submit','Loading':'Loading','No results found':'No results found'},
    Hindi: {
      'Overview':'अवलोकन','Browse Standards':'मानक ब्राउज़ करें','Standards':'मानक','Compliance':'अनुपालन','Compliance Passport':'अनुपालन पासपोर्ट','Mandatory / QCO':'अनिवार्य / QCO','BIS Certification':'BIS प्रमाणन','Find a Laboratory':'प्रयोगशाला खोजें','Analyze a Document':'दस्तावेज़ का विश्लेषण करें','Explore Connections':'कनेक्शन देखें','Consumer Services':'उपभोक्ता सेवाएँ','QR / Barcode':'QR / बारकोड','Report Studio':'रिपोर्ट स्टूडियो','Analytics':'विश्लेषण','Advanced Features':'उन्नत सुविधाएँ','AI Assistant':'AI सहायक','Find a standard':'मानक खोजें','Verify ISI / CM/L':'ISI / CM/L सत्यापित करें','Find a laboratory':'प्रयोगशाला खोजें','Analyze a document':'दस्तावेज़ का विश्लेषण करें','Check mandatory rules':'अनिवार्य नियम जाँचें','Ask SmartGuide':'SmartGuide से पूछें','New to BIS compliance?':'BIS अनुपालन में नए हैं?','Knowledge Engine':'ज्ञान इंजन','Agentic RAG':'एजेंटिक RAG','System Online':'सिस्टम ऑनलाइन','Startup / Innovator':'स्टार्टअप / नवप्रवर्तक','Clear':'साफ़ करें','Voice input':'आवाज़ से इनपुट','Auto Speak: ON':'ऑटो स्पीक: चालू','Stop':'रोकें','Listen':'सुनें','Confidence':'विश्वास स्तर','Support level':'समर्थन स्तर','Evidence Trail':'साक्ष्य विवरण','Product Intelligence':'उत्पाद बुद्धिमत्ता','Product':'उत्पाद','Standard':'मानक','Requirements':'आवश्यकताएँ','Certification':'प्रमाणन','Laboratory':'प्रयोगशाला','Documents':'दस्तावेज़','Check':'जाँचें','Search':'खोजें','Submit':'जमा करें','Loading':'लोड हो रहा है','No results found':'कोई परिणाम नहीं मिला','English':'अंग्रेज़ी','Hindi':'हिंदी','Kannada':'कन्नड़','Telugu':'तेलुगु','Tamil':'तमिल'},
    Kannada: {
      'Overview':'ಅವಲೋಕನ','Browse Standards':'ಮಾನದಂಡಗಳನ್ನು ಬ್ರೌಸ್ ಮಾಡಿ','Standards':'ಮಾನದಂಡಗಳು','Compliance':'ಅನುಸರಣೆ','Compliance Passport':'ಅನುಸರಣೆ ಪಾಸ್‌ಪೋರ್ಟ್','Mandatory / QCO':'ಕಡ್ಡಾಯ / QCO','BIS Certification':'BIS ಪ್ರಮಾಣೀಕರಣ','Find a Laboratory':'ಪ್ರಯೋಗಾಲಯ ಹುಡುಕಿ','Analyze a Document':'ದಾಖಲೆ ವಿಶ್ಲೇಷಿಸಿ','Explore Connections':'ಸಂಪರ್ಕಗಳನ್ನು ಅನ್ವೇಷಿಸಿ','Consumer Services':'ಗ್ರಾಹಕ ಸೇವೆಗಳು','QR / Barcode':'QR / ಬಾರ್‌ಕೋಡ್','Report Studio':'ವರದಿ ಸ್ಟುಡಿಯೋ','Analytics':'ವಿಶ್ಲೇಷಣೆ','Advanced Features':'ಮುನ್ನಡೆದ ವೈಶಿಷ್ಟ್ಯಗಳು','AI Assistant':'AI ಸಹಾಯಕ','Find a standard':'ಮಾನದಂಡ ಹುಡುಕಿ','Verify ISI / CM/L':'ISI / CM/L ಪರಿಶೀಲಿಸಿ','Find a laboratory':'ಪ್ರಯೋಗಾಲಯ ಹುಡುಕಿ','Analyze a document':'ದಾಖಲೆ ವಿಶ್ಲೇಷಿಸಿ','Check mandatory rules':'ಕಡ್ಡಾಯ ನಿಯಮಗಳನ್ನು ಪರಿಶೀಲಿಸಿ','Ask SmartGuide':'SmartGuide ಅನ್ನು ಕೇಳಿ','New to BIS compliance?':'BIS ಅನುಸರಣೆಯಲ್ಲಿ ಹೊಸಬರೇ?','Knowledge Engine':'ಜ್ಞಾನ ಎಂಜಿನ್','Agentic RAG':'ಏಜೆಂಟಿಕ್ RAG','System Online':'ಸಿಸ್ಟಮ್ ಆನ್‌ಲೈನ್','Startup / Innovator':'ಸ್ಟಾರ್ಟ್‌ಅಪ್ / ನವೋದ್ಯಮಿ','Clear':'ತೆರವುಗೊಳಿಸಿ','Voice input':'ಧ್ವನಿ ಇನ್‌ಪುಟ್','Auto Speak: ON':'ಆಟೋ ಸ್ಪೀಕ್: ಆನ್','Stop':'ನಿಲ್ಲಿಸಿ','Listen':'ಕೇಳಿ','Confidence':'ವಿಶ್ವಾಸ ಮಟ್ಟ','Support level':'ಬೆಂಬಲ ಮಟ್ಟ','Evidence Trail':'ಸಾಕ್ಷ್ಯ ವಿವರ','Product Intelligence':'ಉತ್ಪನ್ನ ಬುದ್ಧಿಮತ್ತೆ','Product':'ಉತ್ಪನ್ನ','Standard':'ಮಾನದಂಡ','Requirements':'ಅವಶ್ಯಕತೆಗಳು','Certification':'ಪ್ರಮಾಣೀಕರಣ','Laboratory':'ಪ್ರಯೋಗಾಲಯ','Documents':'ದಾಖಲೆಗಳು','Check':'ಪರಿಶೀಲಿಸಿ','Search':'ಹುಡುಕಿ','Submit':'ಸಲ್ಲಿಸಿ','Loading':'ಲೋಡ್ ಆಗುತ್ತಿದೆ','No results found':'ಯಾವುದೇ ಫಲಿತಾಂಶ ಕಂಡುಬಂದಿಲ್ಲ','English':'ಇಂಗ್ಲಿಷ್','Hindi':'ಹಿಂದಿ','Kannada':'ಕನ್ನಡ','Telugu':'ತೆಲುಗು','Tamil':'ತಮಿಳು'},
    Telugu: {
      'Overview':'అవలోకనం','Browse Standards':'ప్రమాణాలను చూడండి','Standards':'ప్రమాణాలు','Compliance':'అనుసరణ','Compliance Passport':'అనుసరణ పాస్‌పోర్ట్','Mandatory / QCO':'తప్పనిసరి / QCO','BIS Certification':'BIS ధృవీకరణ','Find a Laboratory':'ప్రయోగశాలను కనుగొనండి','Analyze a Document':'పత్రాన్ని విశ్లేషించండి','Explore Connections':'కనెక్షన్లను చూడండి','Consumer Services':'వినియోగదారు సేవలు','QR / Barcode':'QR / బార్‌కోడ్','Report Studio':'రిపోర్ట్ స్టూడియో','Analytics':'విశ్లేషణ','Advanced Features':'అధునాతన ఫీచర్లు','AI Assistant':'AI సహాయకుడు','Find a standard':'ప్రమాణాన్ని కనుగొనండి','Verify ISI / CM/L':'ISI / CM/L ధృవీకరించండి','Find a laboratory':'ప్రయోగశాలను కనుగొనండి','Analyze a document':'పత్రాన్ని విశ్లేషించండి','Check mandatory rules':'తప్పనిసరి నియమాలను తనిఖీ చేయండి','Ask SmartGuide':'SmartGuide ను అడగండి','New to BIS compliance?':'BIS అనుసరణలో కొత్తవారా?','Knowledge Engine':'జ్ఞాన ఇంజిన్','Agentic RAG':'ఏజెంటిక్ RAG','System Online':'సిస్టమ్ ఆన్‌లైన్','Startup / Innovator':'స్టార్టప్ / ఆవిష్కర్త','Clear':'క్లియర్','Voice input':'వాయిస్ ఇన్‌పుట్','Auto Speak: ON':'ఆటో స్పీక్: ఆన్','Stop':'ఆపండి','Listen':'వినండి','Confidence':'నమ్మక స్థాయి','Support level':'మద్దతు స్థాయి','Evidence Trail':'ఆధారాల వివరాలు','Product Intelligence':'ఉత్పత్తి మేధస్సు','Product':'ఉత్పత్తి','Standard':'ప్రమాణం','Requirements':'అవసరాలు','Certification':'ధృవీకరణ','Laboratory':'ప్రయోగశాల','Documents':'పత్రాలు','Check':'తనిఖీ','Search':'వెతకండి','Submit':'సమర్పించండి','Loading':'లోడ్ అవుతోంది','No results found':'ఫలితాలు కనబడలేదు','English':'ఆంగ్లం','Hindi':'హిందీ','Kannada':'కన్నడ','Telugu':'తెలుగు','Tamil':'తమిళం'},
    Tamil: {
      'Overview':'கண்ணோட்டம்','Browse Standards':'தரநிலைகளை உலாவுக','Standards':'தரநிலைகள்','Compliance':'இணக்கம்','Compliance Passport':'இணக்க பாஸ்போர்ட்','Mandatory / QCO':'கட்டாயம் / QCO','BIS Certification':'BIS சான்றிதழ்','Find a Laboratory':'ஆய்வகத்தைக் கண்டறிக','Analyze a Document':'ஆவணத்தை பகுப்பாய்வு செய்க','Explore Connections':'இணைப்புகளைப் பார்க்கவும்','Consumer Services':'நுகர்வோர் சேவைகள்','QR / Barcode':'QR / பார்கோடு','Report Studio':'அறிக்கை ஸ்டுடியோ','Analytics':'பகுப்பாய்வு','Advanced Features':'மேம்பட்ட அம்சங்கள்','AI Assistant':'AI உதவியாளர்','Find a standard':'தரநிலையைக் கண்டறிக','Verify ISI / CM/L':'ISI / CM/L சரிபார்க்கவும்','Find a laboratory':'ஆய்வகத்தைக் கண்டறிக','Analyze a document':'ஆவணத்தை பகுப்பாய்வு செய்க','Check mandatory rules':'கட்டாய விதிகளைச் சரிபார்க்கவும்','Ask SmartGuide':'SmartGuide-ஐ கேளுங்கள்','New to BIS compliance?':'BIS இணக்கத்தில் புதியவரா?','Knowledge Engine':'அறிவு இயந்திரம்','Agentic RAG':'ஏஜென்டிக் RAG','System Online':'சிஸ்டம் ஆன்லைன்','Startup / Innovator':'ஸ்டார்ட்அப் / புதுமையாளர்','Clear':'அழி','Voice input':'குரல் உள்ளீடு','Auto Speak: ON':'தானியங்கி பேச்சு: ஆன்','Stop':'நிறுத்து','Listen':'கேளுங்கள்','Confidence':'நம்பிக்கை நிலை','Support level':'ஆதரவு நிலை','Evidence Trail':'ஆதார விவரம்','Product Intelligence':'தயாரிப்பு நுண்ணறிவு','Product':'தயாரிப்பு','Standard':'தரநிலை','Requirements':'தேவைகள்','Certification':'சான்றிதழ்','Laboratory':'ஆய்வகம்','Documents':'ஆவணங்கள்','Check':'சரிபார்க்கவும்','Search':'தேடுக','Submit':'சமர்ப்பிக்கவும்','Loading':'ஏற்றப்படுகிறது','No results found':'முடிவுகள் எதுவும் இல்லை','English':'ஆங்கிலம்','Hindi':'இந்தி','Kannada':'கன்னடம்','Telugu':'தெலுங்கு','Tamil':'தமிழ்'}
  };
  const original = new WeakMap();
  const getLang = () => document.getElementById('globalLang')?.value || 'English';
  const translateNode = (node, dict) => {
    if (node.nodeType !== Node.TEXT_NODE) return;
    const parent = node.parentElement;
    if (!parent || ['SCRIPT','STYLE','TEXTAREA'].includes(parent.tagName)) return;
    const raw = original.has(node) ? original.get(node) : node.nodeValue;
    if (!original.has(node)) original.set(node, raw);
    const trimmed = raw.trim();
    if (!trimmed || trimmed.length > 100) return;
    const translated = dict[trimmed];
    if (translated) node.nodeValue = raw.replace(trimmed, translated);
  };
  const apply = () => {
    const dict = dictionaries[getLang()] || dictionaries.English;
    document.documentElement.lang = getLang() === 'Hindi' ? 'hi' : getLang() === 'Kannada' ? 'kn' : getLang() === 'Telugu' ? 'te' : getLang() === 'Tamil' ? 'ta' : 'en';
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (!el.dataset.i18nOriginal) el.dataset.i18nOriginal = el.textContent.trim();
      if (dict[key]) el.textContent = dict[key];
    });
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = []; let n; while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(node => translateNode(node, dict));
    document.querySelectorAll('input[placeholder],textarea[placeholder]').forEach(el => {
      if (!el.dataset.i18nPlaceholder) el.dataset.i18nPlaceholder = el.placeholder;
      const key = el.dataset.i18nPlaceholder.trim();
      if (dict[key]) el.placeholder = dict[key];
    });
  };
  const boot = () => {
    const select = document.getElementById('globalLang');
    if (select && !select.dataset.globalI18nBound) {
      select.dataset.globalI18nBound = '1';
      select.addEventListener('change', () => setTimeout(apply, 0));
    }
    apply();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  setTimeout(boot, 800);
  setTimeout(boot, 2000);
})();
