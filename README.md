# AccountingPlus

Це веб-додаток, розроблений на фреймворку Django.

## Структура проєкту

Нижче наведено опис основних директорій та додатків проєкту:

*   `accountingplus/`: Основний каталог проєкту, що містить глобальні налаштування (`settings.py`), конфігурацію URL (`urls.py`) та інші файли, необхідні для роботи Django.

*   `persons/`: Додаток Django, що відповідає за функціональність, пов'язану з управлінням даними про осіб. Він містить моделі, представлення, форми та шаблони для цієї частини функціоналу.

*   `assets/`: Каталог для зберігання статичних файлів, таких як CSS, JavaScript та зображення, які використовуються в проєкті.

*   `data/`: Призначений для зберігання файлів з даними, наприклад, JSON-файлів, які можуть використовуватися для заповнення бази даних або для інших потреб.

*   `static/`: У цьому каталозі збираються всі статичні файли проєкту перед розгортанням.

*   `templates/`: Містить базові HTML-шаблони, які використовуються в усьому проєкті.

*   `weasyprint/`: Модуль, що забезпечує інтеграцію з бібліотекою `WeasyPrint` для генерації PDF-документів.

## Встановлення та запуск

Нижче наведено інструкції для налаштування та запуску проєкту на різних операційних системах.

### macOS

1.  **Встановлення Homebrew (якщо не встановлено):**
    Homebrew — це менеджер пакунків для macOS, який спрощує встановлення програмного забезпечення. Щоб встановити його, відкрийте термінал та виконайте команду:
    ```bash
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```

2.  **Встановлення Python 3.9:**
    ```bash
    brew install python@3.9
    ```

3.  **Встановлення PostgreSQL:**
    ```bash
    brew install postgresql
    ```
    Після встановлення запустіть сервіс PostgreSQL:
    ```bash
    brew services start postgresql
    ```
    Створіть нового користувача та базу даних для проєкту:
    ```bash
    createuser -s Login
    createdb accounting_plus --owner=Login
    ```
    Встановіть пароль для користувача `Login`:
    ```bash
    psql -c "ALTER USER Login WITH PASSWORD 'Password';"
    ```

4.  **Встановлення залежностей для WeasyPrint:**
    ```bash
    brew install pango cairo libffi
    ```

5.  **Клонування репозиторію:**
    ```bash
    git clone ./
    cd <назва-директорії-проєкту>
    ```

6.  **Створення та активація віртуального середовища:**
    ```bash
    python3.9 -m venv venv
    source venv/bin/activate
    ```

7.  **Встановлення залежностей проєкту:**
    ```bash
    pip install -r requirements.txt
    ```

8.  **Налаштування змінних середовища:**
    Для налаштування підключення до бази даних, вам потрібно встановити наступні змінні середовища. Ви можете зробити це в терміналі перед запуском сервера:
    ```bash
    export DJANGO_DB_ENGINE="django.db.backends.postgresql"
    export DJANGO_DB_NAME="accounting_plus"
    export DJANGO_DB_USER="Login"
    export DJANGO_DB_PASSWORD="Password"
    export DJANGO_DB_HOST="127.0.0.1"
    export DJANGO_DB_PORT="5432"
    ```


9.  **Застосування міграцій та запуск сервера:**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```
    Тепер проєкт буде доступний за адресою `http://127.0.0.1:8000/`.

### Windows

1.  **Встановлення Chocolatey (якщо не встановлено):**
    Chocolatey — це менеджер пакунків для Windows. Щоб встановити його, відкрийте PowerShell від імені адміністратора та виконайте команду:
    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    ```

2.  **Встановлення Python 3.9:**
    ```powershell
    choco install python --version=3.9
    ```

3.  **Встановлення PostgreSQL:**
    ```powershell
    choco install postgresql
    ```
    Після встановлення, відкрийте `psql` та виконайте наступні команди для створення користувача та бази даних:
    ```sql
    CREATE USER Login WITH PASSWORD 'Password';
    CREATE DATABASE accounting_plus OWNER Login;
    ```

4.  **Встановлення залежностей для WeasyPrint (MSYS2):**
    *   Завантажте та встановіть [MSYS2](https://www.msys2.org/#installation), дотримуючись інструкцій на офіційному сайті.
    *   Після встановлення, відкрийте термінал MSYS2 та виконайте команду:
        ```bash
        pacman -S mingw-w64-x86_64-pango
        ```
    *   Закрийте термінал MSYS2.

5.  **Клонування репозиторію:**
    ```bash
    git clone ./
    cd <назва-директорії-проєкту>
    ```

6.  **Створення та активація віртуального середовища:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

7.  **Встановлення залежностей проєкту:**
    ```bash
    pip install -r requirements.txt
    ```

8.  **Налаштування змінних середовища:**
    Для налаштування підключення до бази даних, вам потрібно встановити наступні змінні середовища. Ви можете зробити це в PowerShell перед запуском сервера:
    ```powershell
    $env:DJANGO_DB_ENGINE="django.db.backends.postgresql"
    $env:DJANGO_DB_NAME="accounting_plus"
    $env:DJANGO_DB_USER="Login"
    $env:DJANGO_DB_PASSWORD="Password"
    $env:DJANGO_DB_HOST="127.0.0.1"
    $env:DJANGO_DB_PORT="5432"
    ```

9.  **Застосування міграцій та запуск сервера:**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```
    Тепер проєкт буде доступний за адресою `http://127.0.0.1:8000/`.

### Ubuntu

1.  **Встановлення Python 3.9 та інших необхідних пакетів:**
    ```bash
    sudo apt update
    sudo apt install -y python3.9 python3.9-venv python3-pip git
    ```

2.  **Встановлення PostgreSQL:**
    ```bash
    sudo apt install -y postgresql postgresql-contrib
    ```
    Після встановлення створіть нового користувача та базу даних для проєкту:
    ```bash
    sudo -u postgres createuser -s Login
    sudo -u postgres createdb accounting_plus --owner=Login
    ```
    Встановіть пароль для користувача `Login`:
    ```bash
    sudo -u postgres psql -c "ALTER USER Login WITH PASSWORD 'Password';"
    ```

3.  **Встановлення залежностей для WeasyPrint:**
    ```bash
    sudo apt install -y pango1.0-tools libpango-1.0-0 libpangoft2-1.0-0
    ```

4.  **Клонування репозиторію:**
    ```bash
    git clone ./
    cd <назва-директорії-проєкту>
    ```

5.  **Створення та активація віртуального середовища:**
    ```bash
    python3.9 -m venv venv
    source venv/bin/activate
    ```

6.  **Встановлення залежностей проєкту:**
    ```bash
    pip install -r requirements.txt
    ```

7.  **Налаштування змінних середовища:**
    Для налаштування підключення до бази даних, вам потрібно встановити наступні змінні середовища. Ви можете зробити це в терміналі перед запуском сервера:
    ```bash
    export DJANGO_DB_ENGINE="django.db.backends.postgresql"
    export DJANGO_DB_NAME="accounting_plus"
    export DJANGO_DB_USER="Login"
    export DJANGO_DB_PASSWORD="Password"
    export DJANGO_DB_HOST="127.0.0.1"
    export DJANGO_DB_PORT="5432"
    ```

8.  **Застосування міграцій та запуск сервера:**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```
    Тепер проєкт буде доступний за адресою `http://127.0.0.1:8000/`.
