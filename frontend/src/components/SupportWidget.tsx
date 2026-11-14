import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import {
  createConversation,
  fetchConversation,
  streamSupportMessage,
  type SendMessageResponse,
  type SupportPageContext,
} from '../api/support'

const CONVERSATION_STORAGE_KEY = 'shop-support-conversation-id'

function getPageContext(pathname: string): SupportPageContext {
  const productMatch = pathname.match(/^\/products\/([^/]+)$/)
  if (productMatch) {
    return {
      page: 'product_detail',
      product_slug: decodeURIComponent(productMatch[1]),
    }
  }

  const orderMatch = pathname.match(/^\/orders\/([^/]+)$/)
  if (orderMatch) {
    return {
      page: 'order_detail',
      order_no: decodeURIComponent(orderMatch[1]),
    }
  }

  if (pathname === '/cart') {
    return { page: 'cart' }
  }
  if (pathname === '/orders') {
    return { page: 'orders' }
  }
  return { page: 'home' }
}

export function SupportWidget() {
  const location = useLocation()
  const [isOpen, setIsOpen] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(() =>
    localStorage.getItem(CONVERSATION_STORAGE_KEY),
  )
  const [draft, setDraft] = useState('')
  const [streamingText, setStreamingText] = useState('')
  const [agentMeta, setAgentMeta] = useState<{
    toolCallCount: number
    handoff: SendMessageResponse['handoff']
  }>({
    toolCallCount: 0,
    handoff: null,
  })
  const messageEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  const pageContext = getPageContext(location.pathname)

  const conversationQuery = useQuery({
    queryKey: ['support-conversation', conversationId],
    queryFn: ({ signal }) => fetchConversation(conversationId ?? '', signal),
    enabled: Boolean(conversationId),
  })

  useEffect(() => {
    if (!isOpen) {
      return
    }
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [isOpen])

  const sendMutation = useMutation({
    mutationFn: async (message: string) => {
      let activeConversationId = conversationQuery.isSuccess
        ? conversationId
        : null
      if (!activeConversationId) {
        activeConversationId = await createConversation()
        setConversationId(activeConversationId)
        localStorage.setItem(CONVERSATION_STORAGE_KEY, activeConversationId)
      }
      return streamSupportMessage(
        activeConversationId,
        message,
        pageContext,
        (event) => {
          if (event.type === 'token') {
            setStreamingText((current) => current + event.text)
          } else if (event.type === 'meta') {
            setAgentMeta({
              toolCallCount: event.tool_call_count,
              handoff: event.handoff,
            })
          }
        },
      )
    },
    onMutate: () => {
      setDraft('')
      setStreamingText('')
      setAgentMeta({ toolCallCount: 0, handoff: null })
    },
    onSuccess: (response) => {
      queryClient.setQueryData(
        ['support-conversation', response.conversation_id],
        {
          id: response.conversation_id,
          client_type: 'web',
          messages: response.messages,
        },
      )
      setStreamingText('')
    },
    onError: () => {
      setStreamingText('')
    },
  })

  const messages = useMemo(
    () =>
      sendMutation.data?.messages ?? conversationQuery.data?.messages ?? [],
    [conversationQuery.data, sendMutation.data],
  )

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ block: 'end' })
  }, [messages, isOpen, sendMutation.isPending])

  function submitMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const message = draft.trim()
    if (!message || sendMutation.isPending) {
      return
    }
    sendMutation.mutate(message)
  }

  return (
    <>
      <button
        className={`support-launcher ${isOpen ? 'is-open' : ''}`}
        type="button"
        aria-expanded={isOpen}
        aria-controls="support-panel"
        onClick={() => setIsOpen((current) => !current)}
      >
        <span className="support-launcher-icon" aria-hidden="true">
          栖
        </span>
        <span>{isOpen ? '收起客服' : '客服'}</span>
      </button>

      {isOpen ? (
        <aside
          className="support-panel"
          id="support-panel"
          aria-label="客服对话"
        >
          <header className="support-panel-header">
            <div>
              <span className="support-avatar">栖</span>
              <div>
                <strong>桌面好物客服</strong>
                <small>DeepSeek 驱动 · 演示环境</small>
              </div>
            </div>
            <button
              type="button"
              aria-label="关闭客服"
              onClick={() => setIsOpen(false)}
            >
              ×
            </button>
          </header>

          <div className="support-context">
            当前页面：{pageContext.page}
            {pageContext.product_slug
              ? ` · ${pageContext.product_slug}`
              : ''}
            {pageContext.order_no ? ` · ${pageContext.order_no}` : ''}
          </div>

          <div className="support-messages" aria-live="polite">
            {messages.length === 0 ? (
              <div className="support-welcome">
                <strong>你好，我是小栖。</strong>
                <p>
                  可以问我当前商品、最近的订单或商城售后规则。支付和退款为模拟流程。
                </p>
              </div>
            ) : null}

            {messages.map((message) => (
              <div
                className={`support-message support-message--${message.role}`}
                key={message.id}
              >
                {message.content}
              </div>
            ))}

            {sendMutation.isPending ? (
              <div className="support-message support-message--user">
                {sendMutation.variables}
              </div>
            ) : null}

            {sendMutation.isPending ? (
              streamingText ? (
                <div className="support-message support-message--assistant">
                  {streamingText}
                </div>
              ) : (
                <div className="support-typing">小栖正在思考…</div>
              )
            ) : null}
            <div ref={messageEndRef} />
          </div>

          {sendMutation.isError ? (
            <p className="support-error" role="alert">
              {sendMutation.error instanceof Error
                ? sendMutation.error.message
                : '客服暂时不可用'}
            </p>
          ) : null}

          {agentMeta.toolCallCount > 0 ? (
            <div className="support-tool-count">
              已调用 {agentMeta.toolCallCount} 个业务工具
            </div>
          ) : null}

          {agentMeta.handoff ? (
            <div className="support-handoff" role="status">
              <strong>已创建人工工单</strong>
              <span>工单号：{agentMeta.handoff.ticket_no}</span>
            </div>
          ) : null}

          <form className="support-composer" onSubmit={submitMessage}>
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="输入你的问题…"
              maxLength={2000}
              aria-label="客服消息"
            />
            <button type="submit" disabled={!draft.trim() || sendMutation.isPending}>
              发送
            </button>
          </form>
        </aside>
      ) : null}
    </>
  )
}

