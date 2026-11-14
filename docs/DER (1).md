# SIMTELE-RISK · Modelo de datos

Base de datos: **SQLite** (`esquema.sql`). Datos sintéticos, uso educativo.

## Diagrama Entidad-Relación

![DER](DER_SIMTELE_RISK.png)

```mermaid
erDiagram
    caso_estudio ||--o{ escenario : tiene
    escenario ||--o{ simulacion : origina
    simulacion ||--o{ ejecucion_metodo : ejecuta
    ejecucion_metodo ||--o{ iteracion_resultado : registra
    ejecucion_metodo ||--o| resultado_resumen : resume

    caso_estudio {
        int id PK
        text nombre
        text modelo_version
    }
    escenario {
        int id PK
        int caso_id FK
        text tipo
        text parametros_json
        text fuente_datos
    }
    simulacion {
        int id PK
        int escenario_id FK
        text fecha
        text usuario
        text estado
    }
    ejecucion_metodo {
        int id PK
        int simulacion_id FK
        text metodo
        real tolerancia
        real paso
        int max_iter
        int convergio
        real tiempo_ms
    }
    iteracion_resultado {
        int id PK
        int ejecucion_id FK
        int numero
        text aproximacion_json
        real residual
        real error_abs
        real error_rel
    }
    resultado_resumen {
        int id PK
        int ejecucion_id FK
        text referencia
        text valor_json
        text metrica_error_json
        text interpretacion
    }
```

## Modelo relacional

- **caso_estudio**(<u>id</u>, nombre, modelo_version)
- **escenario**(<u>id</u>, *caso_id*, tipo, parametros_json, fuente_datos)
  - `caso_id` → caso_estudio(id)
  - `tipo` ∈ {NORMAL, ESTRÉS, MAL_CONDICIONADO}
- **simulacion**(<u>id</u>, *escenario_id*, fecha, usuario, estado)
  - `escenario_id` → escenario(id)
- **ejecucion_metodo**(<u>id</u>, *simulacion_id*, metodo, tolerancia, paso, max_iter, convergio, tiempo_ms)
  - `simulacion_id` → simulacion(id)
- **iteracion_resultado**(<u>id</u>, *ejecucion_id*, numero, aproximacion_json, residual, error_abs, error_rel)
  - `ejecucion_id` → ejecucion_metodo(id)
  - UNIQUE(ejecucion_id, numero)
- **resultado_resumen**(<u>id</u>, *ejecucion_id*, referencia, valor_json, metrica_error_json, interpretacion)
  - `ejecucion_id` → ejecucion_metodo(id), UNIQUE (relación 1 a 1)

## Cardinalidades

| Relación | Cardinalidad |
|---|---|
| caso_estudio – escenario | 1 : N |
| escenario – simulacion | 1 : N |
| simulacion – ejecucion_metodo | 1 : N |
| ejecucion_metodo – iteracion_resultado | 1 : N |
| ejecucion_metodo – resultado_resumen | 1 : 1 |

## Persistencia

Los parámetros de entrada se guardan como JSON en `escenario.parametros_json`, lo que permite
**recuperar una simulación y repetir el cálculo** con los mismos datos tras reiniciar la aplicación.
