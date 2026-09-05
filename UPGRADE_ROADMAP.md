# BIS SmartGuide v5 Upgrade

## Added
- BIS Standards Intelligence Agent v2 with intent routing for standards, compliance, mandatory/QCO signals, certification and laboratories.
- Smart compliance assessment with Pass/Fail/Not checked states, score, gaps and recommended actions.
- Conservative mandatory-certification checker linked to official BIS compulsory-certification information.
- Product document analyzer for TXT, MD and JSON files.
- Printable compliance assessment report from the browser.
- Browser voice input using Web Speech API where supported.
- Official BIS source directory including Standards Portal, Know Your Standard, licence guidance, recognized laboratories, LIMS and compulsory-certification/QCO information.
- Expanded API metadata and health reporting.

## Deliberate prototype limitations
- The local catalogue remains a small prototype knowledge base; demo records are explicitly not official BIS certification checklists.
- Mandatory/voluntary status is never asserted unless the local record contains a scheme signal; otherwise the result is NEEDS OFFICIAL VERIFICATION.
- Current laboratory availability is delegated to official BIS directory/LIMS rather than invented locally.
- Document upload currently accepts TXT/MD/JSON to keep the backend dependency-free. PDF/OCR extraction can be added as a separate module.
- Voice input is browser-side and sends the recognized text to the agent.
- Image recognition, live BIS crawling, automatic QCO synchronization and a generative LLM are not enabled by this commit; they should be added only with verified data sources/API credentials and explicit source-grounding controls.

## Official BIS grounding
BIS's Know Your Standard service supports searching by IS number or keyword and provides related standards, amendments, notifications, licences and laboratories. The project therefore treats official BIS links as the authority for current regulatory decisions.
