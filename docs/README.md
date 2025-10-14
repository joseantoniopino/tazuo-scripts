# 📚 Documentación TazUO API - Guía de Uso

Esta carpeta contiene la documentación completa de la API de scripting de TazUO para Ultima Online.

---

## 🗂️ Estructura de la Documentación

### 📘 API.md - Documentación Principal
**Tamaño:** ~3300 líneas  
**Propósito:** Documentación completa del namespace `API.*`

**Contiene:**
- **Propiedades globales:** `API.Player`, `API.Backpack`, `API.Bank`, `API.JournalEntries`
- **Métodos principales:** `API.Msg()`, `API.Pause()`, `API.FindType()`, `API.UseObject()`, etc.
- **Funciones de juego:** Movimiento, targeting, búsqueda de items/mobiles, gumps, etc.

**Cuándo usarlo:**
- Cuando necesites métodos generales (pausas, mensajes, búsqueda)
- Para funciones de juego básicas (usar items, targetear, mover)
- Como referencia principal para empezar un script

**Ejemplo:**
```python
API.Msg("Hola mundo")  # Enviar mensaje
API.Pause(1.0)         # Pausar 1 segundo
item = API.FindType(0x0F3F)  # Buscar item por graphic ID
```

---

## 🎭 Clases de Entidades (Py*)

Estas clases representan objetos del juego que heredan de `PyEntity` (entidad base con posición, serial, nombre).

### 👤 PyMobile.md - Mobiles (NPCs, Jugadores, Criaturas)
**Propósito:** Propiedades y métodos de personajes/NPCs

**Contiene:**
- **Estadísticas:** `Hits`, `Mana`, `Stamina` (y sus versiones `Max` y `Diff`)
- **Estados:** `IsDead`, `IsPoisoned`, `IsParalyzed`, `IsYellowHits`
- **Flags:** `IsAttackable`, `IsHuman`, `Notoriety`
- **Posición:** Heredado de `PyEntity` (X, Y, Z, Serial, Name)

**Cuándo usarlo:**
- Cuando trabajas con enemigos, NPCs, o el jugador mismo
- Para verificar salud, estados de buff/debuff
- Para calcular distancias o seleccionar targets

**Ejemplo:**
```python
mobile = API.Player
if mobile.IsPoisoned:
    API.Msg("¡Estás envenenado!")
```

---

### 🎒 PyItem.md - Items y Objetos
**Propósito:** Propiedades de items (en suelo, backpack, equipados)

**Contiene:**
- **Propiedades:** `Amount`, `Hue`, `ItemID`, `Container`
- **Ubicación:** `IsInBackpack`, `IsEquipped`, `OnGround`
- **Información:** `Name`, `Serial`, `Graphic`
- **Posición:** Heredado de `PyEntity`

**Cuándo usarlo:**
- Cuando buscas o manipulas items
- Para filtrar items por color, cantidad, ubicación
- Para detectar items específicos en backpack o suelo

**Ejemplo:**
```python
item = API.FindType(0x099B)  # Buscar botella
if item and item.Amount > 1:
    API.UseObject(item.Serial)
```

---

### 🌍 PyEntity.md - Entidad Base
**Propósito:** Clase base para todos los objetos con posición en el mundo

**Contiene:**
- **Identificación:** `Serial`, `Name`, `Graphic`
- **Posición:** `X`, `Y`, `Z`, `Map`
- **Utilidades:** `DistanceTo()`, `IsValid()`

**Cuándo usarlo:**
- Raramente directamente (es la clase base)
- Para entender qué propiedades heredan Mobile/Item/etc.

---

### 🎮 PyGameObject.md - Objeto de Juego
**Propósito:** Representación genérica de objetos del juego

**Contiene:**
- Propiedades base compartidas por todos los objetos
- Similar a `PyEntity` pero más general

**Cuándo usarlo:**
- Cuando trabajas con objetos que no son Mobile ni Item
- Para objetos genéricos del mundo

---

### 📜 PyJournalEntry.md - Entradas del Journal
**Propósito:** Mensajes del journal/chat del juego

**Contiene:**
- **Contenido:** `Text`, `Speaker`, `SpeechType`
- **Metadata:** `Timestamp`, `Serial`
- **Tipo:** System message, speech, etc.

**Cuándo usarlo:**
- Para detectar mensajes específicos del juego
- Para triggers basados en texto (ej: "You have been poisoned!")
- Para chat automation

**Ejemplo:**
```python
for entry in API.JournalEntries:
    if "you are dead" in entry.Text.lower():
        API.Msg("¡He muerto!")
```

---

### 🗺️ PyLand.md - Tiles de Terreno
**Propósito:** Información de tiles del mapa (suelo, terreno)

**Contiene:**
- **Tipo de tile:** `LandID`, `LandName`
- **Propiedades:** `IsImpassable`, `IsWet`
- **Posición:** X, Y, Z

**Cuándo usarlo:**
- Para pathfinding avanzado
- Para detectar tipo de terreno (agua, montaña, etc.)
- Scripts de navegación

---

### 🏛️ PyStatic.md - Objetos Estáticos del Mapa
**Propósito:** Objetos fijos del mapa (árboles, edificios, decoración)

**Contiene:**
- **Identificación:** `StaticID`, `Hue`
- **Propiedades:** `IsImpassable`, `IsSurface`
- **Posición:** X, Y, Z

**Cuándo usarlo:**
- Para detectar obstáculos en el mapa
- Para interactuar con objetos fijos (puertas, cofres fijos)
- Pathfinding complejo

---

### 🏠 PyMulti.md - Multis (Casas, Barcos)
**Propósito:** Estructuras grandes (houses, boats)

**Contiene:**
- **Identificación:** `MultiID`, `Serial`
- **Componentes:** Lista de tiles que forman el multi
- **Posición:** Base position del multi

**Cuándo usarlo:**
- Scripts de navegación en barcos
- Detección de casas
- Interacción con estructuras grandes

---

### 👥 PyProfile.md - Perfiles de Usuario
**Propósito:** Información de perfil de personajes

**Contiene:**
- Datos de perfil del jugador/NPC
- Información adicional de personaje

**Cuándo usarlo:**
- Raramente necesario en scripts normales
- Para obtener info extendida de personajes

---

## 🖼️ Sistema de Gumps/UI

### 🎨 PyControl.md - Controles Base
**Propósito:** Clase base para todos los controles de UI

**Contiene:**
- **Métodos de posición:** `SetPos()`, `SetRect()`, `GetX()`, `GetY()`
- **Métodos de tamaño:** `SetWidth()`, `SetHeight()`
- **Gestión:** `Add()`, `Remove()`, `Dispose()`

**Cuándo usarlo:**
- Como referencia para métodos comunes de todos los controles
- Al crear custom gumps

---

### 🔧 PyBaseControl.md - Control Base Abstracto
**Propósito:** Clase abstracta base para controles

**Contiene:**
- Implementación base de controles
- Propiedades heredadas por todos los controles

**Cuándo usarlo:**
- Raramente directamente (es abstracto)
- Para entender jerarquía de controles

---

### 📋 PyControlDropDown.md - Menús Desplegables
**Propósito:** Controles de dropdown/combobox

**Contiene:**
- **Métodos:** `AddItem()`, `GetSelectedItem()`, `SetSelectedIndex()`
- **Propiedades:** Items, SelectedIndex

**Cuándo usarlo:**
- Para crear menús de selección en gumps custom
- Para dropdowns en interfaces de usuario

---

### 🖼️ PyNineSliceGump.md - Gumps con Nine-Slice
**Propósito:** Sistema de gumps escalables (nine-slice rendering)

**Contiene:**
- **Constructor:** Crear gumps con bordes escalables
- **Configuración:** Textures, tamaños, bordes

**Cuándo usarlo:**
- Para crear ventanas/gumps custom con bordes elegantes
- Cuando necesitas UI escalable

---

### 🎯 ModernNineSliceGump.md - Nine-Slice Moderno
**Propósito:** Versión moderna del sistema nine-slice

**Contiene:**
- Implementación mejorada de nine-slice
- Estilos modernos

**Cuándo usarlo:**
- Igual que `PyNineSliceGump` pero con estilos modernos
- Para UIs más actuales

---

## 🎪 Otros Sistemas

### ⚡ Events.md - Sistema de Eventos
**Propósito:** Callbacks y event handlers

**Contiene:**
- **Eventos disponibles:** `OnPlayerHitsChanged`, `OnItemAdded`, etc.
- **Suscripción:** Cómo registrar callbacks
- **Ejemplos:** Uso de eventos en scripts

**Cuándo usarlo:**
- Para scripts reactivos (responder a eventos del juego)
- Cuando necesitas detectar cambios en tiempo real
- Para automation basada en triggers

**Ejemplo:**
```python
def on_hits_changed(new_hits):
    API.Msg(f"Vida: {new_hits}")

API.Events.OnPlayerHitsChanged(on_hits_changed)

while not API.StopRequested:
    API.ProcessCallbacks()
    API.Pause(0.25)
```

---

### 💪 Buff.md - Sistema de Buffs
**Propósito:** Buffs/debuffs del jugador

**Contiene:**
- **Propiedades:** `Graphic`, `Text`, `Timer`, `Type`, `Title`
- **Tipos:** Enum de tipos de buff

**Cuándo usarlo:**
- Para detectar buffs activos en el jugador
- Para verificar duración de buffs
- Scripts que dependen de estados temporales

**Ejemplo:**
```python
buffs = API.Player.GetBuffs()
for buff in buffs:
    if "poison" in buff.Title.lower():
        API.Msg("¡Tienes veneno activo!")
```

---

### 📝 notes.md - Notas y Trucos Adicionales
**Propósito:** Información extra no documentada automáticamente

**Contiene:**
- **Trucos de gumps:** Métodos helper (`CenterXInViewPort()`, etc.)
- **Convenciones:** Archivos con `_` al inicio no se muestran in-game
- **Tips de Mobiles:** Propiedades calculadas (`Diff` = Max - Current)
- **Ejemplos prácticos**

**Cuándo usarlo:**
- Cuando la documentación automática no es suficiente
- Para trucos y tips específicos de TazUO
- Para entender convenciones del sistema

---

## 🚀 Guía Rápida de Uso

### Para empezar un script nuevo:
1. **Lee `API.md`** - Métodos principales
2. **Consulta `PyMobile.md` o `PyItem.md`** según necesites
3. **Revisa `notes.md`** para trucos y tips

### Para trabajar con UI:
1. **Lee `PyControl.md`** - Métodos base
2. **Consulta `PyNineSliceGump.md`** - Para gumps custom
3. **Revisa `notes.md`** - Trucos de gumps

### Para eventos/callbacks:
1. **Lee `Events.md`** - Sistema de eventos
2. **Consulta ejemplos** en la documentación

---

## 🔍 Por Qué Están Separados

La documentación está dividida por **tipo de objeto/funcionalidad** para:

1. **Organización:** Fácil encontrar lo que necesitas sin buscar en 3300 líneas
2. **Herencia:** Cada clase tiene su archivo (Mobile, Item, Entity tienen propiedades diferentes)
3. **Modularidad:** Consultas solo lo que necesitas en cada momento
4. **Mantenimiento:** Updates de TazUO solo afectan archivos específicos
5. **Claridad:** Separar Mobile de Item de Gumps hace todo más comprensible

---

## 📌 Resumen Rápido

| Archivo | Cuándo Usarlo |
|---------|---------------|
| **API.md** | Métodos globales, funciones principales |
| **PyMobile.md** | Trabajar con NPCs, enemigos, jugador |
| **PyItem.md** | Buscar, usar, manipular items |
| **PyEntity.md** | Referencia de propiedades base |
| **PyControl.md** | Crear/modificar controles de UI |
| **Events.md** | Scripts reactivos con callbacks |
| **Buff.md** | Detectar buffs/debuffs activos |
| **notes.md** | Trucos, tips, convenciones |

---

**Última actualización:** Octubre 12, 2025  
**Versión de TazUO:** Compatible con API generada el 10/5/25
