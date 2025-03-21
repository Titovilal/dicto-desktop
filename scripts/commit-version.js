const { execSync } = require('child_process')
const packageJson = require('../package.json')

try {
  // Añadir package.json al staging
  execSync('git add package.json')

  // Hacer commit con el mensaje que incluye la versión
  const commitMessage = `chore: bump version to v${packageJson.version}`
  execSync(`git commit -m "${commitMessage}"`)

  // Push al repositorio
  execSync('git push')

  console.log(`Commit y push realizados con éxito: ${commitMessage}`)
} catch (error) {
  console.error('Error al realizar commit y push:', error.message)
  process.exit(1)
}
