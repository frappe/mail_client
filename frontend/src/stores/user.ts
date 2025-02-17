import { reactive } from 'vue'
import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'

import router from '@/router'

import type { Folder, UserResource } from '@/types'

export const userStore = defineStore('mail-users', () => {
	const userResource: UserResource = createResource({
		url: 'mail.api.mail.get_user_info',
		onError: (error) => {
			if (error && error.exc_type === 'AuthenticationError') {
				router.push('/login')
			}
		},
		auto: true,
	})

	const getParsedItem = (key: string): string | null => {
		const item = sessionStorage.getItem(key)
		return item ? JSON.parse(item) : null
	}

	const currentMail: Record<Folder, string | null> = reactive({
		Inbox: getParsedItem('currentInboxMail'),
		Sent: getParsedItem('currentSentMail'),
		Outbox: getParsedItem('currentOutboxMail'),
		Drafts: getParsedItem('currentDraftsMail'),
	})

	const setCurrentMail = (folder: Folder, mail: string | null) => {
		const itemName = `current${folder}Mail`
		if (mail) {
			currentMail[folder] = mail
			sessionStorage.setItem(itemName, JSON.stringify(mail))
		} else {
			currentMail[folder] = null
			sessionStorage.removeItem(itemName)
		}
	}

	return { userResource, currentMail, setCurrentMail }
})
