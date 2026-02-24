<script setup>
import { useRoute } from 'vue-router'
import UserInfoField from "@/views/user/space/components/UserInfoField.vue"
import { nextTick, onBeforeUnmount, onMounted, ref, useTemplateRef } from "vue"
import api from "@/js/http/api.js"

const userProfile = ref(null)        // 用户信息
const characters = ref([])           // 对应创建的角色
const isLoading = ref(false)         // 是否正在加载中
const hasCharacters = ref(true)      // 是否还有角色，初始为 true
const sentinelRef = useTemplateRef('sentinel-ref') // 监听哨兵元素
const route = useRoute()             // 获取当前路由对象（可以操作当前路由的参数，比如下面的 user_id）

// 判断哨兵元素是否在可视区域
function checkSentinelVisible() {
  if (!sentinelRef.value) return false

  const rect = sentinelRef.value.getBoundingClientRect()
  return rect.top < window.innerHeight && rect.bottom > 0
}

async function loadMore() {
  // 如果正在加载或者没有角色了就返回
  if (isLoading.value || !hasCharacters.value) return

  isLoading.value = true
  let newCharacters = []

  try {
    const res = await api.get('api/create/character/get_list/', {
      params: {
        items_count: characters.value.length,
        user_id: route.params.user_id,
      }
    })

    const data = res.data
    if (data.result === 'success') {
      // 请求成功，更新用户信息和角色列表
      userProfile.value = data.user_profile
      newCharacters = data.characters
    }
  } catch (err) {
    console.log(err)
  } finally {
    isLoading.value = false

    if (newCharacters.length === 0) {
      hasCharacters.value = false
    } else {
      characters.value.push(...newCharacters)

      await nextTick()

      // 如果哨兵仍然可见，继续加载（解决屏幕过高时数据不够撑满的问题）
      if (checkSentinelVisible()) {
        await loadMore()
      }
    }
  }
}

let observer = null

onMounted(async () => {
  await loadMore()

  // 创建一个 IntersectionObserver 实例
  // 用来监听“哨兵元素”（sentinelRef）是否进入可视区域
  observer = new IntersectionObserver(
    // 当被监听元素的可见性发生变化时会执行回调函数
    entries => {
      entries.forEach(entry => {
        // 如果哨兵进入视口（可见）
        if (entry.isIntersecting) {
          // 说明滚动到底部了，触发加载更多
          loadMore()
        }
      })
    },
    {
      root: null,        // 以浏览器视口作为参考区域
      rootMargin: '2px', // 提前 2px 触发（稍微提前加载）
      threshold: 0       // 只要有一点进入视口就触发
    }
  )

  // 开始监听哨兵元素
  if (sentinelRef.value) {
    observer.observe(sentinelRef.value)
  }
})

onBeforeUnmount(() => {
  // 组件销毁时断开监听，防止内存泄漏
  observer?.disconnect()
})
</script>

<template>
  <div class="flex flex-col items-center">
    <UserInfoField :userProfile="userProfile" />

    <!--
      可以根据屏幕宽度自动决定每行的元素数量，
      并将元素均匀排列在屏幕上；
      当最后一行元素不足时会左对齐。
    -->
    <div class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-9 mt-12 justify-items-center w-full px-9">
      <!-- 角色卡片渲染区域 -->
    </div>

    <!-- 哨兵元素 -->
    <div ref="sentinel-ref" class="h-2 mt-8 w-100 bg-red-600"></div>

    <div v-if="isLoading" class="text-gray-500 mt-4">
      加载中...
    </div>

    <div v-else-if="!hasCharacters" class="text-gray-500 mt-4">
      没有更多角色了
    </div>
  </div>
</template>

<style scoped>
</style>