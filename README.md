# Avril Lavigne KDE — by Hanshack

Versión 0.1.0 · Paquete de personalización para KDE Plasma.

Conserva las imágenes proporcionadas por Hanshack: barra con los discos de
Avril Lavigne, menú con foto y Dolphin con dos fondos distintos. La base del
estilo es Sweet, de EliverLara. Es un proyecto de fans, sin afiliación oficial.

## Instalación

Extraé el ZIP completo. Abrí una terminal dentro de la carpeta extraída y ejecutá:

```bash
bash instalar.sh
```

No uses sudo. Requiere Python 3, KDE Plasma **6.3.6**, Dolphin y los comandos
`plasma-apply-desktoptheme`, `kreadconfig6` y `kbuildsycoca6`.
El menú incluido procede de Debian 13 con Plasma 6.3.6. La versión completa
rechaza otras versiones para no sustituir su menú con código incompatible.

Para revisar los requisitos sin modificar la configuración:

```bash
python3 gestor.py comprobar
```

En otra versión de Plasma 6 podés probar únicamente el estilo y la barra:

```bash
bash instalar.sh --solo-estilo
```

Ese modo no instala ni modifica el menú ni Dolphin; no se ha probado visualmente
en otras versiones de Plasma. El paquete no instala programas ni descarga archivos.

Al terminar, cerrá todas las ventanas de Dolphin, cerrá sesión y entrá de nuevo.
Abrí Dolphin desde el menú de aplicaciones. Si un acceso anclado conserva el
aspecto anterior, quitá ese acceso y volvé a anclar Dolphin desde el menú.
Una ejecución directa de `dolphin` desde terminal no recibe el estilo del lanzador.

## La H verde

La imagen original está incluida. Para elegirla, hacé clic derecho en el menú de
aplicaciones → Configurar lanzador → icono → elegir imagen. Seleccioná:

`~/.local/share/plasma/plasmoids/org.kde.plasma.kickoff/contents/images/hanshack-menu.png`

Si usás XDG_DATA_HOME personalizado, reemplazá `~/.local/share` por esa ruta.
El instalador conserva tu selección actual de icono y la disposición del panel.
Los cambios manuales de icono se revierten desde esa misma opción.

## Desinstalar y recuperar

Desde la misma carpeta:

```bash
bash desinstalar.sh
```

Restaura los archivos que existían antes de instalar y elimina únicamente los
destinos añadidos por este paquete. Si el estilo activo sigue siendo el de Avril,
reactiva el estilo anterior. Si elegiste otro estilo después, lo conserva.

Los respaldos permanecen en `~/.local/state/avril-lavigne-kde/respaldos/` (o bajo
XDG_STATE_HOME). Si modificaste archivos instalados, la desinstalación guarda
esos cambios en `cambios-posteriores-*` antes de restaurar. No borres el directorio
de estado mientras el tema esté instalado. Guardá también este paquete para
poder ejecutar el desinstalador.

El instalador intenta restaurar automáticamente si una operación falla.
Después de un corte de energía o interrupción forzada, ejecutá el desinstalador
para recuperar la configuración antes de volver a instalar.

## Alcance y compatibilidad

- Instala el estilo Plasma en un directorio propio: `Avril-Lavigne-Hanshack`.
- Respalda y reemplaza la copia local de `org.kde.plasma.kickoff`.
- Adapta las rutas del QSS y el lanzador local de Dolphin a la cuenta actual.
- No cambia el fondo del escritorio, fuentes, decoración de ventanas, SDDM,
  atajos, favoritos ni disposición de paneles. Esas preferencias pueden hacer
  que otro equipo se vea diferente al de Hanshack.
- La foto de la barra se estira al tamaño del panel, como en el diseño original.
- Antes de actualizar Plasma, desinstalá este paquete: la copia local del menú
  puede ocultar el menú nuevo de la distribución.
- No es un paquete de tema global instalable directamente desde KDE Store.
  Es un ZIP con instalador por usuario y código fuente legible.

## Validación

Se verificó la instalación, restauración y recuperación de fallos en directorios
temporales con comandos KDE simulados. No se ejecutó una sesión gráfica de KDE
en el entorno de construcción. El aspecto visual debe comprobarse en el equipo
de Hanshack antes de anunciar esta versión como probada para terceros.

## Créditos y distribución

Consultá `CREDITOS.md` y `LICENCIAS/`. Las fotos se incluyen tal como fueron
aportadas para este proyecto; no se ha verificado su licencia de redistribución.
Este paquete no atribuye a Hanshack la autoría de las fotografías ni las publica
automáticamente en ningún sitio. Revisá sus permisos antes de subir el paquete.

Fuentes técnicas:
- https://develop.kde.org/docs/plasma/theme/theme-details/
- https://develop.kde.org/docs/plasma/theme/theme-elements/
- https://specifications.freedesktop.org/desktop-entry/latest-single/
