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
}

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

