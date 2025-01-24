import { createRouter, createWebHistory } from 'vue-router'
import { userStore } from '@/stores/user'
import { sessionStore } from '@/stores/session'

const routes = [
	{
		path: '/',
		redirect: {
			name: 'Inbox',
		},
	},
	{
		path: '/signup',
		name: 'SignUp',
		component: () => import('@/pages/SignUp.vue'),
		meta: { isLogin: true },
	},
	{
		path: '/signup/:requestKey',
		name: 'AccountSetup',
		component: () => import('@/pages/SignUp.vue'),
		props: true,
		meta: { isLogin: true },
	},
	{
		path: '/login',
		name: 'Login',
		component: () => import('@/pages/Login.vue'),
		meta: { isLogin: true },
	},
	{
		path: '/setup',
		name: 'Setup',
		component: () => import('@/pages/Setup.vue'),
		meta: { isSetup: true },
	},
	{
		path: '/inbox',
		name: 'Inbox',
		component: () => import('@/pages/Inbox.vue'),
	},
	{
		path: '/sent',
		name: 'Sent',
		component: () => import('@/pages/Sent.vue'),
	},
	{
		path: '/drafts',
		name: 'Drafts',
		component: () => import('@/pages/Drafts.vue'),
	},
]

const router = createRouter({
	history: createWebHistory('/mail'),
	routes,
})

router.beforeEach(async (to, from, next) => {
	const { isLoggedIn } = sessionStore()
	if (!isLoggedIn) return next(to.meta.isLogin ? undefined : { name: 'Login' })

	const { userResource } = userStore()
	await userResource.promise
	if (!(userResource.data?.tenant && userResource.data?.tenant_domains.length))
		return next(to.meta.isSetup ? undefined : { name: 'Setup' })

	next(to.meta.isLogin || to.meta.isSetup ? { name: 'Inbox' } : undefined)
})

export default router
