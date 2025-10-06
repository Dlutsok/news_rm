-- Добавляем значение RUSMEDICAL в тип enum projecttype (PostgreSQL)
ALTER TYPE projecttype ADD VALUE IF NOT EXISTS 'RUSMEDICAL';


