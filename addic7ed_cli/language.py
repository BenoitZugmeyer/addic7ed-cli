# -*- coding: utf-8 -*-

iso639_3_codes = {
    'Albanian': 'sqi',
    'Arabic': 'ara',
    'Armenian': 'hye',
    'Azerbaijani': 'aze',
    'Bengali': 'ben',
    'Bosnian': 'bos',
    'Bulgarian': 'bul',
    'Català': 'cat',
    'Chinese (Simplified)': 'zho',
    'Chinese (Traditional)': 'zho',
    'Croatian': 'hrv',
    'Czech': 'ces',
    'Danish': 'dan',
    'Dutch': 'nld',
    'English': 'eng',
    'Estonian': 'est',
    'Euskera': 'eus',
    'Finnish': 'fin',
    'French (Canadian)': 'fre',
    'French': 'fre',
    'Galego': 'glg',
    'German': 'deu',
    'Greek': 'ell',
    'Hebrew': 'heb',
    'Hindi': 'hin',
    'Hungarian': 'hun',
    'Icelandic': 'isl',
    'Indonesian': 'ind',
    'Italian': 'ita',
    'Japanese': 'jpn',
    'Korean': 'kor',
    'Latvian': 'lav',
    'Lithuanian': 'lit',
    'Macedonian': 'mkd',
    'Malay': 'mal',
    'Norwegian': 'nor',
    'Persian': 'fas',
    'Polish': 'pol',
    'Portuguese (Brazilian)': 'por',
    'Portuguese': 'por',
    'Romanian': 'ron',
    'Russian': 'rus',
    'Serbian (Cyrillic)': 'srp',
    'Serbian (Latin)': 'srp',
    'Sinhala': 'sin',
    'Slovak': 'slk',
    'Slovenian': 'slv',
    'Spanish (Latin America)': 'spa',
    'Spanish (Spain)': 'spa',
    'Spanish': 'spa',
    'Swedish': 'swe',
    'Tamil': 'tam',
    'Thai': 'tha',
    'Turkish': 'tur',
    'Ukrainian': 'ukr',
    'Vietnamese': 'vie',
}

if __name__ == '__main__':
    from addic7ed_cli.request import session

    page = session.get('/serie/Dexter/8/1/A_Beautiful_Day')

    languages = [option.text
                 for option in page('#filterlang option')
                 if option.text != "All"]

    for language in languages:
        if language not in iso639_3_codes:
            print("Unknown language: {}".format(language))
    print("Check http://www-01.sil.org/iso639-3/codes.asp for a complete list "
          "of ISO 639 codes")
