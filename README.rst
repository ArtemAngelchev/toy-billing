Общая информация
================

  Toy billing service


Запуск тестов (миграции накатывать отдельно не нужно)
-----------------------------------------------------

    ::

        make test


Накат миграций
--------------

    ::

        make db-upgrade


Локальный запуск
----------------

    ::

        make run-local


Боевой запуск
-------------

    ::

        make run


Примеры запросов
----------------

  Создание клиента
  ~~~~~~~~~~~~~~~~

  ::

    POST /v1/customer HTTP/1.1
    Content-Type: application/json

    {"name": "Иванов"}


  Получение клиента
  ~~~~~~~~~~~~~~~~~

  ::

    GET /v1/customer/1 HTTP/1.1


  Обновление клиента
  ~~~~~~~~~~~~~~~~~~

  ::

    PUT /v1/customer/1 HTTP/1.1
    Content-Type: application/json

    {"name": "Сидоров"}


  Удаление клиента
  ~~~~~~~~~~~~~~~~

  ::

    DELETE /v1/customer/1 HTTP/1.1


  Пополнение счета
  ~~~~~~~~~~~~~~~~

  ::

    POST /v1/customer/1/replenishment HTTP/1.1
    Content-Type: application/json

    {"amount": 200}


  Перевод на счет другого клиента
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  ::

    POST /v1/customer/1/transfer HTTP/1.1
    Content-Type: application/json

    {"customer_id": 2, "amount": 100}
