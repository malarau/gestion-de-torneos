## MÓDULO 1: Gestión de usuarios

Este módulo proporciona la funcionalidad básica de autenticación y administración de usuarios en el sistema. Permite a los visitantes registrarse, iniciar sesión, editar su información personal y cerrar sesión. El sistema distingue entre diferentes roles de usuario (administrador, organizador, árbitro y jugador), cada uno con permisos específicos según sus responsabilidades.

### N.º 1 - Registro de usuario  
**HISTORIA**  
Como visitante quiero poder crear una cuenta en el sistema proporcionando mi nombre, correo electrónico y contraseña, para acceder a las funcionalidades básicas del sistema  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 5**
1. El visitante debe poder acceder al formulario de registro  
2. El sistema debe poder permitir el registro de cuentas en la base de datos, solicitando nombre, correo electrónico y contraseña  
3. Se debe validar que el correo no está en uso  
4. Se debe validar la longitud de la contraseña, al menos 6 caracteres y máximo de 16  
5. Tras registrarse, el usuario debe ser redirigido a la página de inicio de sesión para utilizar sus credenciales  

### N.º 2 - Inicio de sesión  
**HISTORIA**  
Como usuario registrado, quiero iniciar sesión en el sistema usando mi correo y contraseña para acceder a mi cuenta y utilizar las funcionalidades disponibles según mi rol  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 3**
1. El usuario puede ingresar credenciales en un formulario de inicio de sesión  
2. El sistema debe validar las credenciales del usuario  
3. Debe informarse un error en caso de credenciales inválidas  
4. Si las credenciales son válidas, el usuario es redirigido al dashboard correspondiente a su rol  
5. En el dashboard, el usuario debe poder visualizar las organizaciones a las que pertenece  

### N.º 3 - Edición de información de usuario  
**HISTORIA**  
Como usuario autenticado en el sistema, quiero poder editar mi información de usuario para mantener mis datos actualizados dentro del sistema  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 8**
1. El sistema debe permitir acceder a la visualización y edición de perfiles de usuario desde la interfaz general  
2. El usuario debe poder modificar su información a excepción del correo electrónico  
3. El usuario debe poder subir una foto de perfil  
4. Los cambios deben persistir en la base de datos al presionar el botón de guardar  

### N.º 4 - Cierre de sesión  
**HISTORIA**  
Como usuario autenticado, quiero cerrar mi sesión activa, para mantener la seguridad de mi cuenta cuando no la esté utilizando  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 2**
1. Debe haber una opción visible y accesible para cerrar sesión  
2. Al presionarla, se debe cerrar la sesión y redirigir al usuario al login  

---

## MÓDULO 2: Gestión de organizaciones

Este módulo facilita la creación y administración de entidades organizadoras dentro del sistema. Los administradores pueden crear organizaciones y asignar usuarios como organizadores responsables. Los usuarios pueden unirse a múltiples organizaciones para participar en sus actividades y torneos.

### N.º 5 - Creación de organizaciones  
**HISTORIA**  
Como administrador, quiero crear nuevas organizaciones para permitir a diferentes entidades gestionar sus propios torneos.  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 5**
1. Existe una opción o botón visible solo para administradores que permite acceder a la creación de organizaciones  
2. En la interfaz de creación, debe permitir asignar un nombre único y una descripción  
3. Debe permitir asignar uno o más usuarios como los organizadores de la organización a crear  
4. La organización debe almacenarse en la base de datos y estar disponible para búsquedas posteriores  

### N.º 6 - Edición de organizaciones  
**HISTORIA**  
Como administrador, quiero visualizar y editar la información de una organización ya creada, para mantener la información actualizada y asignar organizadores cuando sea necesario  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 4**
1. Debe permitir editar los campos asociados a una organización  
2. Debe permitir buscar y seleccionar usuarios existentes para asignarlos como organizadores, siempre que no hayan sido asignados previamente  
3. El sistema debe permitir remover usuarios anteriormente asignados como organizadores  

### N.º 7 - Unirse a organizaciones  
**HISTORIA**  
Como usuario autenticado, quiero ver una lista de organizaciones existentes, para poder unirme a ellas, siendo entonces visible como usuario dentro de ese contexto organizacional y así poder participar en sus actividades  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 3**
1. El usuario puede buscar o listar organizaciones  
2. Es visible para el usuario una opción o botón para poder unirse a una organización  
3. Al unirse es asociado a esa organización, siendo visible dentro de sus actividades y pudiendo ver las mismas  
4. El usuario puede pertenecer a múltiples organizaciones, siendo estas listadas en el dashboard principal  

### N.º 8 - Visualización de organizaciones  
**HISTORIA**  
Como usuario autenticado, quiero seleccionar alguna de las organizaciones a las que pertenezco, para ingresar y visualizar sus actividades  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 4**
1. El usuario puede elegir entre las organizaciones a las que pertenece  
2. Al seleccionar una organización, el sistema debe mostrar información relevante de la misma  

---

## MÓDULO 3: Gestión de Actividades

Este módulo permite definir las diferentes actividades compatibles con el sistema. Los administradores pueden crear, editar y administrar actividades que luego estarán disponibles para ser seleccionadas al crear torneos.

### N.º 9 - Creación de actividades  
**HISTORIA**  
Como administrador, quiero crear actividades deportivas o recreativas en el sistema, para que luego puedan ser seleccionadas al crear torneos  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 3**
1. El administrador puede acceder a un formulario para crear nuevas actividades  
2. Debe poder ingresar nombre, descripción, número mínimo de jugadores por equipo y categoría de la actividad
3. Las actividades creadas deben quedar almacenadas y disponibles para selección en la creación de torneos  
4. Se debe validar que no exista ya una actividad con el mismo nombre  

### N.º 10 - Gestión de Actividades  
**HISTORIA**  
Como administrador, quiero visualizar, editar y desactivar actividades, para mantener actualizado el catálogo de actividades disponibles para torneos  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 4**
1. El administrador puede ver un listado de todas las actividades existentes  
2. Puede editar los detalles de cualquier actividad  
3. Puede desactivar actividades para que ya no sean utilizadas en ningún torneo posterior  

---

## MÓDULO 4: Gestión de torneos

Este módulo permite a los organizadores crear y administrar competiciones dentro de sus organizaciones. Los torneos incluyen configuraciones como tipo de actividad, número máximo de equipos, mínimo de participantes por equipo, entre otros parámetros.

> El torneo opera de la siguiente manera: El sistema organiza torneos de eliminación simple mediante un árbol binario completo, donde primero se calcula el tamaño del bracket (potencia de 2 superior al número de equipos) y se asignan *byes* a los mejores semillas para completarlo. Los equipos se ordenan por *seed_score* (mayor = mejor semilla), y los partidos iniciales enfrentan semillas opuestas (mejor vs. peor restante). Cada **Match** incluye los campos: *level* (ronda, siendo 0 la final), *match_number* (posición en el bracket y en el árbol binario, con 1 la raíz, la final), *team_a* y *team_b*, (ids de equipos, opcionales en *byes*), *score_team_a* y *score_team_b* (marcadores), *winner* (determinado al resolverse el partido), *is_bye* (victoria automática) y *status* (*pending* o *completed*). Si es un *bye*, el ganador avanza automáticamente; al registrarse un resultado (mediante un *trigger* que actualice la siguiente llave), el *winner* se asigna al partido correspondiente en la siguiente ronda, repitiéndose el proceso hasta determinar un campeón en la final.

### N.º 11 - Creación de torneos  
**HISTORIA**  
Como organizador, quiero crear torneos dentro de mi organización, para que equipos puedan participar y competir  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 8**
1. Solo organizadores pueden crear torneos en sus respectivas organizaciones  
2. Debe permitir configurar: nombre, descripción, fecha, tipo de actividad (de las previamente creadas), número máximo de equipos participantes, premios y evento al que pertenece (si aplica)  
3. Los torneos se crean inicialmente en estado "pendiente", pudiendo cambiar a "en juego/iniciado" y finalmente "torneo finalizado"  
4. Debe permitir asignar al menos un usuario de esa organización como árbitro (que no participe como jugador en el mismo torneo)  

### N.º 12 - Edición de torneos  
**HISTORIA**  
Como organizador, quiero editar los detalles de un torneo creado, para realizar ajustes necesarios antes de que inicie  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 5**
1. El organizador puede editar los campos configurables del torneo mientras esté en estado "pendiente"  
2. No debe permitirse la edición de campos críticos (como el tipo de actividad o número de equipos) una vez el torneo haya comenzado  
3. Debe permitir reasignar árbitros, siempre que estos no sean participantes  
4. Los cambios deben persistir en la base de datos y reflejarse en la interfaz  

### N.º 13 - Inicio de torneo
**HISTORIA**  
Como organizador, quiero iniciar el torneo, para que el sistema genere automáticamente los emparejamientos y comience la competición  

**CRITERIOS DE ACEPTACIÓN**  
**PH: 14**
1. El organizador tiene una opción o botón para iniciar el torneo  
2. Solo se tienen en cuenta los equipos que cumplen con el requisito de integrantes definido por la Actividad, sistema debe validar que al menos sean 2
3. El sistema genera el bracket de eliminación para los equipos inscritos  
4. Los emparejamientos se basan en un algoritmo simple de puntaje derivado de los jugadores de cada equipo  
5. El torneo deja de aceptar nuevas inscripciones  
6. El torneo cambia su estado a “en curso”, “en juego” o algo similar  
7. Se notifica a los participantes del inicio del torneo  
  

### N.º 14 - Virtualización del bracket del torneo  
**Historia:**  
Como usuario perteneciente a la organización, quiero visualizar el bracket del torneo de eliminación directa, para seguir el progreso de las competencias  

**Criterios de Aceptación**  
**PH:** 8  
1. Todos los usuarios pertenecientes a la organización donde se lleva a cabo el torneo pueden tener una vista del bracket del torneo  
2. Se visualiza los equipos que avanzan  
3. Se muestran los resultados de cada emparejamiento  
4. La información se actualiza de forma automática tras cada resultado registrado  

---

### N.º 15 - Registro de resultados  
**Historia:**  
Como árbitro designado, quiero registrar los resultados de las partidas disputadas, para actualizar el progreso del torneo  

**Criterios de Aceptación**  
**PH:** 7  
1. Para una partida activa el árbitro puede seleccionar al equipo ganador  
2. El equipo ganador avanza en el bracket del torneo  
3. Solo los árbitros asignados a ese torneo, pueden registrar resultados  

---

## MÓDULO 5: Gestión de equipos

Este módulo facilita la formación de equipos para participar en los torneos. Los usuarios pueden crear equipos, convertirse en líderes de equipo e invitar a otros miembros de la organización a unirse.

---

### N.º 16 - Creación de equipos
**Historia:**  
Como usuario perteneciente a una organización, quiero inscribir un equipo a un torneo perteneciente a la misma organización para invitar a otros usuarios y participar del torneo.  

**Criterios de Aceptación**  
**PH:** 6  
1. Visualizando un torneo, el usuario puede crear un equipo para participar si no se ha alcanzado el máximo de equipos permitidos  
2. Un usuario puede crear equipos solo si no ha sido asignado como árbitro o ya se encuentra asociado a un equipo como jugador dentro de ese mismo torneo (ni es organizador de la organización, ni administrador de plataforma)
3. Al crear un equipo, se vuelve un integrante y líder del mismo automáticamente  
4. Los equipos tienen identificadores (nombre) genéricos (puede cambiarse)

### N.º 17 - Eliminación de equipos  
**Historia:**  
Como usuario perteneciente a una organización, quiero eliminar un equipo que haya creado anteriormente para disolver el equipo. 

**Criterios de Aceptación**  
**PH:** 6  
1. Dentro de la vista del equipo, debe existir un botón para eliminar el equipo
2. Solo el líder de equipo puede eliminar su propio equipo
3. Todos los usuarios son liberados y pueden volver a unirse a otro equipo dentro del torneo
4. Solo se permite eliminar si el torneo no ha comenzado aún

---

### N.º 17 - Invitación a miembros de equipo  
**Historia:**  
Como líder de equipo, quiero invitar a otros usuarios que pertenezcan a la misma organización a unirse a mi equipo para poder participar del torneo.  

**Criterios de Aceptación**  
**PH:** 5  
1. Dentro del contexto del torneo, el líder puede buscar usuarios pertenecientes a la misma organización  
2. Identificando a los usuarios puede enviar invitaciones  
3. Los usuarios invitados reciben una notificación del sistema  
4. No se pueden invitar a usuarios que ya sean árbitros o jugadores en otro equipo del mismo torneo  

---

### N.º 18 - Aceptar o rechazar invitaciones a equipos  
**Historia:**  
Como usuario quiero aceptar o rechazar invitaciones para formar parte de un equipo, para participar o declinar la participación en un torneo  

**Criterios de Aceptación**  
**PH:** 3  
1. El usuario puede visualizar una sección de invitaciones pendientes desde la vista del torneo  
2. Para cada invitación, debe existir un botón para aceptar o rechazar  
3. Al aceptar una invitación, el usuario se convierte en jugador del equipo y todas las otras invitaciones son eliminadas automáticamente  
4. Al rechazar se elimina la invitación

---

## MÓDULO 6: Notificaciones

Este módulo proporciona mecanismos para mantener informados a los usuarios sobre eventos relevantes dentro del sistema. Las notificaciones se generan automáticamente para eventos como invitaciones a equipos y cambios en el estado de los torneos.

---

### N.º 19 - Sistema de notificaciones  
**Historia:**  
Como usuario autenticado, quiero ser notificado cuando ocurre algo relevante para mí dentro de la organización, para mantenerme informado sobre invitaciones a equipos o cambios en el estado de un torneo en el que participo.  

**Criterios de Aceptación**  
**PH:** 7  
1. Existe un lugar dentro de la interfaz donde el usuario pueda visualizar que tiene notificaciones no leídas  
2. Al hacer click, el usuario accede a un centro de notificaciones donde puede visualizar los detalles y marcar notificaciones como leídas  
3. Se generan notificaciones cuando un usuario es invitado a participar en un equipo  
4. Se generan notificaciones cuando el torneo en el que participa el usuario cambia de estado (por ejemplo, “iniciado” o “en curso”)  

---

## MÓDULO 7: Estadísticas

Este módulo ofrece herramientas para evaluar el rendimiento y la participación en los diferentes niveles del sistema.

---

### N.º 20 - Estadísticas de jugadores  
**Historia:**  
Como usuario de la organización, quiero visualizar mis estadísticas personales de participación o de otros usuarios, para conocer el rendimiento general dentro de los torneos  

**Criterios de Aceptación**  
**PH:** 5  
1. El sistema debe mostrar al usuario su número de torneos jugados, victorias, derrotas y posición final promedio  
2. Las estadísticas deben actualizarse automáticamente tras cada partida registrada  
3. Debe permitir ver estadísticas filtradas por organización y por tipo de actividad  

---

### N.º 21 - Estadísticas de plataforma
**Historia:**
Como administrador de la plataforma, quiero visualizar estadísticas generales de los diferentes contextos del sistema

**Criterios de Aceptación**  
**PH:** 6  
1. El sistema debe mostrar métricas sobre la cantidad de usuarios, organizaciones, torneos y equipos
2. Para cada uno de los elementos, debe mostrar la variación porcentual respecto del último mes
3. Debe presentar una gráfica para mostrar los nuevos usuarios respecto del último tiempo
4. Debe mostrar los torneos realizados para las actividades más populares???? ----------------------------sasdsadsdfsdffffffffffffffffffffffffffffffff

---

### N.º 22 - Estadísticas por torneos  
**Historia:**  
Como usuario de la organización, quiero consultar estadísticas específicas de un torneo, para evaluar la participación y el desempeño dentro del mismo  

**Criterios de Aceptación**  
**PH:** 3
1. Debe mostrar total de equipos participantes, cantidad de partidas disputadas, y victorias por equipo  
2. Debe listar el equipo campeón y subcampeón  

---

## MÓDULO 8: Interfaz y Experiencia de Usuario

Este módulo garantiza que la plataforma sea accesible y funcional en diversos dispositivos, incluyendo móviles y escritorio.

---

### N.º 23 - Interfaz Responsiva  
**Historia:**  
Como usuario, quiero acceder al sistema desde dispositivos móviles y escritorio, para poder utilizar la plataforma desde cualquier dispositivo  

**Criterios de Aceptación**  
**PH:** 4  
1. Todos los componentes de la interfaz deben adaptarse correctamente a diferentes tamaños de pantalla  
2. El sistema debe ser completamente funcional tanto en dispositivos móviles como en escritorio  

---

## MÓDULO 9: Gestión de partidas

Este módulo representa los encuentros individuales (partidas) que forman parte de los torneos. Permite a los árbitros registrar y modificar resultados, y a los usuarios de la organización visualizar los detalles de las partidas para seguir el desarrollo del torneo.

### N.º 24 - Visualización de partidas

**Historia:**  
Como usuario autenticado perteneciente a una organización, quiero visualizar el detalle de una partida dentro de un torneo, para conocer información pertinente a la misma, como el nombre del torneo, la fase del torneo, los equipos enfrentados, el resultado, el árbitro y el mejor jugador.

**Criterios de Aceptación**  
**PH:** 4  

1. Cualquier usuario que pertenezca a la organización donde se está llevando a cabo el torneo puede acceder a la visualización del detalle de una partida.  
2. Se muestra el nombre del torneo, fase del torneo (por ejemplo: cuartos de final, semifinal, final), nombres de los equipos involucrados y el árbitro designado.
   - Si la partida ya fue disputada, se muestra:
     - El resultado (formato: Equipo A - 1 | Equipo B - 2)
     - El mejor jugador designado
     - El equipo clasificado
     - El árbitro que registró el resultado
   - Si la partida aún no tiene resultado registrado:
     - Estado como "pendiente" u "en juego"
     - El campo de mejor jugador aparece en blanco

---

### N.º 25 - Registro de resultado de partida

**Historia:**  
Como árbitro asignado a un torneo, quiero poder registrar el resultado de una partida que me fue asignada y el mejor jugador de la misma, para que el sistema determine qué equipo avanza a la siguiente fase del torneo.

**Criterios de Aceptación**  
**PH:** 7

1. Solo el árbitro asignado al torneo puede ingresar al formulario de registro de resultados.  
2. El árbitro debe registrar el puntaje de cada equipo y seleccionar del mejor jugador (entre los participantes de la partida)
3. El sistema valida que los puntajes no estén vacíos, los puntajes sean numéricos y que el mejor jugador esté seleccionado (entre los jugadores participantes)
4. Una vez guardado el resultado el sistema determina automáticamente el equipo ganador y registra el mejor jugador designado
5. El equipo ganador es actualizado como clasificado a la siguiente fase del torneo (según el bracket).  
6. El resultado queda registrado en la base de datos y es visible para todos los usuarios de la organización.

---

### N.º 26 - Edición de resultado de partida

**Historia:**  
Como árbitro de un torneo, quiero poder editar el resultado de una partida, siempre que la siguiente llave del torneo no haya sido jugada aún, para corregir errores de ingreso sin afectar la integridad del torneo.

**Criterios de Aceptación**  
**PH:** 8  

1. Solo el árbitro asignado puede editar el resultado de una partida bajo su responsabilidad.  
2. La edición solo es permitida si:
   - El equipo que avanzó no ha jugado la siguiente partida
   - El torneo no ha finalizado
3. Interfaz de edición muestra los valores actuales (resultado y mejor jugador)
4. Valida los nuevos datos con los mismos criterios que el registro inicial
5. El nuevo resultado sustituye el anterior y actualiza el bracket automáticamente. Además, actualiza el mejor jugador si fue modificado

# Módulo 10: Gestión de Eventos

Este módulo permite agrupar torneos bajo eventos macro (ej: "Copa Mechona 2026") para organización jerárquica. Los organizadores pueden crear/editar eventos y asociar torneos, mientras los usuarios visualizan torneos agrupados.

## N.º 27 - Creación de eventos
**Historia**  
Como organizador quiero crear eventos en mi organización para agrupar torneos relacionados.

**Criterios de Aceptación**  
**PH: 5**  
1. Acceso desde dashboard de organizador con un rol válido (organizador)  
2. Formulario con campos obligatorios, como nombre (único en la organización) y fechas de inicio y fin y una descripción
3. Se debe validar que el nombre no repetido y que la fecha de fin sea posterior al inicio
4. Debe persistir en BD con estado "activo" por defecto
5. Confirmación visual con redirección a listado

## N.º 28 - Edición de eventos
**Historia**  
Como organizador quiero modificar eventos existentes para corregir datos o actualizar información.

**Criterios de Aceptación**  
**PH: 4**  
1. Edición permitida solo para organizadores de la misma organización
2. Debe permitir editar todos los campos
3. Debe validar que las fechas sean coherentes

## N.º 29 - Desactivación de eventos
**Historia**  
Como organizador quiero desactivar eventos obsoletos para mantener limpio el sistema sin perder datos históricos.

**Criterios de Aceptación**  
**PH: 3**  
1. Al desactivar un torneo, cambia su estado a "inactivo"
2. Al desactivar ya no es posible usar el evento en un torneo pero mantiene relación con torneos asociados anteriormente

## N.º 30 - Listado de eventos
**Historia**  
Como usuario quiero ver todos los eventos de mi organización para identificar rápidamente torneos asociados.

**Criterios de Aceptación**  
**PH: 4**  
1. Vista de listado de evento, incluyendo el nombre y ordenados por fecha
2. Se debe permitir seleccionar uno para revisar el detalle del mismo o editar en caso de organizadores

## N.º 31 - Asociación de torneos
**Historia**  
Como organizador quiero vincular torneos a eventos para agrupar competencias relacionadas.

**Criterios de Aceptación**  
**PH: 5**  
1. Al crear un torneo debe existir un selector en creación del torneo, el que solo muestra eventos activos de la misma organización
2. Solo se permite un evento por torneo

## N.º 32 - Vista de detalle
**Historia**  
Como usuario quiero explorar un evento específico para ver todos sus torneos asociados.

**Criterios de Aceptación**  
**PH: 6**  
1. Una vez ingresado al detalle del evento, muestra su detalle, como el nombre, la descripción y las fechas, además del listado de torneos asociados
2. Permite la busqueda de torneos
3. Permite ingresar a la vista de detalle de torneo si se presiona uno