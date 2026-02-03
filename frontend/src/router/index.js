import { createRouter, createWebHistory } from 'vue-router'
import HomepageIndex from "@/views/homepage/HomepageIndex.vue";
import FriendIndex from "@/views/friend/FriendIndex.vue";
import CreateIndex from "@/views/create/CreateIndex.vue";
import NotFoundIndex from "@/views/error/NotFoundIndex.vue";
import LoginIndex from "@/views/user/account/LoginIndex.vue";
import RegisterIndex from "@/views/user/account/RegisterIndex.vue";
import SpaceIndex from "@/views/user/space/SpaceIndex.vue";
import ProfileIndex from "@/views/user/profile/ProfileIndex.vue";
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path:'/',
      name:'homepage-index',
      component: HomepageIndex,
    },
    {
      path:'/friend/',
      name:'friend-index',
      component: FriendIndex,
    },
    {
      path:'/create/',
      name:'create-index',
      component: CreateIndex,
    },
    {
      path:'/404/',
      name:'404',
      component: NotFoundIndex,
    },
    {
      path:'/user/account/login/',
      name:'user-account-login-index',
      component: LoginIndex,
    },
    {
      path:'/user/account/register/',
      name:'user-account-register-index',
      component: RegisterIndex,
    },
    {
      path:'/user/space/:user_id/',//传递一个id参数
      name:'user-space-index',
      component: SpaceIndex,
    },
    {
      path:'/user/profile/',
      name:'user-profile-index',
      component: ProfileIndex,
    },
    {
      path:'/:pathMatch(.*)*', //匹配不存在的路径
      name:'not-found',
      component: NotFoundIndex,
    }
  ],
})

export default router
