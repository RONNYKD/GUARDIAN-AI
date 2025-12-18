import { LucideIcon } from 'lucide-react'
import clsx from 'clsx'

interface StatCardProps {
  title: string
  value: string
  icon: LucideIcon
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  color?: 'primary' | 'success' | 'danger' | 'warning'
  small?: boolean
}

export default function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  trendValue,
  color = 'primary',
  small = false,
}: StatCardProps) {
  const colorClasses = {
    primary: 'bg-primary-100 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400',
    success: 'bg-success-100 dark:bg-success-900/20 text-success-600 dark:text-success-400',
    danger: 'bg-danger-100 dark:bg-danger-900/20 text-danger-600 dark:text-danger-400',
    warning: 'bg-warning-100 dark:bg-warning-900/20 text-warning-600 dark:text-warning-400',
  }

  const trendClasses = {
    up: 'text-success-600 dark:text-success-400',
    down: 'text-danger-600 dark:text-danger-400',
    neutral: 'text-gray-600 dark:text-gray-400',
  }

  return (
    <div className="bg-white dark:bg-gray-800 overflow-hidden shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
      <div className={clsx('p-5', small && 'p-4')}>
        <div className="flex items-center">
          <div className={clsx('flex-shrink-0 rounded-md p-3', colorClasses[color])}>
            <Icon className={clsx('h-6 w-6', small && 'h-5 w-5')} />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className={clsx(
                'text-sm font-medium text-gray-600 dark:text-gray-400 truncate',
                small && 'text-xs'
              )}>
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className={clsx(
                  'text-2xl font-semibold text-gray-900 dark:text-white',
                  small && 'text-xl'
                )}>
                  {value}
                </div>
                {trend && trendValue && (
                  <div className={clsx(
                    'ml-2 flex items-baseline text-sm font-semibold',
                    trendClasses[trend]
                  )}>
                    {trendValue}
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}
