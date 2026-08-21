import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Upload } from 'lucide-react'
import api from '../lib/api'

export default function Runs() {
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [newRunId, setNewRunId] = useState('')
  const [newName, setNewName] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: () => api.get('/runs').then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (body: { run_id: string; name: string }) => api.post('/runs', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      setShowCreate(false)
      setNewRunId('')
      setNewName('')
    },
  })

  const runs = data?.runs || []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Performance Runs</h1>
          <p className="text-slate-500 mt-1">Manage test runs and upload reports</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          <Plus size={18} /> New Run
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
          <h3 className="font-bold text-slate-900 mb-4">Create New Run</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              value={newRunId}
              onChange={(e) => setNewRunId(e.target.value)}
              placeholder="Run ID (e.g. RUN-2026-001)"
              className="px-4 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Name (optional)"
              className="px-4 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => createMutation.mutate({ run_id: newRunId, name: newName || newRunId })}
              disabled={!newRunId}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50"
            >
              Create
            </button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-slate-600">Cancel</button>
          </div>
        </div>
      )}

      {isLoading ? (
        <p className="text-slate-500">Loading...</p>
      ) : runs.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-slate-200">
          <Upload className="mx-auto text-slate-400 mb-4" size={48} />
          <p className="text-slate-600 font-medium">No runs yet. Create one to get started.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Run ID</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Data</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Created</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run: any) => (
                <tr key={run.run_id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link to={`/runs/${run.run_id}`} className="text-blue-600 font-medium hover:underline">{run.run_id}</Link>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{run.name}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                      run.status === 'completed' ? 'bg-green-100 text-green-700' :
                      run.status === 'failed' ? 'bg-red-100 text-red-700' :
                      'bg-slate-100 text-slate-600'
                    }`}>{run.status}</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {run.loadrunner_uploaded && <span className="mr-2">LR</span>}
                    {run.appdynamics_uploaded && <span>AppD</span>}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-500">{new Date(run.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
