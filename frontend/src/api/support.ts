export type SupportMessage = {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export type SupportPageContext = {
  page: string
  product_slug?: string | null
  order_no?: string | null
}

export type Conversation = {
  id: string
  client_type: string
  messages: SupportMessage[]
}

export type SendMessageResponse = {
  conversation_id: string
  reply: string
  messages: SupportMessage[]
  tool_call_count: number
  handoff: {
    ticket_no: string
    status: string
    reason: string
  } | null
}

export type SupportStreamEvent =
  | {
      type: 'meta'
      tool_call_count: number
      handoff: SendMessageResponse['handoff']
    }
  | { type: 'token'; text: string }
  | { type: 'done'; messages: SupportMessage[] }

async function responseError(response: Response): Promise<Error> {
  let message = `客服请求失败：HTTP ${response.status}`
  try {
    const body = (await response.json()) as { detail?: string }
    if (body.detail) {
      message = body.detail
    }
  } catch {
    // Use the status fallback if the response is not JSON.
  }
  return new Error(message)
}

export async function createConversation(): Promise<string> {
  const response = await fetch('/api/v1/conversations', {
    method: 'POST',
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) {
    throw await responseError(response)
  }
  const data = (await response.json()) as { conversation_id: string }
  return data.conversation_id
}

export async function fetchConversation(
  conversationId: string,
  signal?: AbortSignal,
): Promise<Conversation> {
  const response = await fetch(
    `/api/v1/conversations/${encodeURIComponent(conversationId)}`,
    {
      headers: { Accept: 'application/json' },
      signal,
    },
  )
  if (!response.ok) {
    throw await responseError(response)
  }
  return (await response.json()) as Conversation
}

export async function sendSupportMessage(
  conversationId: string,
  message: string,
  pageContext: SupportPageContext,
): Promise<SendMessageResponse> {
  const response = await fetch(
    `/api/v1/conversations/${encodeURIComponent(conversationId)}/messages`,
    {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        page_context: pageContext,
      }),
    },
  )
  if (!response.ok) {
    throw await responseError(response)
  }
  return (await response.json()) as SendMessageResponse
}

export async function streamSupportMessage(
  conversationId: string,
  message: string,
  pageContext: SupportPageContext,
  onEvent: (event: SupportStreamEvent) => void,
): Promise<SendMessageResponse> {
  const response = await fetch(
    `/api/v1/conversations/${encodeURIComponent(conversationId)}/messages/stream`,
    {
      method: 'POST',
      headers: {
        Accept: 'text/event-stream',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        page_context: pageContext,
      }),
    },
  )

  if (!response.ok) {
    throw await responseError(response)
  }
  if (!response.body) {
    throw new Error('浏览器无法读取客服流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let reply = ''
  let finalMessages: SupportMessage[] | null = null
  let toolCallCount = 0
  let handoff: SendMessageResponse['handoff'] = null

  function processBlock(block: string) {
    const lines = block.split(/\r?\n/)
    const eventType = lines
      .find((line) => line.startsWith('event: '))
      ?.slice(7)
    const data = lines
      .filter((line) => line.startsWith('data: '))
      .map((line) => line.slice(6))
      .join('\n')

    if (!eventType || !data) {
      return
    }

    const parsed = JSON.parse(data) as Record<string, unknown>
    if (eventType === 'meta') {
      toolCallCount = Number(parsed.tool_call_count ?? 0)
      handoff =
        (parsed.handoff as SendMessageResponse['handoff'] | undefined) ?? null
      onEvent({ type: 'meta', tool_call_count: toolCallCount, handoff })
    } else if (eventType === 'token') {
      const text = String(parsed.text ?? '')
      reply += text
      onEvent({ type: 'token', text })
    } else if (eventType === 'done') {
      finalMessages = parsed.messages as SupportMessage[]
      onEvent({ type: 'done', messages: finalMessages })
    } else if (eventType === 'error') {
      throw new Error(String(parsed.detail ?? '客服流式响应失败'))
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const blocks = buffer.split(/\r?\n\r?\n/)
    buffer = blocks.pop() ?? ''
    for (const block of blocks) {
      processBlock(block)
    }
    if (done) {
      break
    }
  }

  if (buffer.trim()) {
    processBlock(buffer)
  }
  if (!finalMessages) {
    throw new Error('客服流式响应没有正常结束')
  }

  return {
    conversation_id: conversationId,
    reply,
    messages: finalMessages,
    tool_call_count: toolCallCount,
    handoff,
  }
}

