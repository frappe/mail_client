import { useTimeAgo } from '@vueuse/core'
import { toast } from 'frappe-ui'

export function convertToTitleCase(str: string) {
	if (!str) return ''

	return str
		.toLowerCase()
		.split(' ')
		.map(function (word: string) {
			return word.charAt(0).toUpperCase().concat(word.substr(1))
		})
		.join(' ')
}

export function getSidebarLinks() {
	return [
		{
			label: 'Inbox',
			icon: 'Inbox',
			to: 'Inbox',
			activeFor: ['Inbox'],
		},
		{
			label: 'Sent',
			icon: 'Send',
			to: 'Sent',
			activeFor: ['Sent'],
		},
		{
			label: 'Outbox',
			icon: 'Send',
			to: 'Outbox',
			activeFor: ['Outbox'],
		},
		{
			label: 'Drafts',
			icon: 'Edit3',
			to: 'Drafts',
			activeFor: ['Drafts'],
		},
		{
			label: 'Domains',
			icon: 'Globe',
			to: 'Domains',
			activeFor: ['Domains', 'Domain'],
			forDashboard: true,
		},
		{
			label: 'Members',
			icon: 'Users',
			to: 'Members',
			activeFor: ['Members'],
			forDashboard: true,
		},
	]
}

export function formatNumber(number: number) {
	return number.toLocaleString('en-IN', {
		maximumFractionDigits: 0,
	})
}

export function startResizing(event) {
	const startX = event.clientX
	const sidebar = document.getElementsByClassName('mailSidebar')[0]
	const startWidth = sidebar.offsetWidth

	const onMouseMove = (event) => {
		const diff = event.clientX - startX
		let newWidth = startWidth + diff
		if (newWidth < 200) {
			newWidth = 200
		}
		sidebar.style.width = newWidth + 'px'
	}

	const onMouseUp = () => {
		document.removeEventListener('mousemove', onMouseMove)
		document.removeEventListener('mouseup', onMouseUp)
	}

	document.addEventListener('mousemove', onMouseMove)
	document.addEventListener('mouseup', onMouseUp)
}

export function singularize(word: string) {
	const endings = {
		ves: 'fe',
		ies: 'y',
		i: 'us',
		zes: 'ze',
		ses: 's',
		es: 'e',
		s: '',
	}
	return word.replace(new RegExp(`(${Object.keys(endings).join('|')})$`), (r) => endings[r])
}

export function timeAgo(date) {
	return useTimeAgo(date).value
}

export function validateEmail(email: string) {
	const regExp =
		/^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
	return regExp.test(email)
}

export function formatBytes(bytes: number) {
	if (!+bytes) return '0 Bytes'

	const k = 1024
	const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

	const i = Math.floor(Math.log(bytes) / Math.log(k))

	return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))}${sizes[i]}`
}

export const raiseToast = (message: string, type = 'success') => {
	if (type === 'success')
		return toast({
			title: 'Success',
			text: __(message),
			icon: 'check-circle',
			position: 'bottom-right',
			iconClasses: 'text-green-500',
		})

	const div = document.createElement('div')
	div.innerHTML = message
	// strip html tags
	const text =
		div.textContent || div.innerText || 'Failed to perform action. Please try again later.'
	toast({
		title: 'Error',
		text: __(text),
		icon: 'alert-circle',
		position: 'bottom-right',
		iconClasses: 'text-red-500',
		timeout: 7,
	})
}
