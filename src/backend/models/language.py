from backend.common.exceptions import InvalidArgumentError


class Language:  # pylint: disable=too-few-public-methods
    SUPPORTED_LANGUAGES = [
        'Amharic',
        'Arabic',
        'Basque',
        'Bengali',
        'Bulgarian',
        'Catalan',
        'Cherokee',
        'Croatian',
        'Czech',
        'Danish',
        'Dutch',
        'English',
        'Estonian',
        'Filipino',
        'Finnish',
        'French',
        'German',
        'Greek',
        'Gujarati',
        'Hebrew',
        'Hindi',
        'Hungarian',
        'Icelandic',
        'Indonesian',
        'Italian',
        'Japanese',
        'Kannada',
        'Korean',
        'Latvian',
        'Lithuanian',
        'Malay',
        'Malayalam',
        'Marathi',
        'Norwegian',
        'Polish',
        'Portuguese',
        'Romanian',
        'Russian',
        'Serbian',
        'Chinese',
        'Slovak',
        'Slovenian',
        'Spanish',
        'Swahili',
        'Swedish',
        'Tamil',
        'Telugu',
        'Thai',
        'Chinese',
        'Turkish',
        'Urdu',
        'Ukrainian',
        'Vietnamese',
        'Welsh'
    ]

    @classmethod
    def is_supported(cls, language):
        return language in cls.SUPPORTED_LANGUAGES

    @classmethod
    def validate_and_convert_language(cls, language):
        if not cls.is_supported(language):
            raise InvalidArgumentError(f"Unsupported language: {language}")
        return language

    @classmethod
    def validate_and_convert_languages(cls, languages):
        for language in languages:
            cls.validate_and_convert_language(language)
        return languages
