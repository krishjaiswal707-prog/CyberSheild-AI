import { SettingsProvider } from '@/context/SettingsContext'
import { ModalProvider } from '@/context/ModalContext'
import { ChatProvider } from '@/context/ChatContext'
import MainLayout from '@/components/Layout/MainLayout'

export default function App() {
  return (
    <SettingsProvider>
      <ChatProvider>
        <ModalProvider>
          <MainLayout />
        </ModalProvider>
      </ChatProvider>
    </SettingsProvider>
  )
}
