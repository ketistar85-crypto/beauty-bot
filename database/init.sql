-- database/init.sql
-- Создание таблиц для мультитенантной платформы записи в салон красоты

-- Таблица салонов (главная)
CREATE TABLE IF NOT EXISTS salons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    bot_token VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    subscription_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    working_hours JSONB,
    welcome_message TEXT DEFAULT 'Добро пожаловать!',
    masters_count INTEGER DEFAULT 0,
    appointments_this_month INTEGER DEFAULT 0,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица мастеров
CREATE TABLE IF NOT EXISTS masters (
    id SERIAL PRIMARY KEY,
    salon_id INTEGER REFERENCES salons(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    specialization VARCHAR(255),
    is_active BOOLEAN DEFAULT true
);

-- Таблица услуг
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    salon_id INTEGER REFERENCES salons(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    duration INTEGER NOT NULL,
    price INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true
);

-- Таблица клиентов
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    salon_id INTEGER REFERENCES salons(id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(salon_id, user_id)
);

-- Таблица записей
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    salon_id INTEGER REFERENCES salons(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id),
    master_id INTEGER REFERENCES masters(id),
    service_id INTEGER REFERENCES services(id),
    appointment_time TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица учёта использования по месяцам
CREATE TABLE IF NOT EXISTS subscription_usage (
    id SERIAL PRIMARY KEY,
    salon_id INTEGER REFERENCES salons(id) ON DELETE CASCADE,
    month DATE NOT NULL,
    appointments_count INTEGER DEFAULT 0,
    UNIQUE(salon_id, month)
);

-- Добавляем тестового салона (опционально)
INSERT INTO salons (name, email, bot_token, plan)
SELECT 'Тестовый салон', 'test@example.com', 'test_token_123', 'free'
WHERE NOT EXISTS (SELECT 1 FROM salons WHERE email = 'test@example.com');
