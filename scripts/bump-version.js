const fs = require('fs')
const path = require('path')

// Tipos de incremento de versión
const BUMP_TYPES = {
  PATCH: 'patch',
  MINOR: 'minor',
  MAJOR: 'major'
}

// Obtener el tipo de incremento desde los argumentos de línea de comandos
// Por defecto, incrementa la versión patch
const bumpType = process.argv[2] || BUMP_TYPES.PATCH

// Ruta al package.json
const packageJsonPath = path.join(__dirname, '..', 'package.json')

// Leer el archivo package.json
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'))
const currentVersion = packageJson.version

// Dividir la versión en sus componentes
const [major, minor, patch] = currentVersion.split('.').map(Number)

// Calcular la nueva versión según el tipo de incremento
let newVersion
switch (bumpType) {
  case BUMP_TYPES.MAJOR:
    newVersion = `${major + 1}.0.0`
    break
  case BUMP_TYPES.MINOR:
    newVersion = `${major}.${minor + 1}.0`
    break
  case BUMP_TYPES.PATCH:
  default:
    newVersion = `${major}.${minor}.${patch + 1}`
    break
}

// Actualizar la versión en el objeto package.json
packageJson.version = newVersion

// Escribir el archivo package.json actualizado
fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2) + '\n')

console.log(`Versión actualizada: ${currentVersion} -> ${newVersion}`)
