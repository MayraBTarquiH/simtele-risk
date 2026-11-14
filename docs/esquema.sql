-- SIMTELE-RISK | Esquema de base de datos (SQLite)
-- Proyecto educativo de Métodos Numéricos. Datos sintéticos.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS caso_estudio (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre         TEXT NOT NULL UNIQUE,
    modelo_version TEXT NOT NULL DEFAULT '1.0'
);

CREATE TABLE IF NOT EXISTS escenario (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id         INTEGER NOT NULL,
    tipo            TEXT NOT NULL CHECK (tipo IN ('NORMAL', 'ESTRÉS', 'MAL_CONDICIONADO')),
    parametros_json TEXT NOT NULL,            -- parámetros de entrada reproducibles (JSON)
    fuente_datos    TEXT NOT NULL DEFAULT 'sintético',
    FOREIGN KEY (caso_id) REFERENCES caso_estudio(id) ON DELETE CASCADE,
    UNIQUE (caso_id, tipo, parametros_json)
);

CREATE TABLE IF NOT EXISTS simulacion (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    escenario_id  INTEGER NOT NULL,
    fecha         TEXT NOT NULL DEFAULT (datetime('now')),
    usuario       TEXT,                       -- usuario/equipo (opcional)
    estado        TEXT NOT NULL DEFAULT 'COMPLETADA'
                  CHECK (estado IN ('PENDIENTE', 'COMPLETADA', 'ERROR')),
    FOREIGN KEY (escenario_id) REFERENCES escenario(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ejecucion_metodo (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacion_id INTEGER NOT NULL,
    metodo        TEXT NOT NULL,              -- Jacobi, Gauss-Seidel, LU, GC, RK4, ...
    tolerancia    REAL,
    paso          REAL,
    max_iter      INTEGER,
    convergio     INTEGER NOT NULL CHECK (convergio IN (0, 1)),
    tiempo_ms     REAL,
    FOREIGN KEY (simulacion_id) REFERENCES simulacion(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS iteracion_resultado (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id      INTEGER NOT NULL,
    numero            INTEGER NOT NULL,       -- número de iteración / paso
    aproximacion_json TEXT NOT NULL,          -- vector o valor aproximado (JSON)
    residual          REAL,
    error_abs         REAL,
    error_rel         REAL,
    FOREIGN KEY (ejecucion_id) REFERENCES ejecucion_metodo(id) ON DELETE CASCADE,
    UNIQUE (ejecucion_id, numero)
);

CREATE TABLE IF NOT EXISTS resultado_resumen (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id       INTEGER NOT NULL UNIQUE,
    referencia         TEXT,                  -- solución analítica o de referencia usada
    valor_json         TEXT NOT NULL,         -- resultado final (JSON)
    metrica_error_json TEXT,                  -- errores finales, κ, sensibilidad (JSON)
    interpretacion     TEXT,
    FOREIGN KEY (ejecucion_id) REFERENCES ejecucion_metodo(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_escenario_caso      ON escenario(caso_id);
CREATE INDEX IF NOT EXISTS idx_simulacion_esc      ON simulacion(escenario_id);
CREATE INDEX IF NOT EXISTS idx_ejecucion_sim       ON ejecucion_metodo(simulacion_id);
CREATE INDEX IF NOT EXISTS idx_iteracion_ejec      ON iteracion_resultado(ejecucion_id);

-- Datos iniciales: los cuatro casos de estudio
INSERT OR IGNORE INTO caso_estudio (nombre) VALUES
    ('Detención de emergencia'),
    ('Deterioro mecánico y mantenimiento'),
    ('Oscilaciones por viento'),
    ('Reconstrucción de sensores');
