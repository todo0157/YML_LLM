import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Settings, Trash2, ChevronRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import './App.css'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: string[]
  isWelcome?: boolean
}

interface ApiConfig {
  endpoint: string
  isConnected: boolean
}

const EXAMPLE_QUESTIONS = [
  "MEMS 센서 제작 공정 중 에칭 속도 최적화 방법",
  "PLA 최적 온도와 속도 설정 알려주세요",
  "PETG stringing 해결 방법"
]

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isWelcome: true
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [config, setConfig] = useState<ApiConfig>({
    endpoint: import.meta.env.VITE_API_ENDPOINT || '/api',
    isConnected: false
  })

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    checkConnection()
  }, [config.endpoint])

  const checkConnection = async () => {
    try {
      const response = await fetch(`${config.endpoint}/health`)
      setConfig(prev => ({ ...prev, isConnected: response.ok }))
    } catch {
      setConfig(prev => ({ ...prev, isConnected: false }))
    }
  }

  const handleExampleClick = (question: string) => {
    setInput(question)
    inputRef.current?.focus()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch(`${config.endpoint}/research`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.content
        })
      })

      if (!response.ok) {
        throw new Error('API 요청 실패')
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || '응답을 생성할 수 없습니다.',
        timestamp: new Date(),
        sources: data.sources
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ 오류가 발생했습니다.\n\n${config.isConnected ? '서버 처리 중 오류가 발생했습니다.' : '서버에 연결할 수 없습니다.'}\n\n**해결 방법:**\n1. 네트워크 연결 확인\n2. 잠시 후 다시 시도`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const clearChat = () => {
    setMessages([{
      id: '0',
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isWelcome: true
    }])
  }

  const renderWelcomeMessage = () => (
    <>
      <p style={{ fontWeight: 500, marginBottom: '0.75rem' }}>
        안녕하세요! 연세 마이크로시스템 연구실(YML) AI 어시스턴트입니다. 👋
      </p>
      <p style={{ marginBottom: '1rem' }} className="text-muted">
        연구 논문 분석, 3D 프린팅 최적화, 실험 데이터 처리 등 다양한 질문에 답해드릴 수 있습니다.
      </p>
      <div className="example-questions">
        <p>예시 질문:</p>
        {EXAMPLE_QUESTIONS.map((q, idx) => (
          <div
            key={idx}
            className="example-item"
            onClick={() => handleExampleClick(q)}
          >
            <ChevronRight size={16} />
            <span>{q}</span>
          </div>
        ))}
      </div>
    </>
  )

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="header-icon">
            <span className="material-symbols-outlined">school</span>
          </div>
          <div className="header-text">
            <h1>YML Research Assistant</h1>
            <p className="subtitle">Yonsei Microsystem Laboratory AI</p>
          </div>
        </div>
        <div className="header-right">
          <span className={`status ${config.isConnected ? 'connected' : 'disconnected'}`}>
            {config.isConnected ? '연결됨' : '연결 안됨'}
          </span>
          <button
            className="icon-btn"
            onClick={clearChat}
            title="대화 초기화"
          >
            <Trash2 size={20} />
          </button>
          <button
            className="icon-btn"
            onClick={() => setShowSettings(!showSettings)}
            title="설정"
          >
            <Settings size={20} />
          </button>
        </div>
      </header>

      {showSettings && (
        <div className="settings-panel">
          <div className="settings-content">
            <h3>API 설정</h3>
            <label>
              <span>API 엔드포인트</span>
              <input
                type="text"
                value={config.endpoint}
                onChange={(e) => setConfig(prev => ({ ...prev, endpoint: e.target.value }))}
                placeholder="/api"
              />
            </label>
            <button onClick={checkConnection} className="check-btn">
              연결 테스트
            </button>
          </div>
        </div>
      )}

      <main className="messages-container">
        <div className="messages">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.role}`}
            >
              <div className="message-avatar">
                {message.role === 'user' ? (
                  '👤'
                ) : (
                  <span className="material-symbols-outlined">smart_toy</span>
                )}
              </div>
              <div className="message-wrapper">
                <div className="message-content">
                  {message.isWelcome ? (
                    renderWelcomeMessage()
                  ) : (
                    <>
                      <ReactMarkdown
                        rehypePlugins={[rehypeRaw]}
                        components={{
                          a: ({ href, children }) => (
                            <a href={href} target="_blank" rel="noopener noreferrer" className="source-link">
                              {children}
                            </a>
                          )
                        }}
                      >{message.content}</ReactMarkdown>
                      {message.sources && message.sources.length > 0 && (
                        <div className="sources">
                          <strong>참고 소스:</strong>
                          <ul>
                            {message.sources.slice(0, 3).map((src, idx) => (
                              <li key={idx}>
                                <a href={src} target="_blank" rel="noopener noreferrer">
                                  {src.length > 50 ? src.substring(0, 50) + '...' : src}
                                </a>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </>
                  )}
                </div>
                <span className="timestamp">
                  {message.timestamp.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message assistant">
              <div className="message-avatar">
                <span className="material-symbols-outlined">smart_toy</span>
              </div>
              <div className="message-wrapper">
                <div className="message-content loading">
                  <Loader2 className="spinner" size={20} />
                  <span>연구 중... 웹 검색, 지식베이스 조회</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="input-container">
        <form onSubmit={handleSubmit} className="input-form">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="연구 관련 질문을 입력하세요... (Shift+Enter: 줄바꿈)"
            disabled={isLoading}
            rows={1}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="send-btn"
          >
            {isLoading ? <Loader2 className="spinner" size={20} /> : <Send size={18} />}
          </button>
        </form>
        <p className="disclaimer">
          AI가 생성한 응답입니다. 중요한 결정 전에 검증해주세요. | Yonsei Microsystem Laboratory
        </p>
      </footer>
    </div>
  )
}

export default App
