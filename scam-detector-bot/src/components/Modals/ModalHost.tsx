import { SettingsDrawer } from '@/components/Modals/SettingsDrawer'
import { PostScamSupportModal } from '@/components/Modals/PostScamSupportModal'
import { DetailModal } from '@/components/Modals/DetailModal'

export function ModalHost() {
  return (
    <>
      <SettingsDrawer />
      <PostScamSupportModal />
      <DetailModal />
    </>
  )
}
