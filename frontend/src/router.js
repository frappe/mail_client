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
	},
	{
		path: '/signup/:requestKey',
		name: 'AccountSetup',
		component: () => import('@/pages/SignUp.vue'),
		props: true,
	},
	{
		path: '/login',
		name: 'Login',
		component: () => import('@/pages/Login.vue'),
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
	const toLogin = ['Login', 'SignUp', 'AccountSetup'].includes(to.name)

	if (!isLoggedIn) return next(toLogin ? undefined : { name: 'Login' })

	const { userResource } = userStore()
	await userResource.promise
	next(toLogin ? { name: 'Inbox' } : undefined)
})

export default router
