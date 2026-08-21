import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, Play, FileText, Brain } from 'lucide-react'
import api from '../lib/api'

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const queryClient = useQueryClient()
  const [loadrunnerFile, setLoadrunnerFile] = useState<File | null>(null)
  const [appdynamicsFile, setAppdynamicsFile] = useState<File | null>(null)

  const { data: run } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => api.get(`/runs/${runId}`).then((r) => r.data),
  })

  const { data: analysis } = useQuery({
    queryKey: ['analysis', runId],
    queryFn: () => api.get(`/runs/${runId}/analysis`).then((r) => r.data),
    enabled: !!run?.analysis_completed,
  })

  const { data: rca } = useQuery({
    queryKey: ['rca', runId],
    queryFn: () => api.get(`/runs/${runId}/rca`).then((r) => r.data),
    enabled: !!run?.rca_completed,
  })

  const { data: metrics } = useQuery({
    queryKey: ['metrics', runId],
    queryFn: () => api.get(`/runs/${runId}/metrics`).then((r) => r.data),
    enabled: !!run?.analysis_completed,
  })

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['run', runId] })
    queryClient.invalidateQueries({ queryKey: ['analysis', runId] })
    queryClient.invalidateQueries({ queryKey: ['rca', runId] })
    queryClient.invalidateQueries({ queryKey: ['metrics', runId] })
  }

  const analyzeMutation = useMutation({
    mutationFn: () => api.post(`/runs/${runId}/analyze`),
    onSuccess: invalidateAll,
  })

  const rcaMutation = useMutation({
    mutationFn: () => api.post(`/runs/${runId}/rca`),
    onSuccess: invalidateAll,
  })

  const singleUploadMutation = useMutation({
    mutationFn: async ({ file, source }: { file: File; source: 'loadrunner' | 'appdynamics' }) => {
      const formData = new FormData()
      formData.append('file', file)
      await api.post(`/runs/${runId}/upload/${source}`, formData)
    },
    onSuccess: (_data, variables) => {
      if (variables.source === 'loadrunner') setLoadrunnerFile(null)
      else setAppdynamicsFile(null)
      invalidateAll()
    },
  })

  const selectReport = (event: React.ChangeEvent<HTMLInputElement>, source: 'loadrunner' | 'appdynamics') => {
    const file = event.target.files?.[0]
    if (!file) return

    if (source === 'loadrunner') setLoadrunnerFile(file)
    else setAppdynamicsFile(file)
    singleUploadMutation.mutate({ file, source })
    event.target.value = ''
  }

  if (!run) return <p className="text-slate-500">Loading...</p>

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900">{run.run_id}</h1>
        <p className="text-slate-500">{run.name} &middot; {run.status}</p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2"><Upload size={20} /> Upload Reports</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-slate-700">LoadRunner
            <input type="file" onChange={(event) => selectReport(event, 'loadrunner')} accept=".csv,.json,.xml,.txt,.html,.log" disabled={singleUploadMutation.isPending} className="block mt-1 text-sm disabled:opacity-50" />
            </label>
            <p className="mt-2 text-xs text-slate-500">{loadrunnerFile?.name || 'Select a report to upload and parse it.'}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">AppDynamics
            <input type="file" onChange={(event) => selectReport(event, 'appdynamics')} accept=".csv,.json,.xml,.txt,.log" disabled={singleUploadMutation.isPending} className="block mt-1 text-sm disabled:opacity-50" />
            </label>
            <p className="mt-2 text-xs text-slate-500">{appdynamicsFile?.name || 'Select a report to upload and parse it.'}</p>
          </div>
        </div>
        {singleUploadMutation.isError && <p className="mt-3 text-sm text-red-600">{singleUploadMutation.error instanceof Error ? singleUploadMutation.error.message : 'Upload or parsing failed.'}</p>}
        <div className="mt-4 space-y-1 text-xs text-slate-600">
          <p>LoadRunner: {run.loadrunner_upload_path || 'Not uploaded'}</p>
          <p>AppDynamics: {run.appdynamics_upload_path || 'Not uploaded'}</p>
          {metrics && <p>Merged metrics: runs/{runId}/metrics.json</p>}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 mb-6">
        <button
          onClick={() => analyzeMutation.mutate()}
          disabled={analyzeMutation.isPending || (!run.loadrunner_uploaded && !run.appdynamics_uploaded)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50"
        >
          <Play size={16} /> {analyzeMutation.isPending ? 'Analyzing...' : 'Run Analysis'}
        </button>
        <button
          onClick={() => rcaMutation.mutate()}
          disabled={rcaMutation.isPending || !run.analysis_completed}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg font-medium disabled:opacity-50"
        >
          <Brain size={16} /> {rcaMutation.isPending ? 'Running RCA...' : 'AI Root Cause Analysis'}
        </button>
      </div>

      {/* Analysis Results */}
      {analysis && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2"><FileText size={20} /> Analysis Results</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-red-50 rounded-lg"><p className="text-xs text-red-600 font-bold">CRITICAL</p><p className="text-2xl font-bold text-red-700">{analysis.critical_count}</p></div>
            <div className="p-4 bg-orange-50 rounded-lg"><p className="text-xs text-orange-600 font-bold">HIGH</p><p className="text-2xl font-bold text-orange-700">{analysis.high_count}</p></div>
            <div className="p-4 bg-yellow-50 rounded-lg"><p className="text-xs text-yellow-600 font-bold">MEDIUM</p><p className="text-2xl font-bold text-yellow-700">{analysis.medium_count}</p></div>
            <div className="p-4 bg-green-50 rounded-lg"><p className="text-xs text-green-600 font-bold">LOW</p><p className="text-2xl font-bold text-green-700">{analysis.low_count}</p></div>
          </div>

          {analysis.top_slow_apis?.length > 0 && (
            <div>
              <h3 className="font-bold text-slate-800 mb-2">Top Slow APIs</h3>
              <table className="w-full text-sm">
                <thead><tr className="border-b"><th className="py-2 text-left text-slate-500">API</th><th className="py-2 text-right text-slate-500">P95 (ms)</th><th className="py-2 text-right text-slate-500">Avg (ms)</th></tr></thead>
                <tbody>
                  {analysis.top_slow_apis.slice(0, 5).map((api: any, i: number) => (
                    <tr key={i} className="border-b border-slate-100">
                      <td className="py-2 font-medium">{api.api}</td>
                      <td className="py-2 text-right text-red-600 font-bold">{api.p95_ms.toFixed(0)}</td>
                      <td className="py-2 text-right">{api.avg_ms.toFixed(0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {metrics && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Merged Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><p className="text-slate-500">Transactions</p><p className="text-xl font-bold">{metrics.total_transactions}</p></div>
            <div><p className="text-slate-500">Errors</p><p className="text-xl font-bold">{metrics.total_errors}</p></div>
            <div><p className="text-slate-500">Peak Vusers</p><p className="text-xl font-bold">{metrics.peak_concurrent_users}</p></div>
            <div><p className="text-slate-500">Infrastructure Components</p><p className="text-xl font-bold">{metrics.infrastructure?.length ?? 0}</p></div>
          </div>
        </div>
      )}

      {/* RCA Results */}
      {rca && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2"><Brain size={20} /> Root Cause Analysis</h2>
          <div className="mb-4">
            <p className="text-sm text-slate-500">Confidence</p>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-3 bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-blue-600 rounded-full" style={{ width: `${rca.confidence * 100}%` }} />
              </div>
              <span className="text-sm font-bold">{(rca.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg mb-4">
            <p className="font-bold text-slate-900">Root Cause</p>
            <p className="text-slate-700 mt-1">{rca.root_cause}</p>
          </div>
          {rca.recommendations?.length > 0 && (
            <div>
              <p className="font-bold text-slate-900 mb-2">Recommendations</p>
              <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
                {rca.recommendations.map((r: any, i: number) => (
                  <li key={i}>
                    {r.action}
                    {(r.effort || r.impact) && (
                      <span className="text-slate-400"> (effort: {r.effort || '—'}, impact: {r.impact || '—'})</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
