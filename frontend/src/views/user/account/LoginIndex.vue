<script setup>
import { ref } from "vue";
import { useUserStore } from "@/stores/user.js";
// 引入路由，用来做登录成功后的页面跳转
import { useRouter } from "vue-router";
import api from "@/js/http/api.js";

const username = ref('')
const password = ref('')
const errorMessage = ref('')
const user = useUserStore()
const router = useRouter()

/**
 * 处理登录按钮点击事件
 */
async function handleLogin() {

  // 每次点击登录前，先清空错误提示
  errorMessage.value = ''

  // 前端校验：用户名不能为空
  if (!username.value.trim()) {
    errorMessage.value = '用户名不能为空'

  // 前端校验：密码不能为空
  } else if (!password.value.trim()) {
    errorMessage.value = '密码不能为空'

  // 校验通过，开始向后端发登录请求
  } else {
    try {
      // 调用登录接口，把用户名和密码发给服务器
      const res = await api.post('api/user/account/login/', {
        username: username.value,
        password: password.value
      })

      // 后端返回的数据
      const data = res.data

      // 如果后端返回登录成功
      if (data.result === 'success') {
        // 存储access和信息
        user.setAccessToken(data.access)
        user.setUserInfo(data)

        // 登录成功后，跳转到首页
        await router.push({
          name: 'homepage-index',
        })

      // 登录失败（如用户名或密码错误）
      } else {
        errorMessage.value = data.result
      }

    } catch (err) {
      // 网络错误 / 服务器异常 / 接口报错
      errorMessage.value = '登录失败，请稍后再试'
      console.error(err)
    }
  }
}
</script>

<template>
<div class="flex justify-center mt-30">
  <form @submit.prevent="handleLogin" class="fieldset bg-base-200 border-base-300 rounded-box w-xs border p-4">

    <label class="label">用户名</label>
    <input v-model="username" type="text" class="input" placeholder="用户名" />

    <label class="label">密码</label>
    <input v-model="password" type="password" class="input" placeholder="密码" />

    <p v-if="errorMessage" class="text-sm text-red-500 mt-1">{{ errorMessage }}</p>

    <button class="btn btn-neutral mt-4">登录</button>
    <div class="flex justify-end" >
      <router-link :to="{name:'user-account-register-index'}" class="btn btn-sm btn-ghost text-gray-500">
        注册
      </router-link>
    </div>
  </form>
</div>
</template>

<style scoped>

</style>