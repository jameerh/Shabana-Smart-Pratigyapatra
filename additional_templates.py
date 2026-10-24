"""Generic reusable affidavit templates based on the supplied four sample declarations.

The supplied source contains legacy-font/encoding corruption. These templates use
readable Marathi wording for the clear intended meaning; operators should verify
the legal wording and local office requirements before submission.
"""
GENERIC_FOOD_AFFIDAVIT_TEMPLATES = {
    "Anna Suraksha Eligibility Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_village", "applicant_taluka", "applicant_district",
            "income_year_range", "annual_income", "affidavit_place",
            "affidavit_date", "gender",
        ],
        "heirs": False,
        "template": """सत्य प्रतिज्ञापत्र

मा. कार्यकारी दंडाधिकारी, जत, ता. जत, जि. सांगली यांच्या समोर

प्रतिज्ञापत्र लिहून देणारा/देणारी मी {gender_prefix} {applicant_full_name},
वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. {applicant_village}, ता. {applicant_taluka}, जि. {applicant_district}.

मी सत्यप्रतिज्ञेवर {gender_verb} की,

मी वरील पत्त्यावरचा/ची कायमचा/ची रहिवासी असून माझे {income_year_range} या वर्षाचे मजुरीपासूनचे एकूण वार्षिक उत्पन्न {annual_income}/- रुपये आहे. मी अन्न सुरक्षा योजनेअंतर्गत लाभार्थी होण्यास पात्र आहे. सदर यादीमध्ये माझे नाव नमूद झालेले नसल्याने अन्न सुरक्षा लाभार्थी यादीमध्ये माझे नाव समाविष्ट होण्यासाठी हे प्रतिज्ञापत्र देत आहे.

वरील सर्व माहिती माझ्या माहिती व समजुतीनुसार खरी आहे. सदर माहिती खोटी आढळल्यास लागू कायद्यानुसार होणाऱ्या कारवाईस मी जबाबदार राहीन, याची मला जाणीव आहे.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

प्रतिज्ञाकर्त्याची सही / अंगठा
{applicant_full_name}
"""
    },
    "No Kerosene License or Fuel Pump Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_village", "applicant_taluka", "applicant_district",
            "affidavit_place", "affidavit_date", "gender",
        ],
        "heirs": False,
        "template": """सत्य प्रतिज्ञापत्र

मा. कार्यकारी दंडाधिकारी, जत, ता. जत, जि. सांगली यांच्या समोर

प्रतिज्ञापत्र लिहून देणारा/देणारी मी {gender_prefix} {applicant_full_name},
वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. {applicant_village}, ता. {applicant_taluka}, जि. {applicant_district}.

मी सत्यप्रतिज्ञेवर {gender_verb} की,

मी वरील पत्त्यावरचा/ची कायमचा/ची रहिवासी असून माझ्या कुटुंबातील कोणाच्याही नावे घाऊक किंवा किरकोळ नियंत्रित रॉकेल विक्री परवाना अथवा पेट्रोल/डिझेल पंप परवाना नाही. याबाबत हे प्रतिज्ञापत्र देत आहे.

वरील सर्व माहिती माझ्या माहिती व समजुतीनुसार खरी आहे. सदर माहिती खोटी आढळल्यास लागू कायद्यानुसार होणाऱ्या कारवाईस मी जबाबदार राहीन, याची मला जाणीव आहे.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

प्रतिज्ञाकर्त्याची सही / अंगठा
{applicant_full_name}
"""
    },
    "No Essential Commodities Act Action Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_village", "applicant_taluka", "applicant_district",
            "affidavit_place", "affidavit_date", "gender",
        ],
        "heirs": False,
        "template": """सत्य प्रतिज्ञापत्र

मा. कार्यकारी दंडाधिकारी, जत, ता. जत, जि. सांगली यांच्या समोर

प्रतिज्ञापत्र लिहून देणारा/देणारी मी {gender_prefix} {applicant_full_name},
वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. {applicant_village}, ता. {applicant_taluka}, जि. {applicant_district}.

मी सत्यप्रतिज्ञेवर {gender_verb} की,

मी वरील पत्त्यावरचा/ची कायमचा/ची रहिवासी असून माझ्याविरुद्ध अथवा माझे वडील (मयत) यांच्याविरुद्ध जीवनावश्यक वस्तू अधिनियम, १९५५ अंतर्गत कोणतीही कारवाई सुरू किंवा प्रस्तावित नाही आणि यापूर्वीही अशी कारवाई झालेली नाही. याबाबत हे प्रतिज्ञापत्र देत आहे.

वरील सर्व माहिती माझ्या माहिती व समजुतीनुसार खरी आहे. सदर माहिती खोटी आढळल्यास लागू कायद्यानुसार होणाऱ्या कारवाईस मी जबाबदार राहीन, याची मला जाणीव आहे.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

प्रतिज्ञाकर्त्याची सही / अंगठा
{applicant_full_name}
"""
    },
    "No Employment or Private Company Membership Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_village", "applicant_taluka", "applicant_district",
            "affidavit_place", "affidavit_date", "gender",
        ],
        "heirs": False,
        "template": """सत्य प्रतिज्ञापत्र

मा. कार्यकारी दंडाधिकारी, जत, ता. जत, जि. सांगली यांच्या समोर

प्रतिज्ञापत्र लिहून देणारा/देणारी मी {gender_prefix} {applicant_full_name},
वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. {applicant_village}, ता. {applicant_taluka}, जि. {applicant_district}.

मी सत्यप्रतिज्ञेवर {gender_verb} की,

मी वरील पत्त्यावरचा/ची कायमचा/ची रहिवासी असून मी सरकारी, निमसरकारी किंवा खाजगी नोकरीत पूर्णवेळ अथवा अर्धवेळ काम करत नाही. तसेच मी कोणत्याही खाजगी कंपनीचा सभासद नाही. याबाबत हे प्रतिज्ञापत्र देत आहे.

वरील सर्व माहिती माझ्या माहिती व समजुतीनुसार खरी आहे. सदर माहिती खोटी आढळल्यास लागू कायद्यानुसार होणाऱ्या कारवाईस मी जबाबदार राहीन, याची मला जाणीव आहे.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

प्रतिज्ञाकर्त्याची सही / अंगठा
{applicant_full_name}
"""
    },
}
