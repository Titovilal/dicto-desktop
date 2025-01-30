# dicto-desktop

An Electron application with Vue

## Recommended IDE Setup

- [VSCode](https://code.visualstudio.com/) + [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) + [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar)

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

TODO:
- [ ] Mover whisper a module en backend
- [ ] Hacer que cuando se reescriba o se modifique el nombre de un perfil y es el perfil seleccionado, que se modifique el perfil seleccionado porque si no se buguea.

- [x] Hacer que se vea bien lo que esta pasando
- [x] Crear modo compacto con solo indicadores visuales de lo que está pasando
- [x] Añadir forma de ir hacía atras en settings o profiles.
- [x] Añadir configuración de idioma
- [x] Refactorizar creando hook para audio, otro para whisper y otro para play sound
- [x] Añadir sonido de terminado
- [x] Añadir reescritura con ChatGPT o DeepSeek
- [x] Añadir perfiles de prompt para reescritura
- [ ] A la hora de hacer autenticacion, generar un token y que se tenga que poner en la aplicación
- [x] Añadir configuración de que se hace cuando llega el resultado (e.g. poner en portapapeles)
- [ ] Crear nextjs app para el frontend con DB Neon y generación de API Keys
