<script setup>
  import { useRoute } from 'vue-router';
  import UserInfoField from "@/views/user/space/components/UserInfoField.vue";
  import {nextTick, onBeforeUnmount, onMounted, ref, useTemplateRef} from "vue";
  import api from "@/js/http/api.js";

  const userProfile = ref(null) //鐢ㄦ埛淇℃伅
  const characters = ref([])  //瀵瑰簲鐨勫垱寤虹殑瑙掕壊
  const isLoading = ref(false) //鏄惁鍦ㄥ姞杞戒腑
  const hasCharacters = ref(true) //鏄惁杩樻湁瑙掕壊,鍒濆涓簍rue
  const sentinelRef = useTemplateRef('sentinel-ref')// 鐩戝惉鍝ㄥ叺
  const route = useRoute(); // 鑾峰彇褰撳墠璺敱瀵硅薄(鍙互鎿嶄綔褰撳墠璺敱鐨勫弬鏁帮紝姣斿涓嬮潰鐨勫彇鍑簎ser_id)

  function checkSentinelVisible() {  // 鍒ゆ柇鍝ㄥ叺鏄惁鑳借鐪嬪埌
    if (!sentinelRef.value) return false

    const rect = sentinelRef.value.getBoundingClientRect()
    return rect.top < window.innerHeight && rect.bottom > 0
  }

  async function loadMore() {
    if(isLoading.value || !hasCharacters.value) return//濡傛灉姝ｅ湪鍔犺浇鎴栬€呮病鏈夎鑹蹭簡灏辫繑鍥?
    isLoading.value = true

    let newCharacters = []
    try {
      const res = await api.get('api/create/character/get_list/',{
        params:{
          items_count: characters.value.length,
          user_id:route.params.user_id,
        }
      })
      const data = res.data
      if(data.result === 'success') {//杩斿洖鎴愬姛灏辫幏鍙栦竴涓嬩俊鎭?
        userProfile.value = data.user_profile
        newCharacters = data.characters
      }
    } catch (err) {
      console.log(err)
    }finally {
      isLoading.value = false
      if(newCharacters.length === 0) {
        hasCharacters.value = false
      } else {
        characters.value.push(...newCharacters)

        await nextTick()

        if(checkSentinelVisible()) { //濡傛灉鐪嬪埌鍝ㄥ叺灏辩户缁姞杞?
          await loadMore()
        }
      }
    }
  }

let observer = null

onMounted(async () => {
  await loadMore()
  // 鍒涘缓涓€涓?IntersectionObserver 瀹炰緥
  // 鐢ㄦ潵鐩戝惉鈥滃摠鍏靛厓绱犫€濓紙sentinelRef锛夋槸鍚﹁繘鍏ヨ鍙?
  observer = new IntersectionObserver( //娴忚鍣ㄥ師鐢?API:鐩戝惉涓€涓厓绱犳槸鍚﹁繘鍏ュ彲瑙嗗尯鍩?
    // 褰撹鐩戝惉鐨勫厓绱犲彂鐢熷彲瑙佹€у彉鍖栨椂锛屼細鎵ц杩欎釜鍥炶皟鍑芥暟
    entries => {
      entries.forEach(entry => {
        // 濡傛灉鍝ㄥ叺杩涘叆瑙嗗彛锛堝彲瑙侊級
        if (entry.isIntersecting) {
          // 璇存槑婊氬姩鍒板簳閮ㄤ簡锛岃Е鍙戝姞杞芥洿澶?
          loadMore()
        }
      })
    },
    // 瑙傚療鍣ㄩ厤缃?
    {
      root: null,          // 浠ユ祻瑙堝櫒瑙嗗彛浣滀负鍙傜収鐗?
      rootMargin: '2px',   // 鎻愬墠2px瑙﹀彂锛堢◢寰彁鍓嶅姞杞斤級
      threshold: 0         // 鍙鏈変竴鐐硅繘鍏ヨ鍙ｅ氨瑙﹀彂
    }
  )
  // 鐩戝惉鍝ㄥ叺鍏冪礌
  observer.observe(sentinelRef.value)
})

onBeforeUnmount(() => {
  // 缁勪欢閿€姣佹椂鏂紑鐩戝惉锛岄槻姝㈠唴瀛樻硠婕?
  observer?.disconnect()
})

</script>

<template>
  <div class="flex flex-col items-center">
    <UserInfoField :userProfile="userProfile"/>

<!--    鍙互鏍规嵁灞忓箷瀹藉害鑷姩鍐冲畾姣忚鐨勫厓绱犳暟閲忥紝骞跺皢鍏冪礌鍧囧寑鎺掑垪鍦ㄥ睆骞曚笂锛涘綋鏈€鍚庝竴琛屽厓绱犱笉瓒虫椂浼氬乏瀵归綈銆?->
    <div class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-9 mt-12 justify-items-center w-full px-9">
    </div>

<!--    鍝ㄥ叺-->
    <div ref="sentinel-ref" class="h-2 mt-8 w-100 bg-red-600"></div>

    <div v-if="isLoading" class="text-gray-500 mt-4">鍔犺浇涓?..</div>
    <div v-else-if="!hasCharacters" class="text-gray-500 mt-4">没有更多角色了</div>
  </div>
</template>

<style scoped>

</style>
