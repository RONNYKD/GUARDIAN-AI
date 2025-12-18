import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

interface WebSocketContextType {
  isConnected: boolean
  lastMessage: WebSocketMessage | null
  sendMessage: (message: any) => void
  subscribe: (type: string, callback: (data: any) => void) => () => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const subscribersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map())
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const connect = useCallback(() => {
    try {
      // WebSocket URL - adjust for your backend
      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)

          // Notify subscribers
          const callbacks = subscribersRef.current.get(message.type)
          if (callbacks) {
            callbacks.forEach(callback => callback(message.data))
          }

          // Notify wildcard subscribers
          const wildcardCallbacks = subscribersRef.current.get('*')
          if (wildcardCallbacks) {
            wildcardCallbacks.forEach(callback => callback(message))
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        wsRef.current = null

        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connect()
        }, 5000)
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Error connecting to WebSocket:', error)
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const subscribe = useCallback((type: string, callback: (data: any) => void) => {
    if (!subscribersRef.current.has(type)) {
      subscribersRef.current.set(type, new Set())
    }
    subscribersRef.current.get(type)!.add(callback)

    // Return unsubscribe function
    return () => {
      const callbacks = subscribersRef.current.get(type)
      if (callbacks) {
        callbacks.delete(callback)
        if (callbacks.size === 0) {
          subscribersRef.current.delete(type)
        }
      }
    }
  }, [])

  return (
    <WebSocketContext.Provider value={{ isConnected, lastMessage, sendMessage, subscribe }}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}
