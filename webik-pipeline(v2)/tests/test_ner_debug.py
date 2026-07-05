"""Debug: что выдаёт spaCy на каждый токен в entity."""
import spacy

nlp = spacy.load("ru_core_news_lg")
text = "В Северной Кореи и в Москве, из СССР в США"
doc = nlp(text)
for ent in doc.ents:
    print(f"ent='{ent.text}' label={ent.label_}")
    for tok in ent:
        print(f"  tok='{tok.text}' lemma='{tok.lemma_}' pos={tok.pos_}")
