<script setup>

import SendIcon from "@/components/character/icon/SendIcon.vue";
import MicIcon from "@/components/character/icon/MicIcon.vue";
import {ref, useTemplateRef} from "vue";
import streamApi from "@/js/http/streamApi.js";
import MicroPhone from "@/components/character/chat_field/chat_history/message/MicroPhone.vue";
const props = defineProps(['friendId'])
const emit = defineEmits(['pushBackMessage', 'addToLastMessage'])
const inputRef = useTemplateRef('input-ref')
const message = ref('')
let processId = 0
const showMic = ref(false) // 控制麦克风组件的显示（默认不显示）
function focus() {
  inputRef.value.focus()
}

async function handleSend(event, audio_message) {

  let content
  if (audio_message) {
    content = audio_message.trim()
  } else {
    content = message.value.trim()
  }


  const curId = ++ processId

  message.value = ''

  // crypto.randomUUID()：生成符合 UUID v4 标准的唯一标识符，确保每条消息都有独立的 ID
  //利用role在渲染时对父组件的每条history消息进行区分
  emit('pushBackMessage', {role: 'user', content: content, id: crypto.randomUUID()})
  emit('pushBackMessage', {role: 'ai', content: '', id: crypto.randomUUID()})

  try{
    await streamApi('/api/friend/message/chat/', {
      body: {
        friend_id: props.friendId,
        message: content,
      },
      onmessage(data, isDone) {
        if(curId !== processId)
          return
        if (data.content) {
          emit('addToLastMessage', data.content)
        }
      },
      onerror(err) {
      },
    })
  }catch(err){
  }
}
function close() {
  ++ processId
  showMic.value = false
}
function handleStop() {
  ++ processId
}

defineExpose({
  focus,
  close,
})
</script>

<template>
  <form v-if="!showMic" @submit.prevent="handleSend" class="absolute bottom-4 left-2 h-12 w-86 flex items-center">
    <input
        ref="input-ref"
        v-model="message"
        class="input bg-black/30 backdrop-blur-sm text-white text-base w-full h-full rounded-2xl pr-20"
        type="text"
        placeholder="文本输入..."
    >
    <div @click="handleSend" class="absolute right-2 w-8 h-8 flex justify-center items-center cursor-pointer">
      <SendIcon />
    </div>
    <div @click="showMic = true" class="absolute right-10 w-8 h-8 flex justify-center items-center cursor-pointer">
      <MicIcon/>
    </div>
  </form>
  <div v-else>
    <MicroPhone
        @close="showMic = false"
        @send="handleSend"
        @stop="handleStop"
    />
  </div>
</template>

<style scoped>

</style>
