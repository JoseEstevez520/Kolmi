import { onBeforeUnmount, ref, watch } from 'vue'
import { createStreamPace, wholeWords } from 'elastic-ui'

// A streamed text at the library's pace (createStreamPace): steady instead of in the model's
// bursts, a whole word at a time. `paced` is what to draw; `settling` stays true until it has
// caught up with what arrived, so whoever draws it keeps treating it as still coming.
export function usePacedText(text, streaming) {
  const shown = ref(0)
  const quiet = ref(false)
  const paced = ref('')
  const settling = ref(false)
  const draw = () => {
    paced.value = wholeWords(text(), shown.value, streaming(), quiet.value)
    settling.value = streaming() || paced.value.length < text().length
  }
  const pace = createStreamPace({
    onFrame: (n) => {
      shown.value = n
      draw()
    },
    onQuiet: () => {
      quiet.value = true
      draw()
    },
    onCaughtUp: draw,
    // What was already there when it was drawn first (an earlier answer) just shows.
    startShown: !streaming(),
  })
  watch(
    [text, streaming],
    ([t, s]) => {
      pace.update(t || '', Boolean(s))
      shown.value = pace.shown
      quiet.value = pace.quiet
      draw()
    },
    { immediate: true },
  )
  onBeforeUnmount(() => pace.stop())
  return { paced, settling }
}
