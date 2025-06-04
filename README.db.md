Aquí está la información estructurada en formato markdown para añadir al README.db.md:

# Base de Datos - Modelo Relacional

## Tablas

### 1. Usuarios (users)
Representa a todas las personas que interactúan con la plataforma.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    profile_picture VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Consideraciones:**
- `is_admin`: Perfecto para el administrador global. Los roles de "organizador", "árbitro" y "jugador" son contextuales a organizaciones y torneos, por lo que se manejan en tablas de relación.

### 2. Organizaciones (organizations)
Entidades que gestionan sus propios torneos (ej. universidades, empresas).

```sql
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Consideraciones:**
- `created_by`: Debería ser NOT NULL si asumimos que un admin siempre las crea.

**Oportunidad de mejora:**
- Podría categorizarse cada organización, para diferenciarlas.

### 3. Miembros de Organización (organization_members)
Tabla de unión para la relación muchos-a-muchos entre usuarios y organizaciones. Define quién pertenece a qué organización y si es organizador de la misma.

```sql
CREATE TABLE organization_members (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    is_organizer BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, user_id)
);
```

**Consideraciones:**
- `is_organizer`: Indica si el user_id tiene rol de organizador dentro de esa organization_id.
- `ON DELETE CASCADE` es útil: si se borra una organización o un usuario, estas membresías se eliminan.

### 4. Actividades (activities)
Tipos de deportes o juegos para los torneos (ej. Fútbol, Ajedrez, LoL).

```sql
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    min_players_per_team INTEGER NOT NULL DEFAULT 1,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Consideraciones:**
- `min_players_per_team`: Importante para la validación al iniciar torneos, los equipos sin esa cantidad serán descartados. El sistema debe validar.

**Oportunidad de mejora:**
- La categorización podría ser más compleja.

### 5. Eventos (events)
Un "Evento" podría agrupar varios torneos dentro de una organización (ej. "Copa Mechona 2026").

```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, name)
);
```

**Consideraciones:**
- La utilización en torneos es opcional.
- Las fechas son de referencia.

### 6. Torneos (tournaments)
Las competiciones específicas creadas dentro de una organización.

```sql
CREATE TABLE tournaments (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE RESTRICT,
    event_id INTEGER REFERENCES events(id) ON DELETE RESTRICT,
    activity_id INTEGER REFERENCES activities(id) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    max_teams INTEGER NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    prizes TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    created_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Consideraciones:**
- Añadí `event_id` como FK opcional.
- El `status` podría tener más variantes como `registration_open` antes de `in_progress` o `cancelled`
- `end_date`: Podría ser calculado cuando el status pase a ser 'completed'

### 7. Árbitros de Torneo (tournament_referees)
Usuarios asignados como árbitros para un torneo específico.

```sql
CREATE TABLE tournament_referees (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    assigned_by INTEGER REFERENCES users(id) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tournament_id, user_id)
);
```

**Consideraciones:**
- Un usuario en esta tabla para un torneo X no debería poder ser miembro de un equipo en el mismo torneo X.

### 8. Equipos (teams)
Equipos creados para participar en un torneo específico.

```sql
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(100) NOT NULL,
    seed_score DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tournament_id, name)
);
```

**Consideraciones:**
- El nombre es genérico al comienzo, pero puede ser personalizable por el líder de equipo.
- No se especifica el líder, eso se especifica al establecer la unión entre equipos y usuarios (team_members).
- `seed_score`: Se calculará por la aplicación antes de iniciar el torneo o bien a medida que ingresan los miembros del equipo.

### 9. Miembros de Equipo (team_members)
Usuarios que son parte de un equipo en un torneo.

```sql
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    is_leader BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, user_id),
    UNIQUE(user_id, team_id)
);
```

**Consideraciones:**
- Un `user_id` no puede estar en más de un equipo para el mismo en el mismo torneo.
- El `user_id` debe pertenecer a la organización del torneo.
- Debe haber al menos un líder por equipo.

### 10. Partidos (matches)
Los enfrentamientos individuales dentro de un torneo.

```sql
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE NOT NULL,
    level INTEGER NOT NULL,
    match_number INTEGER NOT NULL,
    team_a_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    team_b_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    score_team_a INTEGER,
    score_team_b INTEGER,
    winner_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    best_player_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_bye BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','completed')),
    completed_at TIMESTAMP,
    recorded_by_referee_id INTEGER REFERENCES users(id),
    UNIQUE(tournament_id, level, match_number),
    UNIQUE(tournament_id, match_number)
);
```

**Consideraciones:**
- `level` y `match_number` definen la estructura del bracket. Al crear, siempre se estructurará un árbol binario completo.
- `best_player_id`: Debería ser un `user_id` que sea miembro de `team_a_id` o `team_b_id`.
- `recorded_by_referee_id`: Almacena el `user_id` del árbitro que ingresó o modificó por última vez el resultado. Este usuario debe estar en `tournament_referees` para ese torneo.
- La lógica de "si la siguiente llave no ha sido jugada aún" para editar resultados es de aplicación, usando `status` y `completed_at` de los partidos sucesores.

### 11. Invitaciones a Equipos (team_invitations)
Para que los líderes de equipo inviten a otros usuarios.

```sql
CREATE TABLE team_invitations (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE NOT NULL,
    invited_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    invited_by_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, invited_user_id)
);
```

**Consideraciones:**
- Al aceptar, se crea un registro en `team_members` y se cancelan otras invitaciones pendientes para ese usuario en el mismo torneo (lógica de aplicación).

### 12. Notificaciones (notifications)
Para informar a los usuarios sobre eventos relevantes.

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    type VARCHAR(50) NOT NULL,
    related_entity_type VARCHAR(50),
    related_entity_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Consideraciones:**
- `type` puede ayudar a la UI a manejar diferentes tipos de notificaciones con iconos o acciones específicas.
- `related_entity_type` y `related_entity_id` son útiles para enlazar la notificación a la entidad que la originó.

## Resumen de Relaciones y Flujos Clave

### Roles de Usuario:

1. **Administrador (Plataforma):**
   - `users.is_admin = TRUE`
   - Puede crear organizaciones y asignar organizadores
   - Puede crear actividades

2. **Usuario Normal:**
   - `users.is_admin = FALSE`
   - Puede registrarse, unirse a organizaciones, crear equipos, unirse a equipos

3. **Organizador (de Organización):**
   - `organization_members.is_organizer = TRUE` para una `organization_id` específica
   - Puede crear torneos y eventos dentro de su organización
   - Puede asignar árbitros a esos torneos

4. **Árbitro (de Torneo):**
   - Existe una entrada en `tournament_referees` para un `tournament_id` específico
   - Puede registrar/editar resultados de partidos en ese torneo

5. **Líder de Equipo:**
   - `team_members.is_leader = TRUE` para un `team_id` específico
   - Puede invitar miembros al equipo

6. **Jugador/Miembro de Equipo:**
   - Existe una entrada en `team_members` para un `team_id` específico
   - Participa en partidos

### Flujo de Creación de Torneo:

1. Admin (`users`) crea una `organizations`
2. Admin asigna un `users` como organizador (`organization_members.is_organizer = TRUE`)
3. Organizador (`organization_members`) crea un `tournaments` (opcionalmente dentro de un `events`) para una `activities` existente
4. Organizador asigna `users` (que sean parte de la `organizations`) como `tournament_referees`

### Flujo de Participación en Torneo:

1. Usuario (`users`) se une a `organizations` (crea entrada en `organization_members`)
2. Usuario (que no sea árbitro en ese torneo) crea un `teams` para un `tournaments` (se añade a `team_members` como líder)
3. Líder (`team_members`) envía `team_invitations` a otros `users` de la misma `organizations` (que no estén ya en otro equipo del torneo o sean árbitros)
4. Usuario invitado acepta la invitación (se crea entrada en `team_members`, se actualiza `team_invitations.status`)

### Gestión de Partidos:

1. Al iniciar el torneo, la aplicación genera los `matches` (bracket) basado en los `teams` inscritos y sus `seed_score`
2. Un `tournament_referees` registra el resultado (`score_team_a`, `score_team_b`, `best_player_id`) en un `matches`, actualizando su `status` y `winner_id`. El `recorded_by_referee_id` se guarda en `matches`
3. La aplicación actualiza el bracket, propagando el `winner_id` al siguiente `matches` correspondiente
```