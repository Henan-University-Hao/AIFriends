<template>
  <div class="not-found">
    <div class="content">
      <div class="code">404</div>
      <h1 class="title">页面走丢了</h1>
      <p class="desc">你访问的页面不存在，或者已经被悄悄移走了。</p>

      <div class="actions">
        <button class="btn primary" @click="goHome">返回首页</button>
        <button class="btn" @click="goBack">返回上页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}

function goBack() {
  router.back()
}
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  background: #ffffff;
  color: #111111;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.content {
  text-align: center;
  max-width: 520px;
  width: 100%;
}

.code {
  font-size: 96px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 6px;
  color: #000000;
  margin-bottom: 20px;
}

.title {
  font-size: 30px;
  font-weight: 600;
  margin: 0 0 14px;
  color: #111111;
}

.desc {
  font-size: 15px;
  line-height: 1.8;
  color: #666666;
  margin: 0 0 32px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
}

.btn {
  min-width: 120px;
  padding: 12px 22px;
  border: 1px solid #111111;
  background: #ffffff;
  color: #111111;
  font-size: 14px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.btn:hover {
  background: #111111;
  color: #ffffff;
}

.btn.primary {
  background: #111111;
  color: #ffffff;
}

.btn.primary:hover {
  background: #333333;
  border-color: #333333;
}

@media (max-width: 480px) {
  .code {
    font-size: 72px;
  }

  .title {
    font-size: 24px;
  }

  .desc {
    font-size: 14px;
  }

  .actions {
    flex-direction: column;
    align-items: center;
  }

  .btn {
    width: 100%;
    max-width: 220px;
  }
}
</style>