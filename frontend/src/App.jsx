import { useState, useEffect, useRef, useCallback } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism"
import {
  Bot, Send, Plus, Settings, Brain, Image, Code, Cpu,
  ChevronDown, Paperclip, Star, Loader2, Menu, X, Zap
} from "lucide-react"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"
// 다이어그램 자동 감지 및 생성 함수
async function generateDiagramFromText(text) {
  const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/)
  if (!jsonMatch) return null
  
  try {
    const data = JSON.parse(jsonMatch[1])
    if (!data.type) return null
    
    let endpoint = ""
    let body = {}
    
    if (data.type === "nodered") {
      endpoint = "/api/diagram/nodered"
      body = { title: data.title || "Node-RED Flow", nodes: data.nodes || [], connections: data.connections || [] }
    } else if (data.type === "circuit") {
      endpoint = "/api/diagram/circuit"
      body = { title: data.title || "회로도", components: data.components || [], connections: data.connections || [] }
    } else {
      return null
    }
    
    const resp = await fetch(`${API}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    })
    const result = await resp.json()
    return result.url ? `http://localhost${result.url}` : null
  } catch (e) {
    return null
  }
}
// ── 모델 아이콘 ──────────────────────────────────────────────
const MODEL_COLORS = {
  claude: { bg: "bg-orange-500",  text: "Claude",  emoji: "🟠" },
  gemini: { bg: "bg-blue-500",    text: "Gemini",  emoji: "🔵" },
  ollama: { bg: "bg-green-600",   text: "Ollama",  emoji: "🟢" },
  gpt:    { bg: "bg-gray-700",    text: "GPT",     emoji: "⚫" },
}

// ── 코드 블록 렌더러 ─────────────────────────────────────────
function CodeBlock({ inline, className, children }) {
  const lang = /language-(\w+)/.exec(className || "")?.[1] || "text"
  const code = String(children).replace(/\n$/, "")
  const [copied, setCopied] = useState(false)

  if (inline) return <code className="bg-gray-800 text-orange-300 px-1 py-0.5 rounded text-sm font-mono">{children}</code>

  return (
    <div className="relative my-3 rounded-lg overflow-hidden border border-gray-700">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <span className="text-xs text-gray-400 font-mono">{lang}</span>
        <button
          onClick={() => { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
          className="text-xs text-gray-400 hover:text-white transition-colors"
        >{copied ? "✓ 복사됨" : "복사"}</button>
      </div>
      <SyntaxHighlighter language={lang} style={oneDark} customStyle={{ margin: 0, borderRadius: 0, fontSize: "13px" }}>
        {code}
      </SyntaxHighlighter>
    </div>
  )
}

// ── 메시지 버블 ──────────────────────────────────────────────
function Message({ msg }) {
  const isUser = msg.role === "user"
  const color = MODEL_COLORS[msg.provider] || MODEL_COLORS.claude
  const [diagUrl, setDiagUrl] = useState(null)

  useEffect(() => {
    if (!isUser && msg.content) {
      generateDiagramFromText(msg.content).then(url => {
        if (url) setDiagUrl(url)
      })
    }
  }, [msg.content, isUser])

  return (
    <div className={`flex gap-3 mb-6 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-white text-sm font-bold
        ${isUser ? "bg-indigo-500" : color.bg}`}>
        {isUser ? "나" : color.emoji}
      </div>

      <div className={`max-w-3xl ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}>
        {!isUser && (
          <span className="text-xs text-gray-500 px-1">{color.text} · {msg.model}</span>
        )}

        <div className={`rounded-2xl px-4 py-3 ${isUser
          ? "bg-indigo-600 text-white rounded-tr-sm"
          : "bg-gray-800 text-gray-100 rounded-tl-sm border border-gray-700"
        }`}>
          {isUser ? (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              className="prose prose-invert prose-sm max-w-none"
              components={{ code: CodeBlock }}
            >
              {msg.content}
            </ReactMarkdown>
          )}
        </div>

        {/* 다이어그램 이미지 자동 표시 */}
        {diagUrl && (
          <div className="mt-2 rounded-xl overflow-hidden border border-gray-700">
            <div className="bg-gray-800 px-3 py-1.5 text-xs text-gray-400 flex items-center gap-2">
              <span>📊</span>
              <span>자동 생성된 다이어그램</span>
              <a href={diagUrl} target="_blank" rel="noreferrer"
                className="ml-auto text-indigo-400 hover:text-indigo-300">
                새 탭에서 열기 ↗
              </a>
            </div>
            <img
              src={diagUrl}
              alt="생성된 다이어그램"
              className="w-full max-w-2xl"
              onError={() => setDiagUrl(null)}
            />
          </div>
        )}
      </div>
    </div>
  )
}

// ── 모델 선택기 ──────────────────────────────────────────────
function ModelSelector({ models, selected, onSelect }) {
  const [open, setOpen] = useState(false)
  const sel = MODEL_COLORS[selected.provider] || MODEL_COLORS.claude

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 transition-colors text-sm">
        <span className={`w-2 h-2 rounded-full ${sel.bg}`}/>
        <span className="text-gray-200 font-medium">{sel.text}</span>
        <span className="text-gray-400 text-xs">{selected.model}</span>
        <ChevronDown className="w-3 h-3 text-gray-400"/>
      </button>

      {open && (
        <div className="absolute top-full mt-2 left-0 z-50 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl min-w-72">
          {Object.entries(models).map(([provider, info]) => (
            <div key={provider}>
              <div className="px-4 py-2 border-b border-gray-800">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${MODEL_COLORS[provider]?.bg || "bg-gray-500"}`}/>
                  <span className="text-xs font-semibold text-gray-400 uppercase">{info.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ml-auto
                    ${info.status === "active" ? "bg-green-900 text-green-400" : "bg-gray-800 text-gray-500"}`}>
                    {info.status === "active" ? "사용가능" : info.status}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {info.features?.map(f => (
                    <span key={f} className="text-xs bg-gray-800 text-gray-500 px-2 py-0.5 rounded">{f}</span>
                  ))}
                </div>
              </div>
              {info.models?.slice(0,3).map(m => (
                <button key={m} onClick={() => { onSelect(provider, m); setOpen(false) }}
                  className={`w-full text-left px-6 py-2 text-sm hover:bg-gray-800 transition-colors
                    ${selected.provider === provider && selected.model === m ? "text-white bg-gray-800" : "text-gray-400"}`}>
                  {m}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── 사이드바 ─────────────────────────────────────────────────
function Sidebar({ sessions, activeSession, onNewSession, onSelectSession, memoryStats, open, onClose }) {
  return (
    <div className={`fixed inset-y-0 left-0 z-40 w-72 bg-gray-950 border-r border-gray-800 flex flex-col
      transform transition-transform duration-200 ${open ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0 lg:static lg:z-auto`}>

      {/* 헤더 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-orange-400"/>
          <span className="font-bold text-white">MyAI Platform</span>
        </div>
        <button onClick={onClose} className="lg:hidden text-gray-400 hover:text-white">
          <X className="w-5 h-5"/>
        </button>
      </div>

      {/* 새 대화 */}
      <button onClick={onNewSession}
        className="mx-4 mt-4 flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white text-sm font-medium transition-colors">
        <Plus className="w-4 h-4"/>
        새 대화
      </button>

      {/* 세션 목록 */}
      <div className="flex-1 overflow-y-auto py-4 space-y-1 px-2">
        {sessions.map(s => (
          <button key={s.id} onClick={() => { onSelectSession(s); onClose() }}
            className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors
              ${activeSession?.id === s.id ? "bg-gray-800 text-white" : "text-gray-400 hover:bg-gray-900 hover:text-gray-200"}`}>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${MODEL_COLORS[s.provider]?.bg || "bg-gray-600"}`}/>
              <span className="truncate">{s.title}</span>
            </div>
            <div className="text-xs text-gray-600 mt-0.5 ml-4">{s.provider} · {s.created_at?.slice(0,10)}</div>
          </button>
        ))}
      </div>

      {/* 메모리 통계 */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
          <Brain className="w-3 h-3"/>
          <span>자기학습 메모리</span>
        </div>
        <div className="bg-gray-900 rounded-lg px-3 py-2 text-xs">
          <div className="flex justify-between text-gray-400">
            <span>저장된 기억</span>
            <span className="text-green-400">{memoryStats?.total_memories || 0}개</span>
          </div>
          <div className="flex justify-between text-gray-400 mt-1">
            <span>상태</span>
            <span className={memoryStats?.status === "online" ? "text-green-400" : "text-yellow-400"}>
              {memoryStats?.status || "확인 중"}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── 메인 앱 ──────────────────────────────────────────────────
export default function App() {
  const [messages,     setMessages]     = useState([])
  const [input,        setInput]        = useState("")
  const [isStreaming,  setIsStreaming]   = useState(false)
  const [sessions,     setSessions]     = useState([])
  const [activeSession,setActiveSession]= useState(null)
  const [models,       setModels]       = useState({})
  const [selectedModel,setSelectedModel]= useState({ provider: "claude", model: "claude-sonnet-4-5" })
  const [memoryStats,  setMemoryStats]  = useState(null)
  const [image,        setImage]        = useState(null)
  const [sidebarOpen,  setSidebarOpen]  = useState(false)
  const [mode,         setMode]         = useState("chat") // chat / image / code / circuit

  const bottomRef  = useRef(null)
  const inputRef   = useRef(null)
  const fileRef    = useRef(null)

  // 초기 데이터 로드
  useEffect(() => {
    fetch(`${API}/api/models/`).then(r => r.json()).then(data => {
      setModels(data)
      // 첫 번째 사용 가능한 모델 자동 선택
      const first = Object.entries(data).find(([,v]) => v.status === "active")
      if (first) setSelectedModel({ provider: first[0], model: first[1].models[0] })
    }).catch(() => {})

    fetch(`${API}/api/memory/stats`).then(r => r.json()).then(setMemoryStats).catch(() => {})
    loadSessions()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function loadSessions() {
    const data = await fetch(`${API}/api/chat/sessions`).then(r => r.json()).catch(() => [])
    setSessions(data)
  }

  async function createSession() {
    const data = await fetch(`${API}/api/chat/sessions?provider=${selectedModel.provider}&model=${selectedModel.model}&title=새 대화`, {
      method: "POST"
    }).then(r => r.json())
    setActiveSession(data)
    setMessages([])
    setSessions(prev => [data, ...prev])
  }

  async function selectSession(session) {
    setActiveSession(session)
    setSelectedModel({ provider: session.provider, model: session.model })
    const msgs = await fetch(`${API}/api/chat/sessions/${session.id}/messages`).then(r => r.json()).catch(() => [])
    setMessages(msgs)
  }

  async function sendMessage() {
    if (!input.trim() && !image) return
    if (isStreaming) return

    // 세션이 없으면 자동 생성
    let session = activeSession
    if (!session) {
      const data = await fetch(
        `${API}/api/chat/sessions?provider=${selectedModel.provider}&model=${selectedModel.model}&title=${input.slice(0,30)}`,
        { method: "POST" }
      ).then(r => r.json())
      session = data
      setActiveSession(data)
      setSessions(prev => [data, ...prev])
    }

    const userMsg = { role: "user", content: input, provider: selectedModel.provider, model: selectedModel.model }
    setMessages(prev => [...prev, userMsg])
    setInput("")
    setIsStreaming(true)

    const aiMsg = { role: "assistant", content: "", provider: selectedModel.provider, model: selectedModel.model }
    setMessages(prev => [...prev, aiMsg])

    const form = new FormData()
    form.append("session_id", session.id)
    form.append("provider",   selectedModel.provider)
    form.append("model",      selectedModel.model)
    form.append("message",    input)
    form.append("use_memory", "true")
    if (image) form.append("image", image)

    try {
      const resp = await fetch(`${API}/api/chat/stream`, { method: "POST", body: form })
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          try {
            const evt = JSON.parse(line.slice(6))
            if (evt.type === "chunk") {
              setMessages(prev => {
                const msgs = [...prev]
                msgs[msgs.length - 1] = { ...msgs[msgs.length-1], content: msgs[msgs.length-1].content + evt.content }
                return msgs
              })
            }
          } catch {}
        }
      }
    } catch (e) {
      setMessages(prev => {
        const msgs = [...prev]
        msgs[msgs.length - 1] = { ...msgs[msgs.length-1], content: `❌ 오류: ${e.message}` }
        return msgs
      })
    } finally {
      setIsStreaming(false)
      setImage(null)
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <div className="flex h-screen bg-gray-950 text-white overflow-hidden">
      {/* 사이드바 오버레이 */}
      {sidebarOpen && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={() => setSidebarOpen(false)}/>}

      <Sidebar
        sessions={sessions}
        activeSession={activeSession}
        onNewSession={createSession}
        onSelectSession={selectSession}
        memoryStats={memoryStats}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* 메인 영역 */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* 상단 바 */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-800 bg-gray-950">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-gray-400 hover:text-white">
            <Menu className="w-5 h-5"/>
          </button>

          <ModelSelector models={models} selected={selectedModel} onSelect={(p, m) => setSelectedModel({ provider: p, model: m })}/>

          <div className="flex gap-1 ml-auto">
            {[
              { id:"chat",    icon: Bot,   label:"채팅"     },
              { id:"image",   icon: Image, label:"이미지"   },
              { id:"code",    icon: Code,  label:"코드실행" },
              { id:"circuit", icon: Cpu,   label:"회로설계" },
            ].map(({ id, icon: Icon, label }) => (
              <button key={id} onClick={() => setMode(id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                  ${mode === id ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800"}`}>
                <Icon className="w-3.5 h-3.5"/>
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4">
              <div className="w-16 h-16 bg-indigo-600/20 rounded-full flex items-center justify-center">
                <Zap className="w-8 h-8 text-indigo-400"/>
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">MyAI Platform</h2>
                <p className="text-gray-400 mt-1 text-sm">Claude · Gemini · Ollama 통합 AI 허브</p>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-4 max-w-md">
                {[
                  "회로기판 설계 도와줘", "Python 코드 작성해줘",
                  "이 이미지 분석해줘",   "RTX 4070 Super 온도 모니터링 코드",
                ].map(s => (
                  <button key={s} onClick={() => setInput(s)}
                    className="text-left px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition-colors border border-gray-700">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <Message key={i} msg={msg} onRate={null}/>
          ))}

          {isStreaming && (
            <div className="flex items-center gap-2 text-gray-500 text-sm ml-11">
              <Loader2 className="w-4 h-4 animate-spin"/>
              <span>{MODEL_COLORS[selectedModel.provider]?.text || "AI"} 응답 생성 중...</span>
            </div>
          )}

          <div ref={bottomRef}/>
        </div>

        {/* 이미지 미리보기 */}
        {image && (
          <div className="px-4 pb-2">
            <div className="flex items-center gap-2 bg-gray-800 rounded-lg p-2 w-fit">
              <img src={URL.createObjectURL(image)} className="w-12 h-12 rounded object-cover"/>
              <span className="text-xs text-gray-400">{image.name}</span>
              <button onClick={() => setImage(null)} className="text-gray-500 hover:text-red-400 ml-2">
                <X className="w-4 h-4"/>
              </button>
            </div>
          </div>
        )}

        {/* 입력 영역 */}
        <div className="px-4 pb-4">
          <div className="flex items-end gap-2 bg-gray-800 rounded-2xl border border-gray-700 focus-within:border-indigo-500 transition-colors p-3">
            <input type="file" ref={fileRef} className="hidden" accept="image/*"
              onChange={e => setImage(e.target.files[0])}/>

            <button onClick={() => fileRef.current?.click()}
              className="text-gray-500 hover:text-gray-300 flex-shrink-0 transition-colors">
              <Paperclip className="w-5 h-5"/>
            </button>

            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder={`${MODEL_COLORS[selectedModel.provider]?.text || "AI"}에게 메시지를 입력하세요... (Shift+Enter: 줄바꿈)`}
              className="flex-1 bg-transparent resize-none outline-none text-white placeholder-gray-500 text-sm leading-relaxed max-h-40 min-h-[24px]"
              rows={1}
              style={{ height: "auto" }}
              onInput={e => { e.target.style.height = "auto"; e.target.style.height = e.target.scrollHeight + "px" }}
            />

            <button onClick={sendMessage} disabled={isStreaming || (!input.trim() && !image)}
              className={`flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all
                ${isStreaming || (!input.trim() && !image)
                  ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/25"
                }`}>
              {isStreaming ? <Loader2 className="w-4 h-4 animate-spin"/> : <Send className="w-4 h-4"/>}
            </button>
          </div>

          <p className="text-xs text-gray-600 text-center mt-2">
            자기학습 메모리 활성화 · 대화가 자동으로 저장됩니다
          </p>
        </div>
      </div>
    </div>
  )
}
