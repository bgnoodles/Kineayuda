from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# Cargamos un modelo público de sentimiento en español
MODEL_NAME = "finiteautomata/beto-sentiment-analysis"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

LABELS_MAP = {
    "NEG": "negativa",
    "NEU": "neutral",
    "POS": "positiva",
}

def analizar_sentimiento(texto: str) -> str:
    """
    Analiza el sentimiento de un texto en español y retorna:
    'positiva', 'neutral' o 'negativa'.
    """
    # Tokenizar
    inputs = tokenizer(
        texto,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256,
    )

    # Pasar por el modelo sin gradientes
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits

    # Softmax para probabilidades
    probs = F.softmax(logits, dim=-1)

    # Índice de la clase más probable
    pred_idx = probs.argmax(dim=-1).item()

    # Convertimos índice -> etiqueta del modelo -> etiqueta nuestra
    raw_label = model.config.id2label[pred_idx]  # 'NEG', 'NEU', 'POS'
    return LABELS_MAP.get(raw_label, "neutral")
