import { useCallback, useReducer } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { sendMessage } from '../api/orderAgent'
import type { ChatMessage, ChatState } from '../types'

// ─── State machine ────────────────────────────────────────────────────────────

type Action =
  | { type: 'USER_SEND'; message: ChatMessage }
  | {
      type: 'AGENT_REPLY'
      message: ChatMessage
      taskId?: string
      contextId?: string
    }
  | { type: 'LOADING_START' }
  | { type: 'LOADING_END' }
  | { type: 'ERROR'; error: string }
  | { type: 'CLEAR_ERROR' }

const initialState: ChatState = {
  messages: [],
  isLoading: false,
}

function chatReducer(state: ChatState, action: Action): ChatState {
  switch (action.type) {
    case 'USER_SEND':
      return {
        ...state,
        messages: [...state.messages, action.message],
        error: undefined,
      }
    case 'AGENT_REPLY':
      return {
        ...state,
        messages: [...state.messages, action.message],
        taskId: action.taskId ?? state.taskId,
        contextId: action.contextId ?? state.contextId,
        isLoading: false,
      }
    case 'LOADING_START':
      return { ...state, isLoading: true, error: undefined }
    case 'LOADING_END':
      return { ...state, isLoading: false }
    case 'ERROR':
      return { ...state, isLoading: false, error: action.error }
    case 'CLEAR_ERROR':
      return { ...state, error: undefined }
    default:
      return state
  }
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export interface UseChatReturn {
  messages: ChatMessage[]
  isLoading: boolean
  error?: string
  send: (text: string) => Promise<void>
  clearError: () => void
}

export function useChat(): UseChatReturn {
  const [state, dispatch] = useReducer(chatReducer, initialState)

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || state.isLoading) return

      const userMessage: ChatMessage = {
        id: uuidv4(),
        role: 'user',
        text: trimmed,
        timestamp: new Date(),
      }

      dispatch({ type: 'USER_SEND', message: userMessage })
      dispatch({ type: 'LOADING_START' })

      try {
        const parsed = await sendMessage(trimmed, state.taskId, state.contextId)

        const agentMessage: ChatMessage = {
          id: uuidv4(),
          role: 'assistant',
          text: parsed.text,
          orderConfirmation: parsed.orderConfirmation,
          auditSteps: parsed.auditSteps.length ? parsed.auditSteps : undefined,
          correlationId: parsed.correlationId,
          timestamp: new Date(),
        }

        dispatch({
          type: 'AGENT_REPLY',
          message: agentMessage,
          taskId: parsed.taskId,
          contextId: parsed.contextId,
        })
      } catch (err) {
        const errorText =
          err instanceof Error ? err.message : 'Unexpected error occurred'
        dispatch({ type: 'ERROR', error: errorText })
      }
    },
    [state.isLoading, state.taskId, state.contextId],
  )

  const clearError = useCallback(() => dispatch({ type: 'CLEAR_ERROR' }), [])

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    send,
    clearError,
  }
}
