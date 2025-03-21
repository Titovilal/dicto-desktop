# dicto-desktop

An Electron application with React and TypeScript

## Recommended IDE Setup

- [VSCode](https://code.visualstudio.com/) + [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) + [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)

## Project Setup

### Install

```bash
$ npm install
```

### Development

```bash
$ npm run dev
```

### Build

```bash
# For windows
$ npm run build:win

# For macOS
$ npm run build:mac

# For Linux
$ npm run build:linux
```

---

## TESTS

- Abrir la app y grabar con botón

- Abrir la app y grabar con shortcut

- CRUD perfil

- Cambiar de perfil

- Borrar perfil seleccionado

- Poner api key valida

Poner api key inválida

---

- crear electron store DONE

- establecer crud de perfiles DONE

- establecer selección de perfiles DONE

- establecer shortcut y cambio de shortcut DONE

- establecer botones para grabar y parar de grabar DONE

- grabar audio DONE

- api call para transcribir DONE

- api call para recibir info del usuario DONE

- poner sonidos de grabacion DONE

- hacer api call DONE

- que no se pueda apretar el boton de grabar mientras se este procesando DONE

- mirar lo de copiar al portapapeles automatico DONE

- mirar lo de hacer ctrl+v automatico DONE

- mejorar interfaz DONE

- manejar error de falta de creditos o api key no existe DONE

- mirar porque la primera ejecucion la tengo que hacer apretando el boton y no desde el shortcut, sino da error y dice que no hay profile DONE

- mejorar efectos de sonido DONE

- controlar volumen desde settings DONE

- poner modo siempre visible DONE

- crear icono de la app DONE

- crear modo compacto DONE

- poner opcion siempre visible DONE

- comprobar que funciona el transcription prompt bien DONE -> NO DE FORMA EXHAUSTIVA

- comprobar que funciona el temperature correctamente DONE -> NO DE FORMA EXHAUSTIVA

- mejorar explicaciones del profile form DONE

- simplificar visual de perfil en profile section DONE

- usar openrouter y permitir elegir diferentes modelos (haiku, 4o-mini) DONE

- Revisar system prompt DONE

- opción AUTO-ENTER DONE

- opción texto copiado como contexto adicional (y mirar prompt para que devuelva el texto ) DONE

- cobrar por tokens de output de ia DONE

- implementar parametro slected text en endpoint DONE

- comprobar system prompt y ai prompts para que funcione el selected text de forma correcta DONE

- crear funcionalidad reescribir con IA DONE

- boton de cancelar DONE

- popup para mostrar estado DONE

- icono de dicto web DONE

- solucionar problema de resizing con nuevo popup DONE

- mejorar la UX de la sidebar DONE

- seleccionar por defecto modelo de IA en settings DONE

- hacwer mas smooth los popups DONE

- cambiar entre perfiles con shortcut DONE

- Desplegar endpoint en railway para eliminar el 60 sec processing DONE

- regenerar api key cuando te registras no funciona DONE

- actualizador automatico DONE

---

- Comprobar que el auto update funciona correctamente

- Crear 3 o 4 perfiles por defecto distintos por defecto

- Crear un blog o página documentando el prompt engineering

- crear playground como excalidraw

- si estamos en el estado de grabando y de repente se pulsa el botón de cambiar selección pues se hace se muestra el de cambiar selección sólo durante dos segundos y se vuelve al de grabando pero qué pasa si en estos dos segundos viene un mensaje para cambiar el estado a done entonces ya no se tiene que pasar otra vez a recording sino se pasará a done

# Como crear releases:

publicar y luego ir a github releases y quitar de draft

# Como ver logs de la app

Get-Content -Path C:\Users\scast\AppData\Roaming\dicto-desktop\logs\main.log -Tail 10 -Wait
