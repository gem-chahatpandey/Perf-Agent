import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, PlayCircle, MessageSquare, LogOut } from 'lucide-react'

interface Props {
  children: ReactNode
  onLogout: () => void
}

export default function Layout({ children, onLogout }: Props) {
  const location = useLocation()

  const nav = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/runs', label: 'Runs', icon: PlayCircle },
    { path: '/chat', label: 'AI Chat', icon: MessageSquare },
  ]

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-64 bg-slate-900 text-slate-200 p-4 flex flex-col">
        <div className="mb-8">
          <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-xs mb-2">
            AIP
          </div>
          <h1 className="text-sm font-bold text-white">AI Performance Platform</h1>
          <p className="text-xs text-slate-400">Performance Analysis POC</p>
        </div>

        <nav className="flex-1 space-y-1">
          {nav.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === item.path
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <item.icon size={18} />
              {item.label}
            </Link>
          ))}
        </nav>

        <button
          onClick={onLogout}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <LogOut size={18} />
          Logout
        </button>
      </aside>

      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  )
}
