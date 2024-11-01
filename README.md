- [eXwonder-backend](#exwonder-backend)
   * [Установка](#installation)
   * [Краткое описание функционала](#description)
   * [Скриншоты из frontend клиента](#screenshots)
   * [Лицензия](#license)

<!-- TOC --><a name="exwonder-backend"></a>
# eXwonder-backend
Backend онлайн хостинга картинок __eXwonder__, являющегося по функционалу урезанной версией Instagram. Код написан на Python фреймворке [Django 5](https://www.djangoproject.com/), использует [PostgreSQL](https://www.postgresql.org/) как основную БД, [Redis](https://github.com/redis/redis) для кэширования и брокинга сообщений, [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) для обработки очередей задач.

<!-- TOC --><a name="installation"></a>
## Установка
1. Клонируем репозиторий:
```cmd
git clone https://github.com/waflawe/eXwonder-backend.git
cd eXwonder-backend/
```
2. Устанавливаем зависимости:
```cmd
pip install -r requirements.txt
```
3. Применяем миграции:
```cmd
python manage.py migrate
```
4. Запускаем отдельно три окна терминала. В первом запускаем `redis` (убедитесь, что он установлен у вас на компьютере):
```cmd
redis-server
```
5. Во втором запускаем `celery`:
```cmd
celery -A core.celery_setup:app worker --loglevel=info
```
6. В третем запускаем сам проект:
```cmd
python manage.py runserver 0.0.0.0:8000
```
7. API будет доступно по адресу: `http://localhost:8000/api/v1/`, документация: `http://localhost:8000/api/v1/schema/docs/`
<!-- TOC --><a name="description"></a>
## Краткое описание функционала
1. Создание и вход в аккаунт.
2. Сброс пароля, двухфакторная аутентификация, изменение пароля аккаунта.
3. Подписки и подписчики.
4. Страница новостей (посты от аккаунтов в подписках за последний час).
5. Создание поста, его удаление, просмотр, лайки, добавление в сохраненные.
6. Комментарии к посту, их создание, лайки, удаление.
7. Глобальный поиск аккаунтов.
8. Страница исследования (последние добавленные посты, самые залайканые посты).
9. Просмотр аккаунтов пользователей.
10. Изменение настроек аккаунта (временная зона, 2FA, почта для сброса пароля, аватарка). 
<!-- TOC --><a name="screenshots"></a>
## Скриншоты из frontend клиента
Доступны [здесь](https://github.com/waflawe/eXwonder-frontend/blob/main/README.md).
<!-- TOC --><a name="license"></a>
## Лицензия
У этого проекта [MIT лицензия](https://github.com/waflawe/eXwonder-backend/blob/main/LICENSE).

