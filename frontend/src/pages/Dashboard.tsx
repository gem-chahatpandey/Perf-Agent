import { useQuery } from '@tanstack/react-query'
import { Activity, AlertTriangle, CheckCircle, Zap } from 'lucide-react'
import api from '../lib/api'

export default function Dashboard() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get('/health').then((r) => r.data),
  })

  const { data: runsData } = useQuery({
    queryKey: ['runs'],
    queryFn: () => api.get('/runs').then((r) => r.data),
  })

  const runs = runsData?.runs || []
  const completedRuns = runs.filter((r: any) => r.analysis_completed)
  const failedRuns = runs.filter((r: any) => r.status === 'failed')

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">AI Performance Analysis Platform Overview</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard
          icon={<Activity className="text-blue-600" size={20} />}
          label="Total Runs"
          value={runs.length}
        />
        <MetricCard
          icon={<CheckCircle className="text-green-600" size={20} />}
          label="Analyzed"
          value={completedRuns.length}
        />
        <MetricCard
          icon={<AlertTriangle className="text-orange-600" size={20} />}
          label="Failed"
          value={failedRuns.length}
        />
        <MetricCard
          icon={<Zap className="text-purple-600" size={20} />}
          label="AI Status"
          value={health?.gemini === 'configured' ? 'Active' : 'Off'}
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-bold text-slate-900 mb-4">System Health</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <HealthItem label="Filesystem" status={health?.filesystem} />
          <HealthItem label="ChromaDB" status={health?.chroma} />
          <HealthItem label="Gemini AI" status={health?.gemini} />
          <HealthItem label="GitHub" status={health?.github} />
        </div>
      </div>

      {runs.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 mt-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4">Recent Runs</h2>
          <div className="space-y-2">
            {runs.slice(0, 5).map((run: any) => (
              <div key={run.run_id} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                <div>
                  <span className="font-medium text-slate-900">{run.run_id}</span>
                  <span className="ml-2 text-sm text-slate-500">{run.name}</span>
                </div>
                <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                  run.status === 'completed' ? 'bg-green-100 text-green-700' :
                  run.status === 'failed' ? 'bg-red-100 text-red-700' :
                  'bg-slate-100 text-slate-600'
                }`}>
                  {run.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function MetricCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: any }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center gap-3 mb-2">{icon}<span className="text-xs font-semibold text-slate-500 uppercase">{label}</span></div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
    </div>
  )
}

function HealthItem({ label, status }: { label: string; status?: string }) {
  const ok = status === 'healthy' || status === 'configured'
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2.5 h-2.5 rounded-full ${ok ? 'bg-green-500' : 'bg-orange-400'}`} />
      <span className="text-sm text-slate-700">{label}</span>
    </div>
  )
}
