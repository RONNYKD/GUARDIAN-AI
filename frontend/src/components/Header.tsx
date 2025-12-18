import { Moon, Sun, Menu, Wifi, WifiOff } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { useWebSocket } from '@/contexts/WebSocketContext'

export default function Header() {
  const { theme, toggleTheme } = useTheme()
  const { isConnected } = useWebSocket()

  return (
    <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
      <button type="button" className="-m-2.5 p-2.5 text-gray-700 dark:text-gray-400 lg:hidden">
        <span className="sr-only">Open sidebar</span>
        <Menu className="h-6 w-6" aria-hidden="true" />
      </button>

      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6 justify-end items-center">
        {/* Connection Status */}
        <div className="flex items-center gap-2">
          {isConnected ? (
            <>
              <Wifi className="h-4 w-4 text-success-500" />
              <span className="text-xs text-gray-600 dark:text-gray-400">Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-gray-400" />
              <span className="text-xs text-gray-600 dark:text-gray-400">Disconnected</span>
            </>
          )}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'light' ? (
            <Moon className="h-5 w-5 text-gray-700 dark:text-gray-400" />
          ) : (
            <Sun className="h-5 w-5 text-gray-700 dark:text-gray-400" />
          )}
        </button>
      </div>
    </header>
  )
}
