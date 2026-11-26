import { onBeforeUnmount, ref, watch } from 'vue'

// Only writing tabs announce themselves. Reader tabs never trigger the warning.
export function useDuplicateLiveTab(liveId) {
  const duplicate = ref(false)
  const tab = crypto.randomUUID()
  let channel, timer
  const peers = new Map()
  const stop = () => {
    channel?.postMessage({ type: 'leave', tab })
    channel?.close()
    clearInterval(timer)
    peers.clear()
    duplicate.value = false
    channel = null
  }
  watch(liveId, (id) => {
    stop()
    if (id == null || !('BroadcastChannel' in window)) return
    channel = new BroadcastChannel(`kolmi:live-writer:${id}`)
    const announce = () => channel.postMessage({ type: 'present', tab })
    channel.onmessage = ({ data }) => {
      if (!data || data.tab === tab) return
      if (data.type === 'leave') peers.delete(data.tab)
      else if (data.type === 'present' || data.type === 'hello') {
        peers.set(data.tab, Date.now())
        if (data.type === 'hello') announce()
      }
      duplicate.value = peers.size > 0
    }
    channel.postMessage({ type: 'hello', tab })
    timer = setInterval(() => {
      for (const [peer, seen] of peers) if (Date.now() - seen > 30000) peers.delete(peer)
      duplicate.value = peers.size > 0
      announce()
    }, 10000)
  }, { immediate: true })
  onBeforeUnmount(stop)
  return duplicate
}
