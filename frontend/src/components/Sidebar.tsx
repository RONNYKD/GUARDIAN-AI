import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Shield, 
  Zap,
  Target
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Demo Mode', href: '/demo', icon: Target },
  { name: 'Threats', href: '/threats', icon: Shield },
]

export default function Sidebar() {
  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
      <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-800 bg-gray-900 px-6 pb-4">
        {/* Logo Area */}
        <div className="flex h-16 shrink-0 items-center gap-3 bg-gray-950/50 -mx-6 px-6">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/50">
            <Zap className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
            GuardianAI
          </span>
        </div>
        
        {/* Navigation */}
        <nav className="flex flex-1 flex-col">
          <ul role="list" className="flex flex-1 flex-col gap-y-2">
            <li>
              <ul role="list" className="space-y-2">
                {navigation.map((item) => (
                  <li key={item.name}>
                    <NavLink
                      to={item.href}
                      className={({ isActive }) =>
                        isActive
                          ? 'bg-blue-600/20 text-blue-400 border-l-4 border-blue-500 group flex gap-x-3 rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200'
                          : 'text-gray-300 hover:text-white hover:bg-gray-800 border-l-4 border-transparent group flex gap-x-3 rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200'
                      }
                    >
                      <item.icon className="h-5 w-5 shrink-0 transition-transform group-hover:scale-110" aria-hidden="true" />
                      {item.name}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  )
}
