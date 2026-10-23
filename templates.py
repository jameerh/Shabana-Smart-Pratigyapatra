# templates.py
TEMPLATES = {
    "Waras (Heirship) Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_taluka", "applicant_district",
            "deceased_relation", "deceased_name",
            "deceased_death_date", "deceased_death_place",
            "city_survey_number", "affidavit_place", "affidavit_date",
            "gender"
        ],
        "heirs": True,
        "template": """प्रतिज्ञापत्र

मी {applicant_full_name}, वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. {applicant_taluka}, ता. {applicant_taluka}, जि. {applicant_district},

मी सत्यप्रतिज्ञेवर {gender_verb} की,
माझे {deceased_relation} {deceased_name} यांचा मृत्यू दिनांक {deceased_death_date}
रोजी {deceased_death_place} येथे झाला.

त्यांचे खालीलप्रमाणे वारस आहेत:

{heir_table}

वरीलप्रमाणे आम्ही {number_of_heirs} कायदेशीर वारस असून
आमच्याशिवाय अन्य कोणीही वारस नाही.

तरी {city_survey_number} या मालमत्तेस वारसनोंद करण्यासाठी
सदर प्रतिज्ञापत्र देत आहे.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({applicant_full_name})
"""
    },

    "Name Change Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_address", "old_name", "new_name",
            "reason", "affidavit_place", "affidavit_date", "gender"
        ],
        "heirs": False,
        "template": """प्रतिज्ञापत्र

मी {applicant_full_name}, वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. {applicant_address},

मी सत्यप्रतिज्ञेवर {gender_verb} की,
माझे मूळ नाव {old_name} असून ते बदलून {new_name} असे करण्याची
माझी इच्छा आहे. नाव बदलण्याचे कारण {reason} आहे.

मी या नावाने ओळखला/ओळखली जात असून माझ्या सर्व कागदपत्रांमध्ये
हे नाव बदलण्याची आवश्यकता आहे.

माझे वरील विधान सत्य व बरोबर आहे.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({applicant_full_name})
"""
    },

    "Lost Document Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_address", "document_type", "document_details",
            "lost_date", "lost_place", "complaint_filed", "affidavit_place",
            "affidavit_date", "gender"
        ],
        "heirs": False,
        "template": """प्रतिज्ञापत्र

मी {applicant_full_name}, वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. {applicant_address},

मी सत्यप्रतिज्ञेवर {gender_verb} की,
माझे {document_type} {document_details} हे दिनांक {lost_date}
रोजी {lost_place} येथे हरवले आहे. याबाबत पोलिसात तक्रार
{complaint_filed} आहे.

सदर कागदपत्र सापडले नसल्याने त्याच्या दुहेरीसाठी हे
प्रतिज्ञापत्र देत आहे.

माझे वरील विधान सत्य व बरोबर आहे.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({applicant_full_name})
"""
    },

    "Date of Birth Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_address", "dob", "dob_place", "reason", "affidavit_place",
            "affidavit_date", "gender"
        ],
        "heirs": False,
        "template": """प्रतिज्ञापत्र

मी {applicant_full_name}, वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. {applicant_address},

मी सत्यप्रतिज्ञेवर {gender_verb} की,
माझी जन्मतारीख {dob} असून जन्मस्थळ {dob_place} आहे.
{reason} या कारणास्तव ही जन्मतारीख नोंदविणे आवश्यक आहे.

माझे वरील विधान सत्य व बरोबर आहे.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({applicant_full_name})
"""
    },

    "Income Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "taluka_name", "district", "village",
            "financial_year", "income_amount", "income_in_words",
            "reason_for_document", "validity_of_document",
            "date_of_application", "talathi_report_date",
            "affidavit_place", "affidavit_date", "gender"
        ],
        "heirs": False,
        "template": """प्रतिज्ञापत्र

मी {applicant_full_name}, वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. गाव {village}, ता. {taluka_name}, जि. {district}

मी सत्यप्रतिज्ञेवर {gender_verb} की,
माझे व माझ्या कुटुंबातील सर्व सदस्यांचे सर्व मार्गाने व साधनाने मिळालेले
१ वर्षांचे उत्पन्न खालीलप्रमाणे आहे:

वर्षवार्षिक उत्पन्न: रु. {income_amount} ({income_in_words})

ही माहिती मी {date_of_application} रोजी केलेल्या अर्जासोबत
{talathi_report_date} रोजीच्या तलाठी अहवालाच्या आधारे सादर करत आहे.

सदरचे प्रतिज्ञापत्र मला {reason_for_document} या कामासाठी आवश्यक आहे.
हे प्रतिज्ञापत्र {validity_of_document} पर्यंत वैध राहील.

माझे वरील विधान सत्य व बरोबर आहे. ते खोटे ठरल्यास मी
भारतीय दंडसंहितेच्या कलम १९३, १९९ व २०० अन्वये दंडास पात्र राहीन.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({applicant_full_name})
"""
    },

    "Address Proof Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "old_address", "new_address", "duration_at_new", "reason",
            "affidavit_place", "affidavit_date", "gender"
        ],
        "heirs": False,
        "template": """प्रतिज्ञापत्र

मी {applicant_full_name}, वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},

मी सत्यप्रतिज्ञेवर {gender_verb} की,
माझा सध्याचा पत्ता {new_address} असून मी येथे {duration_at_new}
पासून राहत आहे. यापूर्वीचा पत्ता {old_address} होता.
पत्ता बदलण्याचे कारण {reason} आहे.

माझे वरील विधान सत्य व बरोबर आहे.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({applicant_full_name})
"""
    },

    "Landless Agricultural Labour Certificate": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "village", "taluka_name", "district", "pincode",
            "application_reference_number",
            "application_date", "affidavit_date",
            "talathi_report_date", "aadhar_number",
            "affidavit_place", "gender"
        ],
        "heirs": False,
        "barcode_field": "application_reference_number",
        "template": """प्रतिज्ञापत्र

मी {applicant_full_name}, वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. गाव {village}, ता. {taluka_name}, जि. {district}, पिनकोड {pincode},

मी सत्यप्रतिज्ञेवर {gender_verb} की,
माझ्या नावे गावात कोणतीही जमीन नसून मी भूमिहीन आहे.
माझा मुख्य व्यवसाय शेतावर मजुरीचे काम करणे हा आहे.

सदर प्रतिज्ञापत्र मी {application_reference_number} या संदर्भ क्रमांकाने
दिनांक {application_date} रोजी केलेल्या अर्जाच्या आधारे देत आहे.
तलाठी यांचा अहवाल दिनांक {talathi_report_date} रोजी सादर केला आहे.
माझा आधार क्रमांक {aadhar_number} आहे.

हे प्रतिज्ञापत्र फक्त गावाच्या हद्दीपर्यंत वैध राहील.

माझे वरील विधान सत्य व बरोबर आहे. ते खोटे ठरल्यास मी
भारतीय दंडसंहितेच्या कलम १९३, १९९ व २०० अन्वये दंडास पात्र राहीन.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({applicant_full_name})
"""
    },

    "Gap Certificate": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_address", "institution_name", "qualification",
            "year_of_completion", "gap_start_year", "gap_end_year",
            "reason", "affidavit_place", "affidavit_date", "gender"
        ],
        "heirs": False,
        "template": """प्रतिज्ञापत्र

मी {applicant_full_name}, वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. {applicant_address},

मी सत्यप्रतिज्ञेवर {gender_verb} की,
मला गॅप सर्टिफिकेट मिळण्यासाठी केलेले हे प्रतिज्ञापत्र आहे.

मी {institution_name} येथे {qualification} परीक्षा {year_of_completion} या वर्षी उत्तीर्ण झालो/झाले.
तरी {gap_start_year} ते {gap_end_year} या कालावधीत मी कोणत्याही शाळा/महाविद्यालयात प्रवेश घेतलेला नाही,
तसेच कोणत्याही शासकीय किंवा निमशासकीय सेवेत नोकरी केलेली नाही.

हे कालखंड गॅप म्हणून नोंदविण्यासाठी सदर प्रतिज्ञापत्र देत आहे.

माझे वरील विधान सत्य व बरोबर आहे. ते खोटे ठरल्यास मी
भारतीय दंडसंहितेच्या कलम १९३, १९९ व २०० अन्वये दंडास पात्र राहीन.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({applicant_full_name})
"""
    },

    "Income Certificate (3 Years)": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_address",
            "year1", "year2", "year3",
            "income1_salary", "income1_agri", "income1_labour", "income1_other",
            "income2_salary", "income2_agri", "income2_labour", "income2_other",
            "income3_salary", "income3_agri", "income3_labour", "income3_other",
            "affidavit_place", "affidavit_date", "gender"
        ],
        "heirs": False,
        "template": """प्रतिज्ञापत्र

मी {applicant_full_name}, वय {applicant_age} वर्षे, व्यवसाय {applicant_occupation},
रा. {applicant_address},

मी सत्यप्रतिज्ञेवर {gender_verb} की,
मला माझ्या नोकरीसाठी उत्पन्नाचा दाखला मिळण्यासाठी हे प्रतिज्ञापत्र देत आहे.

माझे व माझ्या कुटुंबाचे मागील तीन वर्षांचे एकूण उत्पन्न खालीलप्रमाणे आहे:

| तपशील           | {year1} | {year2} | {year3} |
|------------------|--------|--------|--------|
| नोकरी/पेन्शन     | {income1_salary} | {income2_salary} | {income3_salary} |
| शेती             | {income1_agri} | {income2_agri} | {income3_agri} |
| मजुरी            | {income1_labour} | {income2_labour} | {income3_labour} |
| इतर              | {income1_other} | {income2_other} | {income3_other} |
| **एकूण**         | **{total1}** | **{total2}** | **{total3}** |

माझ्या कुटुंबाच्या नावे इतर कोणतेही बँक खाते / शिल्लक नाही.
मला कोणत्याही प्रकारचा दंड शिक्षा झालेली नाही.
रेशन कार्ड, जातीचा दाखला, तहसीलदार यांचा तीन वर्षांचा उत्पन्नाचा दाखला सादर केला आहे.

माझे वरील विधान सत्य व बरोबर आहे. ते खोटे ठरल्यास मी
भारतीय दंडसंहितेच्या कलम १९३, १९९ व २०० अन्वये दंडास पात्र राहीन.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({applicant_full_name})
"""
    },
        "Hiba (Gift) Deed": {
        "fields": [
            "donor_name", "donor_age", "donor_occupation", "donor_address",
            "donee_name", "donee_age", "donee_occupation", "donee_address",
            "property_description", "survey_number", "area", "boundaries",
            "date_of_gift", "witness1_name", "witness1_address",
            "witness2_name", "witness2_address",
            "affidavit_place", "affidavit_date", "gender"
        ],
        "heirs": False,
        "template": """प्रतिज्ञापत्र

मी {donor_name}, वय {donor_age} वर्षे, व्यवसाय {donor_occupation},
रा. {donor_address},

मी सत्यप्रतिज्ञेवर {gender_verb} की,
मी दिनांक {date_of_gift} रोजी माझ्या स्वेच्छेने, बिना कोणत्याही बंधनात,
माझी खालील वर्णन केलेली मालमत्ता {donee_name}, वय {donee_age},
व्यवसाय {donee_occupation}, रा. {donee_address} यांना
मुस्लिम धर्मशास्त्र (इस्लाम) व मुस्लिम परस्परल कायद्यातील तरतुदीनुसार
हिबा (गिफ्ट) केली आहे.

मालमत्तेचे वर्णन:
{property_description}
सर्वे क्रमांक: {survey_number}
क्षेत्र: {area}
हद्दी: {boundaries}

ही हिबा मी विधिवत मुस्लिम धर्मशास्त्राच्या रीतीरिवाजानुसार
{date_of_gift} रोजी खालील साक्षीदारांच्या उपस्थितीत केली
आणि त्यांना ताबा दिला. सदर मालमत्तेवर माझे किंवा माझ्या कोणत्याही
वारसाचे कोणतेही हक्क राहणार नाहीत.

साक्षीदार:
1. {witness1_name}, रा. {witness1_address}
2. {witness2_name}, रा. {witness2_address}

सदर हिबा करण्यापूर्वी मी माझ्या मनापासून विचार करून
माझ्या इच्छेने ही देणगी दिली आहे. मी या मालमत्तेचा
पूर्ण मालक आहे आणि माझ्या नावे इतर कोणतेही बंधन नाही.
ही देणगी परत घेण्याचा मला अधिकार नाही.

माझे वरील विधान सत्य व बरोबर आहे. ते खोटे ठरल्यास मी
भारतीय दंडसंहितेच्या कलम १९३, १९९ व २०० अन्वये दंडास पात्र राहीन.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({donor_name})
"""
    },
                "Alpa Bhumidhar Shetkari (Small Farmer) Affidavit": {
        "fields": [
            "applicant_name", "age", "occupation",
            "village_name", "taluka_name", "district_name",
            "gut_number", "khata_number", "land_area",
            "affidavit_place", "affidavit_date", "gender"
        ],
        "heirs": False,
        "template": """प्रतिज्ञापत्र

मा कार्यकारी दंडाधिकारी सो {village_name} ता {taluka_name} जि {district_name} यांच्यासमोर

संमतीपत्र लिहून देतो मी {gender_prefix} {applicant_name}, वय {age} वर्षे, व्यवसाय {occupation},
रा. {village_name}, ता {taluka_name}, जि {district_name}.

मी सत्यप्रतिज्ञेवर {gender_verb} की,
मी वरील पत्त्यावरचा कायमचा रहिवाशी असून मी अल्पभूधारक शेतकरी आहे.
माझ्या नावे मौजे {village_name}, ता {taluka_name}, जि {district_name} येथे
गट नं. {gut_number}, खाते क्र. {khata_number} ची जमीन असून
एकूण जमीन क्षेत्र {land_area} आहे.
सदर जमिनी व्यतिरिक्त माझ्या नावे अथवा माझ्या कुटुंबातील कोणत्याही व्यक्तीच्या नावे
महाराष्ट्रात अथवा महाराष्ट्राबाहेर कोठेही जमीन वगैरे नाही.
तरी मी अल्पभूधारक शेतकरी आहे म्हणून हे प्रतिज्ञापत्र देत आहे.

वरील सर्व माहिती माझ्या माहिती व समजुतीनुसार खरी आहे.
सदर माहिती खोटी आढळून आल्यास भारतीय दंड संहिता 1961 कलम 199 व 200 अन्वये
संबंधित कायद्यानुसार माझ्यावर खटला भरला जाईल व त्यानुसार मी शिक्षेस पात्र राहीन.
याची मला जाणीव आहे.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

स्वाक्षरी
({applicant_name})
"""
    },
        "Marriage Affidavit": {
        "fields": [
            "applicant_name", "age", "occupation", "village_name", "district_name",
            "marriage_date", "marriage_place", "spouse_father_name",
            "spouse_name_before_marriage", "spouse_name_after_marriage",
            "affidavit_date", "magistrate_name", "magistrate_place", "magistrate_date",
            "gender"
        ],
        "heirs": False,
        "template": """प्रतिज्ञापत्र

मा कार्यकारी दंडाधिकारी सो जत ता जत जि {district_name} यांचेसमोर

प्रतिज्ञापत्र लिहून देतो मी {gender_prefix} {applicant_name}, वय {age} वर्षे, व्यवसाय {occupation}, रा {village_name} ता जत जि {district_name}.

मी सत्यप्रतिज्ञेवर {gender_verb} की,
मी वरील पत्त्यावरचा कायमचा रहिवाशी असून माझा विवाह दि {marriage_date} रोजी {marriage_place} ता जत जि {district_name} येथे {spouse_father_name} यांची मुलगी {spouse_name_before_marriage} यांच्याशी विवाह झाला आहे.

सदर विवाहाची नोंद {village_name} ग्रामपंचायत {village_name} ता.जत जि.{district_name} येथे विवाहनोंद रजिस्टर मध्ये झालेली नाही तरी माझ्या विवाहाची नोंद होणे कामी केलेले प्रतिज्ञापत्र.

तसेच विवाहपूर्वीचे नाव {spouse_name_before_marriage} व विवाहानंतरचे नाव {spouse_name_after_marriage} असे आहे. या दोन्ही नावांची व्यक्ती एकच आहे अन्य कोणीही नाहीत हे खरे व बरोबर आहे.

वरील सर्व माहिती माझ्या माहिती व समजुतीनुसार खरी आहे. सदर माहिती खोटी आढळून आल्यास भारतीय दंड संहिता 1961 कलम 199 व 200 अन्वये संबंधित कायद्यानुसार माझ्यावर खटला भरला जाईल व त्यानुसार मी शिक्षेस पात्र राहीन याची मला जाणीव आहे.

दिनांक: {affidavit_date}

{applicant_name}
{spouse_name_after_marriage}

NO/MAG/AFR/JATH/

Solemnly affirmed before me by
Shri/Smt – {magistrate_name}

रा {magistrate_place} तुर्क ता. जत जि {district_name}

And he/she has signed in my presence

Taluka Executive Magistrate Jath
Date {magistrate_date}
"""
    }
}