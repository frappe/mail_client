export {}

declare module 'vue' {
	interface ComponentCustomProperties {
		__: (message: string, variables?: string[]) => string
	}
}
