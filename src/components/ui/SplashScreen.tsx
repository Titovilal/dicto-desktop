export default function SplashScreen() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white">
      <div className="space-y-6 text-center">
        <h1 className="text-4xl font-bold tracking-tight">Dicto Desktop</h1>
        <div className="flex justify-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
        <p className="text-sm text-gray-400">Loading...</p>
      </div>
    </div>
  )
}
