from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

#Se carga el modelo y el tokenizador se utiliza nlptown/bert-base-multilingual-uncased-sentiment
# que es un modelo BERT preentrenado para análisis de sentimientos en múltiples idiomas
tokenizer = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
model = AutoModelForSequenceClassification.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")

def analizar_sentimiento(texto):
    #Tokeniza el texto de entrada y lo convierte en tensores
    inputs = tokenizer(texto, return_tensors="pt", truncation=True, padding=True)
    
    #Pasa los tensores a través del modelo para obtener las salidas
    with torch.no_grad():
        outputs = model(**inputs)
    
    #Aplica softmax a las salidas para obtener probabilidades
    probabilities = F.softmax(outputs.logits, dim=-1)
    
    #Obtiene la clase con la probabilidad más alta
    predicted_class = torch.argmax(probabilities, dim=-1).item()
    
    #Mapea la clase predicha a una etiqueta de sentimiento
    if predicted_class in [0, 1]:  # Clases 0 y 1 representan sentimientos negativos
        return 'negativa'
    elif predicted_class == 2:       # Clase 2 representa un sentimiento neutral
        return 'neutral'
    else:                            # Clases 3 y 4 representan sentimientos positivos
        return 'positiva'