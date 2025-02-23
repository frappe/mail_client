import { createRouter, createWebHistory } from 'vue-router'

import { sessionStore } from '@/stores/session'
import { userStore } from '@/stores/user'

const routes = [
	{
		path: '/',
		redirect: { name: 'Inbox' },
	},
	{
		path: '/signup',
		name: 'SignUp',
		component: () => import('@/pages/SignupView.vue'),
		meta: { isLogin: true },
	},
	{
		path: '/signup/:requestKey',
		name: 'AccountSetup',
		component: () => import('@/pages/SignupView.vue'),
		props: true,
		meta: { isLogin: true },
	},
	{
		path: '/login',
		name: 'Login',
		component: () => import('@/pages/LoginView.vue'),
		meta: { isLogin: true },
	},
	{
		path: '/setup',
		name: 'Setup',
		component: () => import('@/pages/SetupView.vue'),
		meta: { isSetup: true },
	},
	{
		path: '/inbox',
		name: 'Inbox',
		component: () => import('@/pages/InboxView.vue'),
	},
	{
		path: '/sent',
		name: 'Sent',
		component: () => import('@/pages/SentView.vue'),
	},
	{
		path: '/drafts',
		name: 'Drafts',
		component: () => import('@/pages/DraftsView.vue'),
	},
	{
		path: '/dashboard',
		redirect: { name: 'Domains' },
		meta: { isDashboard: true },
	},
	{
		path: '/dashboard/domains',
		name: 'Domains',
		component: () => import('@/pages/dashboard/DomainsView.vue'),
		meta: { isDashboard: true },
	},
	{
		path: '/dashboard/domains/:domainName',
		name: 'Domain',
		component: () => import('@/pages/dashboard/DomainView.vue'),
		props: true,
		meta: { isDashboard: true },
	},
	{
		path: '/dashboard/members',
		name: 'Members',
		component: () => import('@/pages/dashboard/MembersView.vue'),
		meta: { isDashboard: true },
	},
]

const router = createRouter({
	history: createWebHistory('/mail'),
	routes,
})

router.beforeEach(async (to, from, next) => {
	if (document.referrer.includes('/app/setup-wizard')) window.location.replace('/app')

	const { isLoggedIn } = sessionStore()
	if (!isLoggedIn) return next(to.meta.isLogin ? undefined : { name: 'Login' })

	const { userResource } = userStore()
	await userResource.promise

	if (userResource.data.is_mail_admin) {
		if (!userResource.data.tenant) return next(to.meta.isSetup ? undefined : { name: 'Setup' })
		if (!userResource.data.default_outgoing && !to.meta.isDashboard)
			return next({ name: 'Domains' })
	} else if (to.meta.isDashboard) return next({ name: 'Inbox' })

	next(to.meta.isLogin || to.meta.isSetup ? { name: 'Inbox' } : undefined)
})

export default router
