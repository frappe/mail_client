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

let router = createRouter({
	history: createWebHistory('/mail'),
	routes,
})

router.beforeEach(async (to, from, next) => {
	const { userResource } = userStore()
	const { isLoggedIn } = sessionStore()

	isLoggedIn && (await userResource.promise)

	if (!isLoggedIn) {
		window.location.href = '/login'
	} else {
		next()
	}
})
export default router
