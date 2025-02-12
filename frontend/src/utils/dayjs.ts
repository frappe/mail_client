import dayjs from 'dayjs/esm'
import isSameOrAfter from 'dayjs/esm/plugin/isSameOrAfter'
import isSameOrBefore from 'dayjs/esm/plugin/isSameOrBefore'
import isToday from 'dayjs/esm/plugin/isToday'
import isYesterday from 'dayjs/esm/plugin/isYesterday'
import localizedFormat from 'dayjs/esm/plugin/localizedFormat'
import relativeTime from 'dayjs/esm/plugin/relativeTime'
import updateLocale from 'dayjs/esm/plugin/updateLocale'

dayjs.extend(updateLocale)
dayjs.extend(relativeTime)
dayjs.extend(localizedFormat)
dayjs.extend(isToday)
dayjs.extend(isYesterday)
dayjs.extend(isSameOrBefore)
dayjs.extend(isSameOrAfter)

export default dayjs
