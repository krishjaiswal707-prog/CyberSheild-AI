import { Suspense, lazy } from 'react'
import { Header } from '@/components/Layout/Header'
import { Sidebar } from '@/components/Layout/Sidebar'
import { ChatContainer } from '@/components/Chat/ChatContainer'

const ModalHost = lazy(() =>
  import('@/components/Modals/ModalHost').then((m) => ({ default: m.ModalHost })),
)

export function MainLayout() {
  return (
    <div className="flex h-full w-full flex-col bg-bg text-text-primary">
      <Header />

      <div className="flex min-h-0 flex-1">
        <Sidebar />

        <main
          className="flex min-h-0 min-w-0 flex-1 flex-col"
          aria-label="SafeGuard AI chat"
        >
          <ChatContainer />
        </main>
      </div>

      <Suspense fallback={null}>
        <ModalHost />
      </Suspense>
    </div>
  )
}

export default MainLayout
