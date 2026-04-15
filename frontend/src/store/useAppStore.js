import { create } from 'zustand'

const useAppStore = create((set) => ({
  // Chat
  messages:      [],
  thinking:      false,
  contextOpen:   false,
  activeSources: [],

  // Actions
  addMessage:    (msg)     => set(state => ({ messages: [...state.messages, msg] })),
  setThinking:   (bool)    => set({ thinking: bool }),
  openContext:   (sources) => set({ contextOpen: true, activeSources: sources }),
  closeContext:  ()        => set({ contextOpen: false, activeSources: [] }),
  clearMessages: ()        => set({ messages: [] }),
}))

export default useAppStore
