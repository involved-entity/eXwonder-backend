- [eXwonder-backend](#exwonder-backend)
   * [Установка](#installation)
   * [Краткое описание функционала](#description)
   * [Скриншоты из frontend клиента](#screenshots)
   * [Лицензия](#license)

<!-- TOC --><a name="exwonder-backend"></a>
# eXwonder-backend
__Backend__ часть полноценной социальной сети, основанной на картинках `eXwonder`, вдохновленной `Instagram`. 
Код написан на Python фреймворке __[Django REST Framework](https://www.djangoproject.com/)__, использует __[PostgreSQL](https://www.postgresql.org/)__ как основную БД, 
__[Redis](https://github.com/redis/redis)__ для кэширования, __[RabbitMQ](https://github.com/rabbitmq/rabbitmq-server)__ в качестве брокера сообщений, __[Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html)__ 
для обработки очередей задач. Также применяется библиотека __[dj-rest-auth](https://github.com/iMerica/dj-rest-auth)__ для операций с аккаунтом 
через REST API, к которому также имеется Swagger-схема, сгенерированная при помощи 
__[drf-spectacular](https://github.com/tfranzel/drf-spectacular/)__. Сервер `Live-Time` уведомлений и мессенджер написаны на __[Channels](https://github.com/django/channels)__, используемый линтер 
и форматер кода - __[ruff](https://github.com/astral-sh/ruff)__.

У проекта есть __[Frontend клиент](https://github.com/wellwe11well/eXwonder-frontend/)__.
<!-- TOC --><a name="installation"></a>
## Установка
Перед установкой убедитесь, что у вас установлен менеджер пакетов `uv`, `Redis` и `RabbitMQ` (если вы хотите использовать его как брокер сообщений вместо `Redis`).
1. Клонируем репозиторий:
```cmd
git clone https://github.com/wellwe11well/eXwonder-backend.git
cd eXwonder-backend/
```
2. Устанавливаем зависимости:
```cmd
uv sync
```
3. Создайте файл `.env` и настройте его по примеру файла `.env.template`.
4. Применяем миграции:
```cmd
uv run python manage.py migrate
```
5. Запускаем отдельно три окна терминала. В первом запускаем `celery`:
```cmd
./scripts/celery.sh
```
6. Во втором запускаем основной сервер:
```cmd
./scripts/run.sh
```
7. В третем запускаем сервер уведомлений и мессенджер:
```cmd
./scripts/asgi.sh
```
8. Готово. API будет доступно по адресу: `http://localhost:8000/api/v1/`, а документация к нему - 
`http://localhost:8000/api/v1/schema/docs/`. Сервер `WebSocket` уведомлений будет расположен на 
`ws://localhost:8001/`, а мессенджер - `ws://localhost:8001/messenger/`.
<!-- TOC --><a name="description"></a>
## Краткое описание функционала
1. Создание аккаунта, вход, сброс пароля, 2-х факторная аутентификация, изменение пароля аккаунта.
2. Подписки и подписчики.
3. Операции с постами, а именно:
	- Создание, удаление, просмотр
	- Лайки, теги
	- Добавление в список сохраненных
	- Закрепление постов в профиле
4. Комментарии к посту, лайки комментариев, удаление комментариев.
5. Страница новостей (посты от аккаунтов в подписках за время вашего отсутствия).
6. Страница с рекоммендациями, последними добавленными и самыми залайканными постами.
7. Страница с сохраненными постами.
8. Полноценные `Live-Time` `WebSocket` уведомления.
9. Полноценный `Live-Time` `WebSocket` мессенджер.
10. Глобальный поиск аккаунтов.
11. Кастомизация аккаунта настройками, среди прочих:
	* Публичные:
		* Имя
		* Описание аккаунта
		* Аватар пользователя
	* Приватные:
		* Временная зона
		* Почта
		* Статус включения 2-факторной аутентификации
		* Статус приватности аккаунта (позволяет скрыть аккаунт из поиска)
		* Статус определения круга пользователей, способного оставлять комментарии к постам аккаунта
<!-- TOC --><a name="screenshots"></a>
## Скриншоты из frontend клиента
Доступны [здесь](https://github.com/wellwe11well/eXwonder-frontend/blob/main/README.md).
<!-- TOC --><a name="license"></a>
## Лицензия
У этого проекта [MIT лицензия](https://github.com/wellwe11well/eXwonder-backend/blob/main/LICENSE).

