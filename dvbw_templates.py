"""DVBW legacy-font affidavit template based on the user-supplied sample.

The body intentionally retains the supplied legacy-encoded text. Placeholder values
are substituted as text; users should verify the exported document in Word with the
same DVBW font installed. Legal wording is not independently certified.
"""
DVBW_AFFIDAVIT_TEMPLATES = {
    "DVBW DDF Electricity Connection Affidavit": {
        "fields": [
            "applicant_full_name", "applicant_age", "applicant_occupation",
            "applicant_village", "property_number", "connection_percentage",
            "electricity_office", "affidavit_place", "affidavit_date",
        ],
        "heirs": False,
        "preview_font_hint": "DVBW",
        "required_fields": ["applicant_full_name", "applicant_age", "applicant_occupation", "applicant_village", "property_number", "connection_percentage", "electricity_office", "affidavit_place", "affidavit_date"],
        "template": """¯ÖÏ×ŸÖ–ÖÖ¯Ö¡Ö
´ÖÖ ÛúÖµÖÔÛúÖ¸üß ¤Óü›üÖ×¬ÖÛúÖ¸üßÃÖÖê •ÖŸÖ ŸÖÖ •ÖŸÖ ×•Ö ÃÖÖÓÝÖ»Öß µÖÖÓ“µÖÖ ÃÖ´ÖÖê¸ü
¯ÖÏ×ŸÖ–ÖÖ¯Ö¡Ö ×»ÖÆæü®Ö ¤êüÞÖÖ¸ü ´Öß {applicant_full_name} ¾ÖµÖ ¾ÖÂÖì {applicant_age} ¾µÖ¾ÖÃÖÖµÖ {applicant_occupation} ¸üÖ {applicant_village} ŸÖÖ •ÖŸÖ ×•Ö ÃÖÖÓÝÖ»Öß.

†Ö´Æüß Ûú£Ö®Ö Ûú¸üŸÖÖê Ûúß,
       ´Öß ¾Ö¸üß»Ö ¯ÖŸµÖÖ¾Ö¸ü“ÖÖ ÛúÖµÖ´Ö“ÖÖ ¸ü×Æü¾ÖÖ¿Öß †ÃÖæ®Ö ´ÖÖ—Öê ®ÖÖÓ¾Öê {applicant_village} ŸÖÖ •ÖŸÖ µÖê£Öê ÝÖ™ü ÛÎú.{property_number}, ´Ö¬µÖê  ¾µÖ¾ÖÃÖÖ×µÖÛú &#20; &#BE;ÖÖ¯Ö¸üÖÃÖÖšüß {connection_percentage} DDF ×¾Ö•Ö Ûú®ÖêŒ¿Ö®Ö ×´ÖôûÞÖêÃÖ ´ÖÖ ˆ¯Ö†×³ÖµÖÓŸÖÖ {electricity_office} ŸÖÖ •ÖŸÖ ×•Ö ÃÖÖÓÝÖ»Öß µÖÖÓ“µÖÖÛú›êü †•ÖÔ Ûêú»Öê»ÖÖ †ÖÆêü. ŸÖ¸üß ÃÖ¤ü¸ü Ûú®ÖêŒ¿Ö®ÖÃÖÖšüß »ÖÖÝÖÞÖÖ¸êü ¸üÖê×Æü¡Ö ˆ³ÖÖ¸üÞÖß ´Öß ´ÖÖ—µÖÖ Ã¾ÖÜÖ“ÖÖÔ®Öê Ûú¹ý®Ö ‘ÖêÞµÖÖÃÖ ŸÖµÖÖ¸ü †ÖÆêü ŸÖ¸üß ŸµÖÖÃÖ ´ÖÖ—Öê ³ÖÖ‰ú²ÖÓ¤ü ØÛú¾ÖÖ ‡ŸÖ¸ü ÛúÖêÞÖÖ“ÖßÆüß ŸÖÛÎúÖ¸ü †ÝÖ¸ü Æü¸üÛúŸÖ †Ö»ÖêÃÖ ŸÖß ´ÖÖ—Öê •Ö²ÖÖ²Ö¤üÖ¸üß¾Ö¸ü ×®Ö¾ÖÖ¸ü®Ö Ûú¸üß®Ö. ŸµÖÖ“Öß ŸÖÖê×ÂÖÃÖ ×´Ö ´Ö.¸üÖ.×¾Ö. ´ÖÆüÖ´ÖÓ›üôûÖÃÖ »ÖÖÝÖæ ¤êüÞÖÖ¸ü ®ÖÖÆüß.

 Í  ¾Ö¸üß»Ö ÃÖ¾ÖÔ ´ÖÖ×ÆüŸÖß ´ÖÖ—µÖÖ ´ÖÖ×ÆüŸÖß ¾Ö ÃÖ´Ö•ÖãŸÖß ®ÖãÃÖÖ¸ü ÜÖ¸üß †ÖÆêü. ÃÖ¤ü¸ü ´ÖÖ×ÆüŸÖß ÜÖÖê™üß †Öœüôæû®Ö †Ö»µÖÖÃÖ ³ÖÖ¸üŸÖßµÖ ¤Óü›ü ÃÖÓ×ÆüŸÖÖ 1961 Ûú»Ö´Ö 199 ¾Ö 200 †®¾ÖµÖê ÃÖÓ²ÖÓ×¬ÖŸÖ ÛúÖµÖªÖ®ÖãÃÖÖ¸ü ´ÖÖ—µÖÖ¾Ö¸ü ÜÖ™ü»ÖÖ ³Ö¸ü»ÖÖ •ÖÖ‡Ô»Ö ¾Ö ŸµÖÖ®ÖãÃÖÖ¸ü ´Öß ×¿ÖõÖêÃÖ ¯ÖÖ¡Ö ¸üÖÆüß®Ö µÖÖ“Öß ´Ö»ÖÖ •ÖÖ×ÞÖ¾Ö †ÖÆêü.

ठिकाण: {affidavit_place}
दिनांक: {affidavit_date}

{applicant_full_name}
"""
    }
}
