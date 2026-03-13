<script setup>
import { ref } from "vue";
import { useUserStore } from "@/stores/user.js";
import { useRouter } from "vue-router";
import api, { getErrorMessage } from "@/js/http/api.js";

const username = ref('')
const password = ref('')
const password_confirm = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const user = useUserStore()
const router = useRouter()

async function handleRegister() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!username.value.trim() || !password.value.trim()) {
    errorMessage.value = '用户名和密码不能为空'
  } else if (password.value.trim() !== password_confirm.value.trim()) {
    errorMessage.value = '两次密码输入不一致'
  } else {
    try {
      const res = await api.post('api/user/account/register/', {
        username: username.value,
        password: password.value
      })
      const data = res.data
      if (data.result === 'success') {
        successMessage.value = '注册成功，正在登录中...'
        setTimeout(() => {
          user.setAccessToken(data.access)
          user.setUserInfo(data)
          router.push({
            name:'homepage-index',
          })
        }, 1000)
      } else {
        errorMessage.value = data.result
      }
    } catch (err) {
      errorMessage.value = getErrorMessage(err, '注册失败，请稍后再试')
    }
  }
}
</script>

<template>
<div class="flex justify-center mt-30">
  <form @submit.prevent="handleRegister" class="fieldset bg-base-200 border-base-300 rounded-box w-xs border p-4">

    <label class="label">用户名</label>
    <input v-model="username" type="text" class="input" placeholder="用户名" />

    <label class="label">密码</label>
    <input v-model="password" type="password" class="input" placeholder="密码" />
    <label class="label">确认密码</label>
    <input v-model="password_confirm" type="password" class="input" placeholder="确认密码" />

    <p v-if="errorMessage" class="text-sm text-red-500 mt-1">{{ errorMessage }}</p>
    <p v-else-if="successMessage" class="text-sm text-green-500 mt-1">{{ successMessage }}</p>
    <button class="btn btn-neutral mt-4">注册</button>
    <div class="flex justify-end" >
      <router-link :to="{name:'user-account-login-index'}" class="btn btn-sm btn-ghost text-gray-500">
        登录
      </router-link>
    </div>
  </form>
</div>
</template>

<style scoped>

</style>
