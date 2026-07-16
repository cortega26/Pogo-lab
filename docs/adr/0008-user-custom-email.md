# ADR-0008 — Modelo User custom con email como login

- **Estado:** Aceptada
- **Fecha:** 2026-07-16
- **Relacionadas:** `plan.md` §E · ADR-0001 · ADR-0005

## Contexto

Django recomienda definir un modelo `User` propio **desde el inicio** del proyecto: cambiarlo una vez que existen
datos y migraciones dependientes es una operación costosa y arriesgada (swap de `AUTH_USER_MODEL`). El MVP se
implementó inicialmente con el `auth.User` por defecto + `UserProfile`; la **auditoría de M0/M1 lo detectó cuando
aún no había datos** — el momento barato para corregirlo. El producto usa email como identificador (§E: "User,
email como login").

## Decisión

`apps.accounts.User` extiende `AbstractUser` con **email único como `USERNAME_FIELD`**, sin `username`
(`username = None`), y un `UserManager` propio (`create_user`/`create_superuser` basados en email).
`AUTH_USER_MODEL = "accounts.User"`. allauth se configura con `ACCOUNT_USER_MODEL_USERNAME_FIELD = None` y login por
email. `UserProfile` mantiene la relación 1:1 con `settings.AUTH_USER_MODEL`.

## Alternativas consideradas

- **`auth.User` por defecto + `UserProfile`** (estado inicial): funciona con allauth, pero introducir un User custom
  más adelante, con datos existentes, exige una migración de *swap* dolorosa. Rechazado por deuda estructural.
- **User con `username` + email**: mantiene un campo `username` semánticamente inútil en un producto email-first.

## Consecuencias

- **Positivas:** extensible sin migración de swap; email-first coherente; tipado correcto con django-stubs vía
  `BaseUserManager["User"]`.
- **Negativas / costes:** un `UserManager` propio y configuración extra de allauth; ligera fricción de django-stubs.
- **Mitigaciones:** override de mypy **acotado a `apps.accounts.models`** (`misc`, `assignment`); cubierto por smoke
  tests.

## Reversibilidad

Baja una vez existan datos (por eso se hizo ahora, sin datos). Añadir campos al User es trivial en adelante.
