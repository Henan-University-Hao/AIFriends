<script setup>

import Navbar from "@/components/navbar/Navbar.vue";
import api from "@/js/http/api.js";
import {onMounted} from "vue";
import {useUserStore} from "@/stores/user.js";
import {useRoute, useRouter} from "vue-router";

const user = useUserStore()
const route = useRoute()
const router = useRouter()
// onMounted：组件“挂载完成后”自动执行的回调函数
onMounted(async () => {
  try {
    const res = await api.get('api/user/account/get_user_info/')
    const data = res.data
    if(data.result === 'success') {
      user.setUserInfo(data)
    }
  } catch (err) {
  } finally {
    user.setHasPulledUserInfo(true)

    if(route.meta.needLogin && !user.isLogin()) { //从云端加载完之后，如果需要登录且未登录就跳转到登录页面
      await router.replace({
        name: 'user-account-login-index'
      })
    }
  }
})
</script>

<template>
  <Navbar >
    <router-view></router-view>
  </Navbar>
</template>

<style scoped>

</style>
