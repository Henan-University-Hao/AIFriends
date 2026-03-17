/*
 * 目标：
 * 1) 每次请求都自动带上 accessToken（放到 Authorization 头里）
 * 2) 如果响应返回 401（accessToken 过期/无效），自动用 refresh_token 去刷新 accessToken
 * 3) 刷新成功：把新的 accessToken 保存起来，并“重放”刚才失败的请求
 * 4) 刷新失败：说明 refresh_token 也失效了，直接登出
 */

import axios from "axios"
import { useUserStore } from "@/stores/user.js"
import CONFIG_API from "@/js/config/config.js";

export function getErrorMessage(error, fallback = '系统异常，请稍后重试') {
  return error?.response?.data?.detail
    || error?.response?.data?.result
    || error?.userMessage
    || error?.message
    || fallback
}

const BASE_URL = CONFIG_API.HTTP_URL

// 创建一个 axios 实例：后续都用这个 api 去发请求
const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // 允许携带 cookie（关键：refresh_token 通常在 httpOnly cookie 里）
})

/**
 * 请求拦截器：在每次请求发出前执行
 * 如果 Pinia 里有 accessToken，就自动加到请求头
 */
api.interceptors.request.use(config => {
  const user = useUserStore()
  if (user.accessToken) {
    // Authorization: Bearer xxxxx
    config.headers.Authorization = `Bearer ${user.accessToken}`
  }
  return config
})

/**
 * 下面这套变量 + 函数，是为了“只刷新一次 token”，其他 401 请求排队等结果
 * - isRefreshing：标记是否正在刷新 token
 * - refreshSubscribers：存放“等待刷新结果”的回调队列
 */
let isRefreshing = false
let refreshSubscribers = []

// 把某个请求的“续命回调”加入队列：等刷新完成后再统一处理
function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

// 刷新成功：把新 token 发给所有等待的请求，让它们重试
function onRefreshed(token) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

// 刷新失败：通知所有等待的请求失败（通常会触发登出/跳转登录）
function onRefreshFailed(err) {
  refreshSubscribers.forEach(cb => cb(null, err))
  refreshSubscribers = []
}

/**
 * 响应拦截器：
 * - 正常响应：直接返回
 * - 出错响应：重点处理 401（token 过期）
 */
api.interceptors.response.use(
  response => response,
  async error => {
    const user = useUserStore()

    // 原始请求配置（用来重放请求）
    const originalRequest = error?.config
    if (error?.response?.status === 429) {
      error.userMessage = getErrorMessage(error, '操作过快了，请稍后再试')
      return Promise.reject(error)
    }
    if (!originalRequest) {
      return Promise.reject(error)
    }

    /**
     * 如果：
     * 1) 返回码是 401
     * 2) originalRequest._retry 还没被标记（避免无限循环）
     * 就启动“刷新 + 重试”流程
     */
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true // 防止同一个请求反复触发刷新

      // 返回一个 Promise：让这次请求“先挂起”，等刷新完再决定 resolve/reject
      return new Promise((resolve, reject) => {

        // 这个回调会在刷新完成后被调用
        subscribeTokenRefresh((token, error) => {
          if (error) {
            // 刷新失败：这次请求也失败
            reject(error)
          } else {
            // 刷新成功：给原请求换上新 token，然后重发请求
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(api(originalRequest))
          }
        })

        /**
         * 重点：
         * 如果当前没有在刷新，就由“第一个撞到 401 的请求”负责去刷新 token
         * 其他撞到 401 的请求只需要排队等结果（subscribeTokenRefresh）
         */
        if (!isRefreshing) {
          isRefreshing = true

          /**
           * 注意：这里用的是 axios（全局 axios），不是 api
           * 原因：避免 refresh 请求自己又触发响应拦截器、产生递归
           *
           * refresh_token 通常在 cookie 里，所以 withCredentials 必须为 true
           */
          axios.post(
            `${BASE_URL}/api/user/account/refresh_token/`,
            {},
            { withCredentials: true, timeout: 5000 }
          )
          .then(res => {
            // 后端返回新的 access token（假设字段叫 access）
            user.setAccessToken(res.data.access)

            // 通知所有排队请求：刷新成功了，给你新 token
            onRefreshed(res.data.access)
          })
          .catch(error => {
            // 刷新失败：说明 refresh_token 也过期/无效
            user.logout() // 清理前端登录状态（比如 pinia、localStorage 等）

            // 通知所有排队请求：刷新失败了
            onRefreshFailed(error)

            // 让当前这次 Promise 也失败
            reject(error)
          })
          .finally(() => {
            isRefreshing = false
          })
        }
      })
    }

    // 不是 401 或者已经 retry 过了：直接把错误抛出去
    return Promise.reject(error)
  }
)

export default api
