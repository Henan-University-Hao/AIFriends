<script setup>
import SendIcon from "@/components/character/icon/SendIcon.vue";
import MicIcon from "@/components/character/icon/MicIcon.vue";
import { ref, useTemplateRef, onUnmounted } from "vue";
import streamApi from "@/js/http/streamApi.js";
import MicroPhone from "@/components/character/chat_field/chat_history/message/MicroPhone.vue";
import { getErrorMessage } from "@/js/http/api.js";

const props = defineProps(['friendId'])
const emit = defineEmits(['pushBackMessage', 'addToLastMessage'])
const inputRef = useTemplateRef('input-ref')
const message = ref('')
const errorMessage = ref('')
const showMic = ref(false)
const isMuted = ref(false)
let processId = 0

let mediaSource = null;
let sourceBuffer = null;
let audioPlayer = new Audio();
let audioQueue = [];
let isUpdating = false;

const initAudioStream = () => {
    audioPlayer.pause();
    audioQueue = [];
    isUpdating = false;

    mediaSource = new MediaSource();
    audioPlayer.src = URL.createObjectURL(mediaSource);

    mediaSource.addEventListener('sourceopen', () => {
        try {
            sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg');
            sourceBuffer.addEventListener('updateend', () => {
                isUpdating = false;
                processQueue();
            });
        } catch (e) {
            console.error("MSE AddSourceBuffer Error:", e);
        }
    });

    audioPlayer.play().catch(() => console.error("等待用户交互以播放音频"));
};

const processQueue = () => {
    if (isUpdating || audioQueue.length === 0 || !sourceBuffer || sourceBuffer.updating) {
        return;
    }

    isUpdating = true;
    const chunk = audioQueue.shift();
    try {
        sourceBuffer.appendBuffer(chunk);
    } catch (e) {
        console.error("SourceBuffer Append Error:", e);
        isUpdating = false;
    }
};

const stopAudio = () => {
    audioPlayer.pause();
    audioQueue = [];
    isUpdating = false;

    if (mediaSource) {
        if (mediaSource.readyState === 'open') {
            try {
                mediaSource.endOfStream();
            } catch (e) {
            }
        }
        mediaSource = null;
    }

    if (audioPlayer.src) {
        URL.revokeObjectURL(audioPlayer.src);
        audioPlayer.src = '';
    }
};

const handleAudioChunk = (base64Data) => {
    try {
        const binaryString = atob(base64Data);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        audioQueue.push(bytes);
        processQueue();
    } catch (e) {
        console.error("Base64 Decode Error:", e);
    }
};

onUnmounted(() => {
    audioPlayer.pause();
    audioPlayer.src = '';
});

function focus() {
  inputRef.value.focus()
}

function handleToggleMute() {
  isMuted.value = !isMuted.value
  if (isMuted.value) {
    stopAudio()
  }
}

async function handleSend(event, audioMessage) {
  errorMessage.value = ''

  const content = audioMessage ? audioMessage.trim() : message.value.trim()
  if (!content) {
    return
  }

  if (isMuted.value) {
    stopAudio()
  } else {
    initAudioStream()
  }

  const curId = ++processId
  message.value = ''

  emit('pushBackMessage', { role: 'user', content, id: crypto.randomUUID() })
  emit('pushBackMessage', { role: 'ai', content: '', id: crypto.randomUUID() })

  try {
    await streamApi('/api/friend/message/chat/', {
      body: {
        friend_id: props.friendId,
        message: content,
        enable_tts: !isMuted.value,
      },
      onmessage(data) {
        if (curId !== processId) {
          return
        }
        if (data.content) {
          emit('addToLastMessage', data.content)
        }
        if (data.audio && !isMuted.value) {
          handleAudioChunk(data.audio)
        }
      },
      onerror(err) {
        errorMessage.value = getErrorMessage(err, '操作过快了，请稍后再试')
      },
    })
  } catch (err) {
    errorMessage.value = getErrorMessage(err, '操作过快了，请稍后再试')
  }
}

function close() {
  ++processId
  showMic.value = false
  stopAudio()
}

function handleStop() {
  ++processId
  stopAudio()
}

defineExpose({
  focus,
  close,
})
</script>

<template>
  <div
      @click="handleToggleMute"
      class="absolute top-2 right-11 z-10 h-8 w-8 cursor-pointer rounded-full bg-black/35 backdrop-blur-sm flex items-center justify-center text-white"
      :title="isMuted ? '取消静音' : '静音'"
  >
    <svg v-if="!isMuted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="h-5 w-5 fill-current">
      <path d="M14 3.23a1 1 0 0 0-1.66-.75L7.96 6.5H4a1 1 0 0 0-1 1v9a1 1 0 0 0 1 1h3.96l4.38 4.02A1 1 0 0 0 14 20.77z"/>
      <path d="M17.5 8.5a1 1 0 0 0-1.41 1.42 2.95 2.95 0 0 1 0 4.16 1 1 0 0 0 1.42 1.41 4.95 4.95 0 0 0-.01-6.99z"/>
      <path d="M19.62 6.38a1 1 0 0 0-1.41 1.41 5.96 5.96 0 0 1 0 8.42 1 1 0 0 0 1.41 1.41 7.96 7.96 0 0 0 0-11.24z"/>
    </svg>
    <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="h-5 w-5 fill-current">
      <path d="M14 3.23a1 1 0 0 0-1.66-.75L7.96 6.5H4a1 1 0 0 0-1 1v9a1 1 0 0 0 1 1h3.96l4.38 4.02A1 1 0 0 0 14 20.77z"/>
      <path d="M20.71 5.29a1 1 0 0 0-1.42 0L3.29 21.29a1 1 0 1 0 1.42 1.42l16-16a1 1 0 0 0 0-1.42z"/>
    </svg>
  </div>
  <p
      v-if="errorMessage"
      class="absolute bottom-18 left-2 w-86 rounded-xl bg-black/45 px-3 py-2 text-xs text-red-300 backdrop-blur-sm"
  >
    {{ errorMessage }}
  </p>
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
