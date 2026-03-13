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

async function handleSend(event, audioMessage) {
  errorMessage.value = ''

  const content = audioMessage ? audioMessage.trim() : message.value.trim()
  if (!content) {
    return
  }

  initAudioStream()

  const curId = ++processId
  message.value = ''

  emit('pushBackMessage', { role: 'user', content, id: crypto.randomUUID() })
  emit('pushBackMessage', { role: 'ai', content: '', id: crypto.randomUUID() })

  try {
    await streamApi('/api/friend/message/chat/', {
      body: {
        friend_id: props.friendId,
        message: content,
      },
      onmessage(data) {
        if (curId !== processId) {
          return
        }
        if (data.content) {
          emit('addToLastMessage', data.content)
        }
        if (data.audio) {
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
