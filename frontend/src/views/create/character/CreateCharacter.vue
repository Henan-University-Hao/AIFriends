<script setup>

import Photo from "@/views/create/character/components/Photo.vue";
import Name from "@/views/create/character/components/Name.vue";
import Profile from "@/views/create/character/components/Profile.vue";
import BackgroundImage from "@/views/create/character/components/BackgroundImage.vue";
import {ref, useTemplateRef, onMounted} from "vue";
import {base64ToFile} from "@/js/utils/base64_to_file.js";
import api from "@/js/http/api.js";
import {useRouter} from "vue-router";
import {useUserStore} from "@/stores/user.js";
import Voice from "@/views/create/character/components/Voice.vue";

const user = useUserStore()
const router = useRouter()
const photoRef = useTemplateRef('photo-ref');
const nameRef = useTemplateRef('name-ref');
const voiceRef = useTemplateRef('voice-ref')
const profileRef = useTemplateRef('profile-ref');
const backgroundImageRef = useTemplateRef('backgroundImage-ref');
const errorMessage = ref('');
const voices = ref([])
const curVoiceId = ref(null)

onMounted( async () => {
  try {
    const res = await api.get('api/create/character/voice/get_list/',{})
    const data = res.data
    if (data.result === 'success') {
      voices.value = data.voices
      curVoiceId.value = data.voices[0].id
    }
  } catch(err) {
    console.log(err);
  }
})

async function handleCreate() {
  const photo = photoRef.value.myPhoto;
  const name = nameRef.value.myName?.trim();
  const voice = voiceRef.value.myVoice;
  const profile = profileRef.value.myProfile?.trim();
  const backgroundImage = backgroundImageRef.value.myBackgroundImage;

  errorMessage.value = '';
  if(!photo) {
    errorMessage.value = '头像不能为空'
  } else if(!name) {
    errorMessage.value = '名字不能为空'
  } else if(!voices) {
    errorMessage.value = '音色不能为空';
  } else if(!profile) {
    errorMessage.value = '角色介绍不能为空'
  } else if(!backgroundImage){
    errorMessage.value = '聊天背景不能为空'
  } else {
    const formData = new FormData()
    formData.append('name', name)
    formData.append('voice_id', voice)
    formData.append('profile', profile)
    formData.append('photo', base64ToFile(photo, 'photo.png'))
    formData.append('background_image', base64ToFile(backgroundImage, 'background_image.png'))
    try{
      const res = await api.post('api/create/character/create/', formData);
      const data = res.data;
      if(data.result === 'success'){
        await router.push({
          name:'user-space-index',
          params:{
            user_id:user.id
          }
        })
      } else {
        errorMessage.value = data.result
      }
    } catch (err) {
      errorMessage.value = '系统异常，请稍后重试';
    }
  }
}
</script>

<template>
  <div class="flex justify-center">
    <div class="card w-120 bg-base-200 shadow-sm mt-12">
      <div class="card-body">
        <h3 class="text-lg font-bold my-3">创建角色</h3>
        <Photo ref="photo-ref"/>
        <Name ref="name-ref"/>
        <Voice ref="voice-ref" :voices="voices" :curVoiceId="curVoiceId"/>
        <Profile ref="profile-ref"/>
        <BackgroundImage ref="backgroundImage-ref"/>

        <p v-if="errorMessage" class="text-sm text-red-500">{{errorMessage}}</p>

        <div class="flex justify-center">
          <button @click="handleCreate" class="btn btn-neutral w-60 mt-2">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>