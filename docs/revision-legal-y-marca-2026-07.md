# Revisión legal y de marca — Pogo-lab

- **Fecha:** 2026-07-19
- **Alcance:** descargo de responsabilidad, política de privacidad, términos de servicio y licencias
  (`templates/legal/disclaimer.html`, `privacy.html`, `tos.html`, `README.md`, `pyproject.toml`), más
  contraste con la implementación (registro, consentimiento, seguridad, assets de marca).
- **Método:** lectura íntegra de los documentos + verificación de que las afirmaciones coincidan con el código
  actual. Se hizo *spot-check* de las declaraciones de seguridad; **esto NO es una auditoría de seguridad**.

## Supuestos de encuadre (confirmados con el responsable)

| Dimensión | Valor | Consecuencia |
|---|---|---|
| Responsable del tratamiento | **Persona física en Chile** | Sin razón social; se identifica con nombre + contacto. Ley principal: **Ley 19.628** (vigente) y la inminente **Ley 21.719**. |
| Mercado/audiencia | **LatAm / hispanohablantes** | GDPR aplica solo si hay usuarios UE de hecho; el marco líder es el chileno. |
| Licencia del código | **Privado / todos los derechos reservados** | La afirmación "código abierto" del ToS es incorrecta y debe eliminarse. |

> **Aviso.** Esta es una revisión profesional para priorizar correcciones y señalar vacíos e inconsistencias; **no
> es asesoría jurídica**. Los hallazgos de hechos y de coherencia se afirman de forma directa. Los puntos de
> criterio legal (umbral de edad para menores, alcance exacto de la Ley 21.719, certeza de marca, elección de la
> base legal) se marcan como *confirmar con abogado*.

---

## Resumen ejecutivo

Los documentos están **bien encaminados**: el descargo de afiliación es sólido y consistente en tres lugares, la
postura de privacidad-por-diseño (opt-in, anonimización, revocación) es genuina y está respaldada por
[ADR-0005](adr/0005-separacion-datos-privados-publicos.md), y no se usan assets con IP de terceros. El trabajo
pendiente es de **precisión y completitud**, no de reescritura.

Hay **3 bloqueantes** que resolver antes de la beta, todos de arreglo rápido:

1. **No se nombra al responsable** y se pide ejercer derechos **abriendo un issue público** de GitHub.
2. El ToS dice "**código abierto**" cuando el código es privado (y no hay archivo `LICENSE`).
3. La política afirma **Argon2** pero el sistema usa **PBKDF2** (afirmación de seguridad inexacta).

---

## BLOQUEANTES — resolver antes de la beta

### B1 · Sin identidad del responsable + derechos ejercidos por issue público
- **Documentos:** [privacy.html:55](../templates/legal/privacy.html#L55) y
  [tos.html:51](../templates/legal/tos.html#L51).
- **Texto exacto:** *"Para ejercer tus derechos de privacidad, abre un issue en el repositorio del proyecto."*
- **Problema:** (a) Ningún documento nombra al **responsable del tratamiento** ni un medio de contacto. Identificar
  al responsable es obligatorio bajo la Ley 19.628/21.719 (y GDPR Art. 13). (b) Pedir que el usuario ejerza acceso o
  supresión **en un issue público** lo obliga a divulgar en abierto que es usuario y, potencialmente, datos
  personales. Es un **daño de privacidad activo**, no solo un dato faltante.
- **Por qué importa:** es la falla de privacidad más aguda y la más fácil de arreglar.
- **Fix:** nombrar al responsable (persona física: nombre + país) y dar un **correo de contacto privado**
  (p. ej. `privacidad@pogo-lab.com`). Reemplazar "abre un issue" por ese correo en privacidad **y** en ToS.

### B2 · Contradicción de licencia: "código abierto" vs. repo sin licencia y código privado
- **Documentos:** [tos.html:45](../templates/legal/tos.html#L45), [README.md](../README.md) (§Licencias),
  [pyproject.toml:8](../pyproject.toml#L8) (`license = { text = "Por definir" }`).
- **Texto exacto:** *"El código fuente de Pogo-lab es abierto... sujetos a la licencia del repositorio."*
- **Problema:** el código es **privado / todos los derechos reservados** y **no existe archivo `LICENSE`** en la
  raíz. Sin licencia, el estado por defecto es "todos los derechos reservados", de modo que la afirmación "código
  abierto" es **falsa e induce a error** (alguien podría copiar/reutilizar creyendo tener permiso).
- **Matiz importante:** el repositorio de GitHub es **público**. Un repo público sin licencia deja el código
  *visible* pero **no reutilizable**. Si la intención es que nadie lo vea, hay que volver el repo **privado**; si se
  acepta que sea visible pero no reutilizable, basta con la nota de copyright.
- **Fix:** eliminar "El código fuente de Pogo-lab es abierto" del ToS; ajustar el README; añadir nota
  *"© 2026 [nombre]. Todos los derechos reservados."*; poner `license = { text = "Proprietary" }` (o equivalente) en
  `pyproject.toml`. Decidir explícitamente repo público-visible vs. privado.

### B3 · Afirmación de seguridad inexacta (Argon2 declarado, PBKDF2 en uso)
- **Documento:** [privacy.html:49](../templates/legal/privacy.html#L49).
- **Texto exacto:** *"...hashing seguro de contraseñas (Argon2), cabeceras de seguridad (CSP, HSTS)..."*
- **Evidencia:** `PASSWORD_HASHERS` solo se define en [test.py](../config/settings/test.py); ni `base.py` ni
  `prod.py` lo configuran, así que Django usa su hasher por defecto (**PBKDF2**) pese a tener `argon2-cffi`
  instalado. Las otras dos afirmaciones **sí** son ciertas: CSP existe
  ([base.py:144](../config/settings/base.py#L144), dict de django-csp 4.x) y HSTS también
  ([prod.py:9](../config/settings/prod.py#L9), `SECURE_HSTS_SECONDS = 31536000`).
- **Problema:** declaración factual **incorrecta** sobre una medida de seguridad, en un documento legal. PBKDF2 es
  seguro, pero nombrar Argon2 cuando no se usa es una inexactitud que podría verse como engañosa.
- **Fix (recomendado):** configurar Argon2 como primer hasher en `base.py`
  (`PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher", ...]`) para que la afirmación sea
  cierta. **Alternativa:** cambiar el texto a "PBKDF2".

---

## ALTOS

### A1 · Falta ley aplicable y jurisdicción en el ToS
- El ToS no tiene cláusula de **ley aplicable**, **foro/resolución de disputas**, **divisibilidad** ni **acuerdo
  completo**. Para un ToS real conviene añadirlas.
- **Fix:** sección "Ley aplicable y jurisdicción" → ley chilena y tribunales competentes de Chile; cláusula de
  divisibilidad.

### A2 · Encuadre normativo desalineado con la operación
- La política encabeza los derechos bajo **"GDPR"** ([privacy.html:26](../templates/legal/privacy.html#L26),
  [39](../templates/legal/privacy.html#L39)), pero el responsable es una persona en **Chile** y el mercado es LatAm.
- La ley líder es la **Ley 19.628** (vigente) y, de forma inminente, la **Ley 21.719** (publicada 12/2024; entra en
  vigor ~12/2026 — a meses de esta fecha; crea la Agencia de Protección de Datos Personales y régimen de multas).
  El catálogo de derechos ya listado (acceso, rectificación, supresión, portabilidad, revocación) es compatible con
  el modelo chileno estilo-GDPR.
- **Fix:** reencuadrar los encabezados bajo la ley chilena; conservar la referencia a GDPR solo para usuarios UE de
  hecho. *Confirmar con abogado* la fecha exacta de entrada en vigor y las obligaciones concretas de la 21.719.

### A3 · Menores: gate de 13 años no aplicado y sin sección en privacidad
- **ToS:** [tos.html:25](../templates/legal/tos.html#L25) — *"Debes tener al menos 13 años..."* pero **no hay campo
  de edad** en el registro (no existe `apps/accounts/forms.py` con validación de edad, ni fecha de nacimiento en el
  template de signup). La regla se **afirma pero no se aplica**.
- La política de privacidad **no tiene sección de menores (NNA)**. La Ley 21.719 exige protección reforzada de datos
  de niñas, niños y adolescentes (habitualmente consentimiento del representante). "13" es el umbral **COPPA**
  (EE.UU.), no necesariamente el chileno.
- **Fix:** (a) *confirmar con abogado* el umbral conforme a la ley chilena; (b) añadir sección "Menores" a la
  privacidad; (c) si se mantiene 13+, incluir al menos una **casilla de afirmación de edad** en el registro (la
  autoafirmación es débil, pero es mejor que la regla puramente declarativa actual).

### A4 · Licencia de salida del dataset comunitario "por definir"
- **ToS:** [tos.html:39](../templates/legal/tos.html#L39) otorga a Pogo-lab licencia para usar las contribuciones en
  datasets públicos, pero la licencia **bajo la que se publica** el dataset no está definida (README:
  "CC BY / CC0 a decidir").
- **Problema:** sin licencia de salida, quien descargue el dataset no tiene derechos claros, y la promesa de
  "dataset público" es ambigua.
- **Fix:** decidir la licencia (CC BY 4.0 o CC0) y declararla en la página de descarga y en el ToS. Ya reconocido en
  el README como "sujeto a revisión legal antes de la beta".

---

## MEDIOS

### M1 · Bases legales solapadas (consentimiento vs. interés legítimo)
- [privacy.html:29-30](../templates/legal/privacy.html#L29-L30) lista *consentimiento* para el dataset comunitario y
  *interés legítimo* para "análisis agregados". Si ambos son el **mismo** tratamiento, mezclar bases es problemático.
- Es defendible **si** son tratamientos distintos: dashboard/análisis del propio usuario (ejecución del contrato) vs.
  *pooling* comunitario (consentimiento).
- **Fix:** que la política lo **explicite** en esos términos. (Recomendación de redacción, no error rotundo.)

### M2 · Ubicación de datos / transferencias no mencionada
- La política no dice dónde se alojan los datos. Como el hosting es **OCI Santiago (Chile)** y el mercado es LatAm,
  **no** hay transferencia internacional problemática — es incluso un punto a favor.
- **Fix:** añadir una línea *"Tus datos se alojan en servidores en Chile"*; actualizar si en el futuro se mueve fuera.

### M3 · Coherencia del derecho de supresión con snapshots inmutables
- [privacy.html:37](../templates/legal/privacy.html#L37): *"...se eliminan irreversiblemente"* + *"las contribuciones
  ya agregadas no son reversibles"*. Esto es sostenible **solo si** el dataset publicado está **verdaderamente
  anonimizado** (irreversible), no seudonimizado. El [ADR-0005](adr/0005-separacion-datos-privados-publicos.md) y la
  implementación (excluye `notes`, sin nombre de entrenador ni ubicación precisa, solo país agregado, `dedup_hash`,
  umbral mínimo) apuntan a anonimización real.
- **Fix:** que la política **afirme explícitamente** que los datos del dataset están anonimizados de forma
  irreversible (por eso quedan fuera del derecho de supresión). La afirmación de "borrado sin PII residual" del
  hardening M7 debe **re-verificarse en el código actual** en una auditoría de seguridad aparte (fuera del alcance
  de esta revisión documental).

---

## BAJOS

- **Bj1 · README desactualizado:** dice *"🚧 Planificación — aún no hay código"* cuando M0–M7 están completos. En un
  repo público induce a error. Actualizar el estado.
- **Bj2 · Disclaimer sin fecha:** privacidad y ToS tienen "Última actualización"; el descargo no. Añadir por
  consistencia.
- **Bj3 · "conservas la propiedad de tus datos"** ([tos.html:39](../templates/legal/tos.html#L39)): en la mayoría de
  jurisdicciones los datos/hechos no son "propiedad" en sentido estricto. Reformular como *"conservas el control de
  tus datos"*.
- **Bj4 · Dominio de correo:** `DEFAULT_FROM_EMAIL` usa `noreply@pogo-lab.com`
  ([prod.py:16](../config/settings/prod.py#L16)). Asegurar el control del dominio y un buzón de contacto real antes
  de la beta (ligado a B1).

---

## Marca / propiedad intelectual

### Lo que está bien hecho
- **Descargo de afiliación completo y consistente** en tres lugares: [disclaimer.html:12](../templates/legal/disclaimer.html#L12)
  (Niantic, The Pokémon Company, Nintendo, Creatures Inc.), footer [base.html:208](../templates/base.html#L208) y
  README. Es un uso **nominativo/referencial** correcto.
- **Sin assets con IP de terceros:** `static/` solo contiene `pogo-lab.svg` y `og-image.svg`. El logo
  ([includes/_logo_icon.html](../templates/includes/_logo_icon.html)) es un **diseño original** (círculos
  concéntricos + un trazo tipo órbita), **no** una Pokéball ni un sprite. Riesgo bajo.
- El README declara "sin logos/sprites oficiales, sin APIs privadas, sin automatización del juego" — postura
  defensiva correcta.

### Riesgos a vigilar
- **El nombre del producto "Pogo-lab":** "Pogo" es la abreviatura comunitaria de "Pokémon GO", que contiene la marca
  registrada **"Pokémon"**. Un producto **nombrado** con una alusión a la marca tiene **más exposición** que el uso
  nominativo en el cuerpo del texto. No es infractor per se (muchas herramientas comunitarias lo hacen), pero es la
  **mayor exposición de marca** del proyecto. Recomendación: mantener el descargo prominente, **no** estilizar el
  nombre con tipografía/colores oficiales de Pokémon, y estar preparado para un *rebrand* si Niantic/TPC objeta.
  *Si se busca certeza, consultar a un abogado de marcas.*
- **Nombres de especies** en la UI: uso nominativo casi inevitable; riesgo bajo. Evitar imágenes/sprites oficiales
  (ya se hace).
- **Dominio:** `pogo-lab.com` **no** incorpora la cadena "pokemon/pokémon" — bien.

---

## Plan de acción priorizado

**Antes de la beta (bloqueantes, arreglo rápido):**
1. B1 — Nombrar responsable + correo de contacto privado; quitar "abre un issue" de privacidad y ToS.
2. B2 — Quitar "código abierto" del ToS; añadir nota de copyright; `pyproject` → Proprietary; decidir repo
   público-visible vs. privado.
3. B3 — Configurar Argon2 como primer hasher (o corregir el texto a PBKDF2).

**Antes de la beta (altos):**
4. A1 — Cláusula de ley aplicable y jurisdicción (Chile) + divisibilidad.
5. A2 — Reencuadrar la privacidad bajo la ley chilena (19.628 / 21.719); GDPR solo para UE de hecho.
6. A3 — Sección "Menores" + casilla de edad en registro; *confirmar umbral con abogado*.
7. A4 — Decidir y declarar la licencia de salida del dataset (CC BY 4.0 / CC0).

**Deseables (medios/bajos):** M1 (separar bases legales), M2 (ubicación de datos), M3 (afirmar anonimización
irreversible), Bj1–Bj4 (README, fecha del descargo, "control" vs "propiedad", dominio de correo).

**Puntos de criterio a validar con abogado:** umbral de edad y trato de menores bajo la Ley 21.719; alcance y fecha
de entrada en vigor de la 21.719; elección definitiva de base legal (consentimiento vs. interés legítimo); certeza
de marca sobre el nombre "Pogo-lab".
