# Telegram-бот запису на послуги з адмін-панеллю (демо)

**Демо-проєкт для портфоліо**, не робота для клієнта. Салон, послуги й ціни умовні.

**Задача.** Дати клієнтам записуватися самостійно, а власнику бачити й керувати записами в Telegram.

**Що зроблено.**
- Запис у 4 кроки кнопками: послуга → дата → вільний час → підтвердження.
- Вільні слоти з урахуванням тривалості, графіка й зайнятого часу; один слот не можна зайняти двічі.
- Нагадування клієнту; `/admin`: список записів, скасування одним натиском, експорт CSV.

**Результат.** Логіка слотів, захист від подвійного запису, скасування, експорт і нагадування покриті 8 [тестами](https://github.com/robertvitrovin-droid/demo-telegram-booking-bot/blob/main/tests/test_slots.py). Сценарій клієнта й адміна прогнано через справжні обробники в демо-режимі без токена ([transcript.json](https://github.com/robertvitrovin-droid/demo-telegram-booking-bot/blob/main/demo/transcript.json), [скриншоти](https://github.com/robertvitrovin-droid/demo-telegram-booking-bot/tree/main/screenshots)).

**Посилання.** [Код на GitHub](https://github.com/robertvitrovin-droid/demo-telegram-booking-bot)

Стек: Python, aiogram 3, SQLite, asyncio, pytest · **Ціна від 5 000 грн**, від 3 днів
