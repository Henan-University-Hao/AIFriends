<script setup>
  import { useRoute } from 'vue-router';

  const route = useRoute(); // 获取当前路由对象(可以操作当前路由的参数，比如下面的取出user_id)
</script>

<template>
个人空间:{{ route.params.user_id }}
</template>

<style scoped>

</style>