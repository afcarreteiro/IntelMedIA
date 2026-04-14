import re
import unicodedata
from dataclasses import dataclass

from app.config import settings


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.lower())
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9\s]", "", ascii_text).strip()


PHRASEBOOK = {
    "where_is_the_pain": {
        "pt-PT": "Onde e a dor?",
        "en-GB": "Where is the pain?",
        "fr-FR": "Ou est la douleur ?",
        "es-ES": "Donde esta el dolor?",
        "de-DE": "Wo ist der Schmerz?",
        "it-IT": "Dove sente dolore?",
        "uk-UA": "De bolyt?",
        "ar": "Ayn al alam?",
        "hi-IN": "Dard kahan hai?",
        "bn-BD": "Byatha kothay?",
        "ur-PK": "Dard kahan hai?",
        "zh-CN": "Tong zai nali?",
    },
    "do_you_have_fever": {
        "pt-PT": "Tem febre?",
        "en-GB": "Do you have a fever?",
        "fr-FR": "Avez-vous de la fievre ?",
        "es-ES": "Tiene fiebre?",
        "de-DE": "Haben Sie Fieber?",
        "it-IT": "Ha febbre?",
        "uk-UA": "U vas ye temperatura?",
        "ar": "Hal ladaik humma?",
        "hi-IN": "Kya aapko bukhar hai?",
        "bn-BD": "Apnar jor ache?",
        "ur-PK": "Kya aap ko bukhar hai?",
        "zh-CN": "Ni fa shao ma?",
    },
    "i_have_chest_pain": {
        "pt-PT": "Tenho dor no peito.",
        "en-GB": "I have chest pain.",
        "fr-FR": "J'ai une douleur thoracique.",
        "es-ES": "Tengo dolor en el pecho.",
        "de-DE": "Ich habe Brustschmerzen.",
        "it-IT": "Ho dolore al petto.",
        "uk-UA": "U mene bil u hrudiah.",
        "ar": "Ladayya alam fi al sadr.",
        "hi-IN": "Mujhe chhati me dard hai.",
        "bn-BD": "Amar bukey byatha hocche.",
        "ur-PK": "Mujhe seene mein dard hai.",
        "zh-CN": "Wo xiong kou teng.",
    },
    "i_am_allergic_to_penicillin": {
        "pt-PT": "Sou alergico a penicilina.",
        "en-GB": "I am allergic to penicillin.",
        "fr-FR": "Je suis allergique a la penicilline.",
        "es-ES": "Soy alergico a la penicilina.",
        "de-DE": "Ich bin allergisch gegen Penicillin.",
        "it-IT": "Sono allergico alla penicillina.",
        "uk-UA": "U mene alergiia na penitsylin.",
        "ar": "Ana ladayya hasasiyya min al banisilin.",
        "hi-IN": "Mujhe penicillin se allergy hai.",
        "bn-BD": "Amar penicillin e allergy ache.",
        "ur-PK": "Mujhe penicillin se allergy hai.",
        "zh-CN": "Wo dui qing mei su guo min.",
    },
    "i_have_had_fever_since_yesterday": {
        "pt-PT": "Tenho febre desde ontem.",
        "en-GB": "I have had a fever since yesterday.",
        "fr-FR": "J'ai de la fievre depuis hier.",
        "es-ES": "Tengo fiebre desde ayer.",
        "de-DE": "Ich habe seit gestern Fieber.",
        "it-IT": "Ho febbre da ieri.",
        "uk-UA": "U mene temperatura vid vchora.",
        "ar": "Indi humma mundhu ams.",
        "hi-IN": "Mujhe kal se bukhar hai.",
        "bn-BD": "Amar kal theke jor ache.",
        "ur-PK": "Mujhe kal se bukhar hai.",
        "zh-CN": "Wo cong zuotian kaishi fa shao.",
    },
    "i_take_metformin": {
        "pt-PT": "Tomo metformina.",
        "en-GB": "I take metformin.",
        "fr-FR": "Je prends de la metformine.",
        "es-ES": "Tomo metformina.",
        "de-DE": "Ich nehme Metformin.",
        "it-IT": "Prendo metformina.",
        "uk-UA": "Ia pryimaiu metformin.",
        "ar": "Atanawal al metformin.",
        "hi-IN": "Main metformin leta hun.",
        "bn-BD": "Ami metformin khai.",
        "ur-PK": "Main metformin leta hun.",
        "zh-CN": "Wo chi er jia shuang gua.",
    },
    "i_feel_dizzy": {
        "pt-PT": "Sinto tonturas.",
        "en-GB": "I feel dizzy.",
        "fr-FR": "Je me sens etourdi.",
        "es-ES": "Me siento mareado.",
        "de-DE": "Mir ist schwindelig.",
        "it-IT": "Mi sento stordito.",
        "uk-UA": "U mene zapamorochenia.",
        "ar": "Ashur bil daukha.",
        "hi-IN": "Mujhe chakkar aa rahe hain.",
        "bn-BD": "Amar matha ghurchhe.",
        "ur-PK": "Mujhe chakkar aa rahe hain.",
        "zh-CN": "Wo tou yun.",
    },
    "i_will_check_your_blood_pressure": {
        "pt-PT": "Vou medir a sua tensao arterial.",
        "en-GB": "I will check your blood pressure.",
        "fr-FR": "Je vais verifier votre tension arterielle.",
        "es-ES": "Voy a medir su tension arterial.",
        "de-DE": "Ich werde Ihren Blutdruck messen.",
        "it-IT": "Misurero la sua pressione arteriosa.",
        "uk-UA": "Ia vymiriayu vash arterialnyi tysk.",
        "ar": "Sa aqis daght al dam ladayk.",
        "hi-IN": "Main aapka blood pressure check karunga.",
        "bn-BD": "Ami apnar roktochap mapbo.",
        "ur-PK": "Main aap ka blood pressure check karunga.",
        "zh-CN": "Wo yao gei ni liang xue ya.",
    },
    "how_long_has_this_been_happening": {
        "pt-PT": "Ha quanto tempo isto acontece?",
        "en-GB": "How long has this been happening?",
        "fr-FR": "Depuis combien de temps cela dure ?",
        "es-ES": "Cuanto tiempo lleva ocurriendo esto?",
        "de-DE": "Wie lange passiert das schon?",
        "it-IT": "Da quanto tempo succede?",
        "uk-UA": "Skilky chasu tse tryvaie?",
        "ar": "Mundhu mata hadha yahduth?",
        "hi-IN": "Yeh kab se ho raha hai?",
        "bn-BD": "Eta kotodin dhore hocche?",
        "ur-PK": "Yeh kab se ho raha hai?",
        "zh-CN": "Zhe yang you duo jiu le?",
    },
}

NORMALIZED_PHRASE_INDEX = {
    (language_code, _normalize_text(phrase)): phrase_key
    for phrase_key, translations in PHRASEBOOK.items()
    for language_code, phrase in translations.items()
}


@dataclass
class TranslationResult:
    translated_text: str
    engine: str
    uncertainty_reasons: list[str]

    @property
    def is_uncertain(self) -> bool:
        return bool(self.uncertainty_reasons)


class TranslationService:
    def translate(self, source_text: str, source_language: str, target_language: str) -> TranslationResult:
        if source_language == target_language:
            return TranslationResult(
                translated_text=source_text,
                engine="identity",
                uncertainty_reasons=[],
            )

        phrase_key = NORMALIZED_PHRASE_INDEX.get((source_language, _normalize_text(source_text)))
        if phrase_key and target_language in PHRASEBOOK[phrase_key]:
            return TranslationResult(
                translated_text=PHRASEBOOK[phrase_key][target_language],
                engine=f"{settings.translation_provider}_phrasebook",
                uncertainty_reasons=[],
            )

        return TranslationResult(
            translated_text=source_text,
            engine=f"{settings.translation_provider}_fallback",
            uncertainty_reasons=[
                "Local fallback mode could not confidently translate this free-form utterance.",
                "Clinician review is required before relying on this output.",
            ],
        )
