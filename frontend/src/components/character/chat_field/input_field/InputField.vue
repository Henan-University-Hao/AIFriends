<script setup>

import SendIcon from "@/components/character/icon/SendIcon.vue";
import MicIcon from "@/components/character/icon/MicIcon.vue";
import {ref, useTemplateRef} from "vue";
import streamApi from "@/js/http/streamApi.js";
const props = defineProps(['friendId'])
const emit = defineEmits(['pushBackMessage', 'addToLastMessage'])
const inputRef = useTemplateRef('input-ref')
const message = ref('')
let isProcessing = false //是否正在执行（防止重复发消息）
function focus() {
  inputRef.value.focus()
}

async function handleSend() {
  if (isProcessing) return
  isProcessing = true

  const content = message.value.trim()
  if(!content) return // 内容判空
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
        if(isDone){
          isProcessing = false
        } else if (data.content) {
          emit('addToLastMessage', data.content)
        }
      },
      onerror(err) {
        isProcessing = false
      },
    })
  }catch(err){
    isProcessing = false
  }
}

defineExpose({
  focus,
})
</script>

<template>
  <form @submit.prevent="handleSend" class="absolute bottom-4 left-2 h-12 w-86 flex items-center">
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
    <div class="absolute right-10 w-8 h-8 flex justify-center items-center cursor-pointer">
      <MicIcon />
    </div>
  </form>
</template>

<style scoped>

</style>
