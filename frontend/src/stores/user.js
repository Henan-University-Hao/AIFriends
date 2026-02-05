import {defineStore} from "pinia";
import {ref} from "vue";

export const useUserStore = defineStore('user', () => {
    const id = ref(1)
    const username = ref('LH')
    const photo = ref('http://127.0.0.1:8000/media/user/photos/default.png')
    const profile = ref('111')
    const accessToken = ref('11')
    function isLogin() {
            // 如果 accessToken 有值，说明已登录
            if (accessToken.value) {
                return true
            }
            // 如果 accessToken 没有值，说明未登录
            return false
    }
    function setAccessToken(token) {
        accessToken.value = token
    }

    function setUserInfo(data) {
        id.value = data.user_id
        username.value = data.username
        photo.value = data.photo
        profile.value = data.profile
    }

    function logout() {
        id.value = 0
        username.value = ''
        photo.value = ''
        profile.value = ''
    }

    return {
        id,
        username,
        photo,
        profile,
        accessToken, //不能忘记！！！！
        isLogin,
        setAccessToken,
        setUserInfo,
        logout
    }
})
