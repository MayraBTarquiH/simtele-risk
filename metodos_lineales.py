"""
SIMTELE-RISK | Núcleo numérico: teoría de errores + sistemas lineales
Métodos: Jacobi, Gauss-Seidel, LU (Doolittle), Gradiente Conjugado y solución directa de referencia.
Todos los datos son sintéticos (proyecto educativo).
"""
import time
import numpy as np

# ---------------------------------------------------------------------------
# TEORÍA DE ERRORES (transversal)
# ---------------------------------------------------------------------------
def error_abs(x, x_ref):
    return float(np.linalg.norm(np.asarray(x) - np.asarray(x_ref), np.inf))


def error_rel(x, x_ref, eps=1e-15):
    """Error relativo; devuelve NaN (no divide) si ||x_ref|| es ~0."""
    den = float(np.linalg.norm(np.asarray(x_ref), np.inf))
    return error_abs(x, x_ref) / den if den > eps else float("nan")


def error_pct(x, x_ref):
    return 100.0 * error_rel(x, x_ref)


def residual(A, b, x):
    """||b - A x||_inf"""
    return float(np.linalg.norm(b - A @ x, np.inf))


def residual_rel(A, b, x, eps=1e-15):
    nb = float(np.linalg.norm(b, np.inf))
    return residual(A, b, x) / nb if nb > eps else residual(A, b, x)


def sensibilidad(A, b, delta=1e-6, seed=0):
    """Perturba b en un 'delta' relativo y mide cuánto cambia x.
    Cota teórica: ||dx||/||x|| <= kappa(A) * ||db||/||b||."""
    rng = np.random.default_rng(seed)
    x0 = np.linalg.solve(A, b)
    signos = rng.choice([-1.0, 1.0], size=len(b))
    b2 = b + delta * np.abs(b) * signos
    x1 = np.linalg.solve(A, b2)
    rel_b = np.linalg.norm(b2 - b, np.inf) / np.linalg.norm(b, np.inf)
    rel_x = np.linalg.norm(x1 - x0, np.inf) / np.linalg.norm(x0, np.inf)
    kappa = float(np.linalg.cond(A, np.inf))
    return {
        "delta_b_rel": float(rel_b),
        "cambio_x_rel": float(rel_x),
        "amplificacion": float(rel_x / rel_b) if rel_b > 0 else float("nan"),
        "cota_kappa": kappa,
    }


# ---------------------------------------------------------------------------
# PROPIEDADES DE LA MATRIZ (condiciones de convergencia)
# ---------------------------------------------------------------------------
def diagnostico_matriz(A):
    n = A.shape[0]
    simetrica = bool(np.allclose(A, A.T))
    autovalores = np.linalg.eigvalsh((A + A.T) / 2)
    spd = simetrica and bool(autovalores.min() > 0)
    dom_diag = bool(np.all(np.abs(np.diag(A)) > np.sum(np.abs(A), axis=1) - np.abs(np.diag(A))))
    D = np.diag(np.diag(A))
    L = np.tril(A, -1)
    U = np.triu(A, 1)
    T_j = -np.linalg.solve(D, L + U)
    T_gs = -np.linalg.solve(D + L, U)
    return {
        "n": n,
        "simetrica": simetrica,
        "definida_positiva": spd,
        "diag_dominante": dom_diag,
        "autovalor_min": float(autovalores.min()),
        "autovalor_max": float(autovalores.max()),
        "kappa_inf": float(np.linalg.cond(A, np.inf)),
        "kappa_2": float(np.linalg.cond(A, 2)),
        "radio_espectral_jacobi": float(max(abs(np.linalg.eigvals(T_j)))),
        "radio_espectral_gs": float(max(abs(np.linalg.eigvals(T_gs)))),
    }


# ---------------------------------------------------------------------------
# REGISTRO DE ITERACIONES
# ---------------------------------------------------------------------------
def _registro(k, x, A, b, x_ref):
    return {
        "iter": k,
        "x": x.copy(),
        "residual": residual(A, b, x),
        "residual_rel": residual_rel(A, b, x),
        "error_abs": error_abs(x, x_ref),
        "error_rel": error_rel(x, x_ref),
        "error_pct": error_pct(x, x_ref),
    }


def _resultado(nombre, x, hist, convergio, motivo, t0):
    return {
        "metodo": nombre,
        "x": x,
        "historial": hist,
        "iteraciones": hist[-1]["iter"],
        "convergio": convergio,
        "motivo": motivo,
        "tiempo_ms": (time.perf_counter() - t0) * 1000.0,
    }


LIMITE_DIVERGENCIA = 1e12


def _bucle_iterativo(nombre, paso, A, b, x_ref, tol, max_iter, x0):
    t0 = time.perf_counter()
    x = np.zeros_like(b) if x0 is None else x0.astype(float).copy()
    hist = [_registro(0, x, A, b, x_ref)]
    for k in range(1, max_iter + 1):
        x = paso(x)
        reg = _registro(k, x, A, b, x_ref)
        hist.append(reg)
        if not np.isfinite(reg["residual"]) or reg["residual"] > LIMITE_DIVERGENCIA:
            return _resultado(nombre, x, hist, False, "DIVERGE (residual explota)", t0)
        if reg["residual_rel"] < tol:
            return _resultado(nombre, x, hist, True, "residual relativo < tol", t0)
    return _resultado(nombre, x, hist, False, "máx. de iteraciones alcanzado", t0)


# ---------------------------------------------------------------------------
# MÉTODOS
# ---------------------------------------------------------------------------
def jacobi(A, b, x_ref, tol=1e-10, max_iter=1000, x0=None):
    D = np.diag(A)
    R = A - np.diagflat(D)
    return _bucle_iterativo("Jacobi", lambda x: (b - R @ x) / D, A, b, x_ref, tol, max_iter, x0)


def gauss_seidel(A, b, x_ref, tol=1e-10, max_iter=1000, x0=None):
    n = len(b)

    def paso(x):
        x = x.copy()
        for i in range(n):
            x[i] = (b[i] - A[i, :i] @ x[:i] - A[i, i + 1:] @ x[i + 1:]) / A[i, i]
        return x

    return _bucle_iterativo("Gauss-Seidel", paso, A, b, x_ref, tol, max_iter, x0)


def lu_doolittle(A):
    """A = L U (L con diagonal 1). Sin pivoteo: válido para matrices SPD."""
    n = A.shape[0]
    L = np.eye(n)
    U = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            U[i, j] = A[i, j] - L[i, :i] @ U[:i, j]
        if abs(U[i, i]) < 1e-14:
            raise ZeroDivisionError("Pivote nulo: se requiere pivoteo parcial")
        for j in range(i + 1, n):
            L[j, i] = (A[j, i] - L[j, :i] @ U[:i, i]) / U[i, i]
    return L, U


def lu(A, b, x_ref, **_):
    t0 = time.perf_counter()
    L, U = lu_doolittle(A)
    n = len(b)
    y = np.zeros(n)
    for i in range(n):  # sustitución hacia adelante: L y = b
        y[i] = b[i] - L[i, :i] @ y[:i]
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):  # sustitución hacia atrás: U x = y
        x[i] = (y[i] - U[i, i + 1:] @ x[i + 1:]) / U[i, i]
    hist = [_registro(1, x, A, b, x_ref)]
    res = _resultado("LU (Doolittle)", x, hist, True, "método directo", t0)
    res["L"], res["U"] = L, U
    return res


def gradiente_conjugado(A, b, x_ref, tol=1e-10, max_iter=1000, x0=None):
    """CG estándar: requiere A simétrica definida positiva (SPD)."""
    t0 = time.perf_counter()
    x = np.zeros_like(b) if x0 is None else x0.astype(float).copy()
    r = b - A @ x
    p = r.copy()
    rs = r @ r
    hist = [_registro(0, x, A, b, x_ref)]
    for k in range(1, max_iter + 1):
        Ap = A @ p
        denom = p @ Ap
        if denom <= 0:
            return _resultado("Gradiente Conjugado", x, hist, False, "p^T A p <= 0 (A no es SPD)", t0)
        alpha = rs / denom
        x = x + alpha * p
        r = r - alpha * Ap
        hist.append(_registro(k, x, A, b, x_ref))
        if hist[-1]["residual_rel"] < tol:
            return _resultado("Gradiente Conjugado", x, hist, True, "residual relativo < tol", t0)
        rs_new = r @ r
        p = r + (rs_new / rs) * p
        rs = rs_new
    return _resultado("Gradiente Conjugado", x, hist, False, "máx. de iteraciones alcanzado", t0)


def solucion_directa(A, b):
    """Referencia directa (LAPACK)."""
    return np.linalg.solve(A, b)


def ejecutar_todos(A, b, x_ref, tol=1e-10, max_iter=1000):
    ref = solucion_directa(A, b)
    res_ref = {
        "metodo": "Directa (referencia)", "x": ref, "iteraciones": 1, "convergio": True,
        "motivo": "np.linalg.solve", "tiempo_ms": 0.0,
        "historial": [_registro(1, ref, A, b, x_ref)],
    }
    return [
        res_ref,
        jacobi(A, b, x_ref, tol, max_iter),
        gauss_seidel(A, b, x_ref, tol, max_iter),
        lu(A, b, x_ref),
        gradiente_conjugado(A, b, x_ref, tol, max_iter),
    ]


# ---------------------------------------------------------------------------
# ESCENARIOS (NORMAL / ESTRÉS / MAL_CONDICIONADO)
# ---------------------------------------------------------------------------
ESCENARIOS = ["NORMAL", "ESTRÉS", "MAL_CONDICIONADO"]


def config_escenario(escenario):
    if escenario == "NORMAL":
        return dict(n=4, tol=1e-10, max_iter=500, margen=1.0, delta=1e-6, tipo="SPD diagonal dominante")
    if escenario == "ESTRÉS":
        return dict(n=10, tol=1e-12, max_iter=5000, margen=0.05, delta=1e-3, tipo="SPD, n mayor, dominancia débil, tolerancia estricta")
    if escenario == "MAL_CONDICIONADO":
        return dict(n=6, tol=1e-10, max_iter=5000, margen=None, delta=1e-8, tipo="Matriz de Hilbert (SPD, κ enorme)")
    raise ValueError("Escenario desconocido")


def construir_sistema(escenario, n=None, seed=42):
    """Devuelve A, b, x_ref con x_ref conocido y A SPD."""
    cfg = config_escenario(escenario)
    n = n or cfg["n"]
    rng = np.random.default_rng(seed)
    if escenario == "MAL_CONDICIONADO":
        i = np.arange(1, n + 1)
        A = 1.0 / (i[:, None] + i[None, :] - 1.0)  # Hilbert
    else:
        B = rng.uniform(-1, 1, (n, n))
        B = np.triu(B, 1)
        B = B + B.T                                   # simétrica, diagonal cero
        diag = np.sum(np.abs(B), axis=1) + cfg["margen"]
        A = B + np.diag(diag)                         # simétrica, diag. dominante => SPD
    x_ref = np.arange(1, n + 1, dtype=float)
    b = A @ x_ref
    return A, b, x_ref


if __name__ == "__main__":
    for esc in ESCENARIOS:
        cfg = config_escenario(esc)
        A, b, x_ref = construir_sistema(esc)
        print(f"\n=== {esc}  (n={A.shape[0]}, κ∞={np.linalg.cond(A, np.inf):.3e}) ===")
        for r in ejecutar_todos(A, b, x_ref, cfg["tol"], cfg["max_iter"]):
            h = r["historial"][-1]
            print(f"{r['metodo']:<22} conv={str(r['convergio']):<5} it={r['iteraciones']:<5} "
                  f"res_rel={h['residual_rel']:.2e} err_abs={h['error_abs']:.2e}  [{r['motivo']}]")
