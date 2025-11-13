import ollama
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from sklearn.preprocessing import normalize

# 1. Расширенная база знаний
knowledge_base = {
    "Как играть аккорд C?": "Аккорд C: x32010. Бой: D DU UDU. Песни: 'Кино - Пачка сигарет'.",
    "Как играть аккорд C на гитаре?": "Аккорд C: x32010. Бой: D DU UDU. Песни: 'Кино - Пачка сигарет'.",
    "Аккорд C": "Аккорд C: зажмите 2 струну на 1 ладу, 4 струну на 2 ладу, 5 струну на 3 ладу. x32010.",
    "Как взять аккорд C?": "Аккорд C: x32010. Первый палец - 2 струна 1 лад, второй - 4 струна 2 лад, третий - 5 струна 3 лад.",

    "Как играть бой шестёрку?": "Бой 'шестёрка': D DU UDU. Акцент на 2 и 4 доли. Подходит для многих песен.",
    "Что такое бой шестёрка?": "Бой 'шестёрка': вниз-вниз-вверх-вниз-вверх (D DU UDU). Основной ритмический рисунок.",
    "Бой шестерка": "Шестёрка: D-DU-UDU. Играйте равномерно, акцентируя 2 и 4 доли.",

    "Как играть аккорд Am?": "Аккорд Am: x02210. Простой минорный аккорд, часто используется с C и G.",
    "Аккорд Am": "Am: x02210. Первый палец - 2 струна 1 лад, второй - 3 струна 2 лад, третий - 4 струна 2 лад.",

    "Как играть аккорд G?": "Аккорд G: 320003 или 320033. Варианты: 3 пальца или 4 пальца.",
    "Аккорд G": "G: 320003. Первый палец - 5 струна 2 лад, второй - 6 струна 3 лад, третий - 1 струна 3 лад.",

    "Какие песни играть на Am, C, G?": "Песни: 'Цой - Кукушка', 'Сплин - Выхода нет', 'Кино - Группа крови'.",
    "Песни на аккорды Am C G": "Простые песни: 'Кино - Звезда', 'Сплин - Романс', 'ДДТ - Что такое осень'.",
    "Песни для начинающих": "На Am, C, G: 'Цой - Кукушка', 'Кино - Пачка сигарет', 'Сплин - Выхода нет'.",

    "Как настроить гитару?": "Стандартный строй: E A D G B e (Ми Ля Ре Соль Си ми). Используйте тюнер или приложение.",
    "Настройка гитары": "1 струна - E (ми), 2 - B (си), 3 - G (соль), 4 - D (ре), 5 - A (ля), 6 - E (ми).",

    "Как играть перебор?": "Простой перебор: 4-3-2-3-1-3-2-3. Большой палец играет басовые струны (4-5-6).",
    "Перебор на гитаре": "Перебор 'восьмёрка': 5-3-2-3-1-3-2-3. Практикуйте медленно, затем ускоряйтесь."
}

# 2. Инициализация модели и индекса
embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
questions = list(knowledge_base.keys())
question_embeddings = embedder.encode(questions)
question_embeddings = normalize(question_embeddings).astype('float32')

index = faiss.IndexFlatIP(question_embeddings.shape[1])
index.add(question_embeddings)


def get_answer(query):
    clean_query = ' '.join(query.strip().lower().split())

    categories = {
        'аккорд': ['аккорд', 'аккорды', 'am', 'c', 'g', 'd', 'e', 'f'],
        'бой': ['бой', 'шестерк', 'восьмерк', 'ритм'],
        'перебор': ['перебор', 'перебирать'],
        'настройка': ['настройк', 'строй', 'тюнер'],
        'песни': ['песн', 'репертуар', 'играть что']
    }

    detected_category = None
    for category, keywords in categories.items():
        if any(keyword in clean_query for keyword in keywords):
            detected_category = category
            break

    if not detected_category:
        return "Пожалуйста, уточните вопрос. Вот что я умею:\n" \
               "- Объяснять про аккорды (Am, C, G)\n" \
               "- Показывать гитарные бои (шестерка, восьмерка)\n" \
               "- Рассказывать о переборах\n" \
               "- Помогать с настройкой гитары\n" \
               "- Рекомендовать песни для начинающих"

    query_embedding = normalize(embedder.encode(clean_query).reshape(1, -1)).astype('float32')
    D, I = index.search(query_embedding, k=1)
    similarity_percent = (D[0][0] + 1) * 50

    print(f"Сходство: {similarity_percent:.2f}%")

    if similarity_percent > 90:
        return knowledge_base[questions[I[0][0]]]

    response = ollama.chat(
        model="mistral",
        messages=[{
            "role": "system",
            "content": f"Ты гитарный эксперт. Отвечай на вопрос о {detected_category}. "
                       "Будь конкретным и используй профессиональные термины. "
                       "Если вопрос неясен, уточни или дай общий совет."
        }, {
            "role": "user",
            "content": clean_query
        }]
    )
    return response['message']['content']


# 3. Чат-бот
print("Бот. Задавайте вопросы (аккорды, бой, настройка). Для выхода - 'стоп'")

while True:
    user_input = input("Ты: ")
    if user_input.lower() in ['стоп', 'выход', 'exit']:
        break

    answer = get_answer(user_input)
    print(f"Бот: {answer}\n")