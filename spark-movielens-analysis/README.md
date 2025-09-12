# Анализ кинорейтингов MovieLens с помощью Apache Spark (SparkSQL)

## 🎯 О проекте

Это учебный проект, целью которого было освоить базовые навыки работы с Apache Spark. В ходе проекта я развернул Spark в Docker-контейнере, загрузил в него набор данных MovieLens и выполнил несколько аналитических SQL-запросов для поиска инсайтов.

## 🛠️ Инструменты

*   **Docker:** для быстрого развертывания изолированного окружения.
*   **Apache Spark:** для распределенной обработки данных.
*   **PySpark / SparkSQL:** для написания аналитических запросов.

---

## 📈 Анализ и результаты

Были загружены два набора данных: `movies.csv` и `ratings.csv`. На их основе были даны ответы на следующие вопросы.

### Вопрос 1: Какие 10 фильмов получили больше всего оценок?

**Запрос:**
```sql
SELECT m.title, COUNT(r.rating) AS rating_count 
FROM ratings r 
JOIN movies m ON r.movieId = m.movieId 
GROUP BY m.title 
ORDER BY rating_count DESC 
LIMIT 10;
```

**Результат:**
*(➡️ Сюда скопируйте таблицу с результатом из вашего терминала)*

### Вопрос 2: Какие 10 фильмов имеют самый высокий средний рейтинг (при условии, что их оценили не менее 50 раз)?

**Запрос:**
```sql
SELECT m.title, AVG(r.rating) AS avg_rating 
FROM ratings r 
JOIN movies m ON r.movieId = m.movieId 
GROUP BY m.title 
HAVING COUNT(r.rating) > 50 
ORDER BY avg_rating DESC 
LIMIT 10;
```

**Результат:**
*(➡️ Сюда скопируйте таблицу с результатом из вашего терминала)*

---
