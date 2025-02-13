export interface ReplyDetails {
	to: string
	cc: string
	bcc: string
	subject?: string
	in_reply_to_mail_type: 'Outgoing Mail' | 'Incoming Mail'
	in_reply_to_mail_name?: string
}
