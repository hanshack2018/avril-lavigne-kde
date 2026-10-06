#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Instalación por usuario, reversible, sin dependencias Python externas."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
THEME = 'Avril-Lavigne-Hanshack'
VERSION = '6.3.6'

def locations():
    home = Path.home()
    data = Path(os.environ.get('XDG_DATA_HOME') or home / '.local/share')
    state = Path(os.environ.get('XDG_STATE_HOME') or home / '.local/state')
    if not data.is_absolute() or not state.is_absolute():
        raise RuntimeError('Las rutas XDG deben ser absolutas.')
    # Qt stylesheets and Desktop Entry have separate escaping rules.
    if any(c in str(data) for c in '\n\r\t"\\%'):
        raise RuntimeError('La ruta XDG contiene caracteres no soportados por este instalador.')
    return data, state / 'avril-lavigne-kde'

def run(*args):
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout.strip()

def current_theme():
    return run('kreadconfig6', '--file', 'plasmarc', '--group', 'Theme',
               '--key', 'name', '--default', 'default')

def apply_theme(name):
    run('plasma-apply-desktoptheme', name)

def refresh():
    try:
        run('kbuildsycoca6')
    except (OSError, subprocess.CalledProcessError):
        print('Aviso: no se pudo actualizar el menú. Cerrá sesión y entrá de nuevo.')

def system_desktop():
    for base in os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':'):
        if base:
            p = Path(base) / 'applications/org.kde.dolphin.desktop'
            if p.is_file():
                return p
    raise RuntimeError('No se encontró el lanzador del sistema de Dolphin.')

def desktop_quote(text):
    value = ''.join('\\' + c if c in '\\"`$' else c for c in str(text))
    return '"' + value.replace('\\', '\\\\') + '"'

def make_desktop(original, qss):
    lines = []
    count = 0
    for line in original.splitlines():
        if line.startswith('DBusActivatable='):
            continue
        if line == '[Desktop Entry]':
            lines.extend([line, 'DBusActivatable=false'])
            continue
        if line.startswith('Exec='):
            match = re.fullmatch(r'Exec=(?:/usr/bin/)?dolphin(\s.*)?', line)
            if not match:
                raise RuntimeError('El lanzador de Dolphin tiene un Exec no compatible: ' + line)
            line = 'Exec=dolphin --stylesheet ' + desktop_quote(qss) + (match[1] or '')
            count += 1
        lines.append(line)
    if not count:
        raise RuntimeError('El lanzador de Dolphin no contiene Exec.')
    return '\n'.join(lines) + '\n'

def exists(path):
    return path.exists() or path.is_symlink()

def remove(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)

def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_symlink():
        dst.symlink_to(os.readlink(src))
    elif src.is_dir():
        shutil.copytree(src, dst, symlinks=True)
    else:
        shutil.copy2(src, dst)

def fingerprint(path):
    h = hashlib.sha256()
    def add(p, name):
        h.update(name.encode())
        if p.is_symlink():
            h.update(b'link' + os.readlink(p).encode())
        elif p.is_file():
            h.update(b'file' + p.read_bytes())
        elif p.is_dir():
            h.update(b'dir')
    add(path, '.')
    if path.is_dir() and not path.is_symlink():
        for p in sorted(path.rglob('*')):
            add(p, str(p.relative_to(path)))
    return h.hexdigest() if exists(path) else None

def save(state, info):
    tmp = state / 'estado.tmp'
    tmp.write_text(json.dumps(info, indent=2, ensure_ascii=False))
    tmp.replace(state / 'estado.json')

def preflight(style_only):
    for tool in ['plasmashell', 'plasma-apply-desktoptheme', 'kreadconfig6', 'kbuildsycoca6']:
        if not shutil.which(tool):
            raise RuntimeError('Falta el comando: ' + tool)
    version = run('plasmashell', '--version')
    if not re.search(r'\b6\.', version):
        raise RuntimeError('Se necesita KDE Plasma 6.')
    if not style_only:
        if not re.search(r'\b6\.3\.6\b', version):
            raise RuntimeError('El paquete completo requiere Plasma 6.3.6. '
                               'Usá --solo-estilo para instalar únicamente el estilo del panel.')
        if not shutil.which('dolphin'):
            raise RuntimeError('Falta Dolphin.')
    data, state = locations()
    if not (ROOT / 'assets/tema/metadata.json').is_file():
        raise RuntimeError('Extraé el paquete completo antes de ejecutarlo.')
    print('Detectado:', version)
    print('Estilo anterior:', current_theme())
    print('Destino:', data)
    if not style_only:
        make_desktop(system_desktop().read_text(), data / 'avril-lavigne-kde/dolphin.qss')
    return data, state

def targets(data, style_only):
    result = [('tema', data / 'plasma/desktoptheme' / THEME)]
    if not style_only:
        result += [('kickoff', data / 'plasma/plasmoids/org.kde.plasma.kickoff'),
                   ('recursos', data / 'avril-lavigne-kde'),
                   ('dolphin', data / 'applications/org.kde.dolphin.desktop')]
    return result

def restore(state, info, preserve_changes=False):
    if current_theme() == THEME:
        apply_theme(info['previous_theme'])
    recovery = state / ('cambios-posteriores-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    for entry in reversed(info['entries']):
        if not entry.get('touched'):
            continue
        dst = Path(entry['path'])
        backup = state / entry['backup']
        if entry['existed'] and not exists(backup):
            raise RuntimeError('Falta un respaldo. No se borrará: ' + str(dst))
        if preserve_changes and exists(dst) and fingerprint(dst) != entry.get('installed_hash'):
            copy(dst, recovery / entry['name'])
            print('Cambios posteriores conservados en:', recovery / entry['name'])
        remove(dst)
        if entry['existed']:
            copy(backup, dst)
        entry['touched'] = False
        save(state, info)
    info['status'] = 'restored'
    save(state, info)
    refresh()

def install(style_only=False):
    data, state = preflight(style_only)
    manifest = state / 'estado.json'
    if manifest.exists():
        old = json.loads(manifest.read_text())
        if old.get('status') != 'restored':
            raise RuntimeError('Ya hay una instalación o recuperación pendiente. Ejecutá desinstalar.sh primero.')
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    info = {'version': '0.1.0', 'previous_theme': current_theme(),
            'status': 'preparing', 'entries': []}
    if info['previous_theme'] == THEME:
        raise RuntimeError('Seleccioná otro estilo antes de instalar para poder restaurarlo después.')
    # Complete every backup before modifying any destination.
    for name, dst in targets(data, style_only):
        entry = {'name': name, 'path': str(dst), 'existed': exists(dst),
                 'backup': f'respaldos/{stamp}/{name}', 'touched': False}
        if entry['existed']:
            copy(dst, state / entry['backup'])
        info['entries'].append(entry)
    save(state, info)
    try:
        for entry in info['entries']:
            dst = Path(entry['path'])
            entry['touched'] = True
            save(state, info)
            remove(dst)
            name = entry['name']
            if name in ('tema', 'kickoff'):
                copy(ROOT / 'assets' / name, dst)
            elif name == 'recursos':
                dst.mkdir(parents=True)
                copy(ROOT / 'assets/lugares.jpg', dst / 'lugares.jpg')
                menu = data / 'plasma/plasmoids/org.kde.plasma.kickoff/contents/images/menu-foto.png'
                qss = (ROOT / 'assets/dolphin.qss.in').read_text()
                qss = qss.replace('@MENU@', str(menu)).replace('@LUGARES@', str(dst / 'lugares.jpg'))
                (dst / 'dolphin.qss').write_text(qss)
            elif name == 'dolphin':
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(make_desktop(system_desktop().read_text(), data / 'avril-lavigne-kde/dolphin.qss'))
            entry['installed_hash'] = fingerprint(dst)
            save(state, info)
        apply_theme(THEME)
        info['status'] = 'installed'
        save(state, info)
        refresh()
    except (Exception, KeyboardInterrupt):
        print('La instalación falló; intentando restaurar los archivos anteriores.')
        restore(state, info)
        raise
    print('Instalación terminada. Cerrá Dolphin, cerrá sesión y entrá de nuevo.')
    print('Copias de seguridad:', state / 'respaldos' / stamp)

def uninstall():
    _, state = locations()
    manifest = state / 'estado.json'
    if not manifest.exists():
        print('No hay una instalación registrada.')
        return
    info = json.loads(manifest.read_text())
    if info.get('status') == 'restored':
        print('La configuración anterior ya fue restaurada.')
        return
    restore(state, info, preserve_changes=True)
    print('Restauración terminada. Cerrá sesión y entrá de nuevo.')

def main():
    parser = argparse.ArgumentParser(description='Avril Lavigne KDE — by Hanshack')
    parser.add_argument('accion', choices=['instalar', 'desinstalar', 'comprobar'])
    parser.add_argument('--solo-estilo', action='store_true', help='Instalar solo el estilo Plasma; omitir menú y Dolphin')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Ejecutá esto como tu usuario habitual, sin sudo.')
    try:
        if args.accion == 'comprobar':
            preflight(args.solo_estilo)
            print('Comprobación completada. No se modificó la configuración.')
            return
        _, state = locations()
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (state / 'operacion.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if args.accion == 'instalar':
                install(args.solo_estilo)
            else:
                uninstall()
    except (Exception, KeyboardInterrupt) as exc:
        print('ERROR:', str(exc) or 'Operación interrumpida', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
