import router from '@/router'
import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive } from 'vue'

export const userStore = defineStore('mail-users', () => {
	const userResource = createResource({
		url: 'mail_client.api.mail.get_user_info',
		onError(error) {
			if (error && error.exc_type === 'AuthenticationError') {
				router.push('/login')
			}
		},
		auto: true,
	})

	const defaultOutgoing = createResource({
		url: 'mail_client.api.mail.get_default_outgoing',
		auto: true,
	})

	const currentMail = reactive({
		incoming: JSON.parse(sessionStorage.getItem('currentIncomingMail')) || null,
		sent: JSON.parse(sessionStorage.getItem('currentSentMail')) || null,
		draft: JSON.parse(sessionStorage.getItem('currentDraftMail')) || null,
	})

	const setCurrentMail = (folder, mail) => {
		const itemName = `current${folder.charAt(0).toUpperCase() + folder.slice(1)}Mail`
		if (!mail) {
			currentMail[folder] = null
			sessionStorage.removeItem(itemName)
			return
		}
		currentMail[folder] = mail
		sessionStorage.setItem(itemName, JSON.stringify(mail))
	}

	return { userResource, defaultOutgoing, currentMail, setCurrentMail }
})
