import { useState } from 'react'
import { Send } from 'lucide-react'
import api from '../lib/api'
import type { ChatMessage } from '../types'

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [runId, setRunId] = useState('')

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMsg: ChatMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await api.post('/chat', {
        question: input,
        run_id: runId || undefined,
        history: messages.slice(-10),
      })
      const assistantMsg: ChatMessage = { role: 'assistant', content: res.data.answer }
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error: AI service unavailable' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-48px)]">
      <div className="mb-4">
        <h1 className="text-3xl font-bold text-slate-900">AI Chat</h1>
        <div className="flex items-center gap-3 mt-2">
          <label className="text-sm text-slate-500">Run context:</label>
          <input
            value={runId}
            onChange={(e) => setRunId(e.target.value)}
            placeholder="e.g. RUN-2026-001 (optional)"
            className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm w-64"
          />
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-white rounded-xl border border-slate-200 p-4 space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-center py-16 text-slate-400">
            <p className="text-lg font-medium">Ask me about your performance tests</p>
            <p className="text-sm mt-2">e.g. "Why did RUN-001 fail?" or "Which API is the bottleneck?"</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 text-slate-800'
            }`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 px-4 py-3 rounded-2xl text-sm text-slate-500">Thinking...</div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          placeholder="Ask a question about performance..."
          className="flex-1 px-4 py-3 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  )
}
